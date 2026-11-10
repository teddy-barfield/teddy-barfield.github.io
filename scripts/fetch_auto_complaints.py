#!/usr/bin/env python3
"""Fetch DFS auto insurer complaint rankings (data.ny.gov h2wd-9xfe) and write small processed files.

Usage: python3 scripts/fetch_auto_complaints.py
Writes to data/auto-complaints/: rankings_long.csv, ranking_over_time.csv,
ratio_distribution.csv, year_summary.csv, meta.json
"""
import csv, json, os, statistics, time, urllib.parse, urllib.request
from datetime import date

ID = "h2wd-9xfe"
BASE = f"https://data.ny.gov/resource/{ID}.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "auto-complaints")
SMALL_BOOK_M = 1.0  # $ millions of premium
NUM = ["ratio", "upheld_complaints", "question_of_fact_complaints", "not_upheld_complaints",
       "total_complaints", "premiums_written_in_millions", "rank", "filing_year"]


def get(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-data-script/1.0", "Accept": "application/json"})
    last = None
    for attempt in range(4):  # retry transient disconnects
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa
            last = e
            time.sleep(2 ** attempt)
    raise last


def fetch_all():
    rows, off = [], 0
    while True:  # server-side select + stable order, paged
        page = get({"$select": ",".join(["naic", "company_name"] + NUM),
                    "$order": "filing_year,rank,naic", "$limit": 1000, "$offset": off})
        rows += page
        if len(page) < 1000:
            return rows
        off += 1000


def clean(raw):
    out, dropped = [], {"missing_key": 0, "duplicate": 0}
    seen = set()
    for r in raw:
        if not r.get("naic") or not r.get("filing_year") or not r.get("ratio"):
            dropped["missing_key"] += 1
            continue
        key = (r["naic"], r["filing_year"])
        if key in seen:
            dropped["duplicate"] += 1
            continue
        seen.add(key)
        o = {"naic": r["naic"].strip(), "company_name": " ".join(r["company_name"].split())}
        for k in NUM:
            v = float(r[k])
            o[k] = int(v) if k != "ratio" and k != "premiums_written_in_millions" else v
        out.append(o)
    return out, dropped


def pct(sorted_vals, p):
    i = (len(sorted_vals) - 1) * p
    lo, hi = int(i), min(int(i) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    raw = fetch_all()
    rows, dropped = clean(raw)
    years = sorted({r["filing_year"] for r in rows})
    cols = ["naic", "company_name", "filing_year", "rank", "ratio", "upheld_complaints",
            "question_of_fact_complaints", "not_upheld_complaints", "total_complaints",
            "premiums_written_in_millions", "small_book"]
    for r in rows:  # ratios on < $1M of premium swing wildly on 1-2 complaints; flag, do not drop
        r["small_book"] = int(r["premiums_written_in_millions"] < SMALL_BOOK_M)
    write("rankings_long.csv", cols, [[r[c] for c in cols] for r in rows])
    same = []  # years whose full table is identical to the previous year (publisher repeat)
    for y in years[1:]:
        f = lambda yy: sorted((r["naic"], r["ratio"], r["upheld_complaints"], r["rank"]) for r in rows if r["filing_year"] == yy)
        if f(y) == f(y - 1):
            same.append(y)

    # ranking-over-time: one row per insurer (latest name), rank + ratio per year
    by = {}
    for r in rows:
        by.setdefault(r["naic"], {})[r["filing_year"]] = r
    names = {n: d[max(d)]["company_name"] for n, d in by.items()}
    hdr = ["naic", "company_name", "years_listed"] + [f"rank_{y}" for y in years] + [f"ratio_{y}" for y in years]
    table = []
    for n, d in sorted(by.items(), key=lambda kv: names[kv[0]]):
        table.append([n, names[n], len(d)] + [d[y]["rank"] if y in d else "" for y in years]
                     + [d[y]["ratio"] if y in d else "" for y in years])
    write("ranking_over_time.csv", hdr, table)

    # per-year distribution of complaint ratio
    dist, hist_rows = [], []
    tests = [lambda x: x == 0, lambda x: 0 < x < 0.1, lambda x: 0.1 <= x < 0.25, lambda x: 0.25 <= x < 0.5,
             lambda x: 0.5 <= x < 1, lambda x: 1 <= x < 2, lambda x: 2 <= x < 5, lambda x: x >= 5]
    labels = ["0 (none upheld)", ">0-0.1", "0.1-0.25", "0.25-0.5", "0.5-1", "1-2", "2-5", "5+"]
    for y in years:
        rs = [r for r in rows if r["filing_year"] == y]
        v = sorted(r["ratio"] for r in rs)
        prem = sum(r["premiums_written_in_millions"] for r in rs)
        up = sum(r["upheld_complaints"] for r in rs)
        dist.append([y, len(rs), round(prem, 1), up, sum(r["total_complaints"] for r in rs),
                     round(up / prem, 4) if prem else "", sum(1 for x in v if x == 0),
                     round(pct(v, .25), 4), round(statistics.median(v), 4), round(pct(v, .75), 4),
                     round(pct(v, .9), 4), v[-1]])
        for lab, test in zip(labels, tests):
            hist_rows.append([y, lab, sum(1 for x in v if test(x))])
    write("year_summary.csv", ["filing_year", "insurers", "premiums_millions", "upheld", "total_complaints",
          "pooled_ratio", "insurers_zero_upheld", "p25", "median", "p75", "p90", "max"], dist)
    write("ratio_distribution.csv", ["filing_year", "ratio_bucket", "insurers"], hist_rows)

    meta = {"dataset": "Automobile Insurance Company Complaint Rankings: Beginning 2009",
            "agency": "New York State Department of Financial Services (DFS)",
            "resource_id": ID, "url": f"https://data.ny.gov/d/{ID}",
            "api": BASE, "pulled": date.today().isoformat(),
            "rows_fetched": len(raw), "rows_kept": len(rows), "dropped": dropped,
            "years": [years[0], years[-1]], "years_identical_to_prior_year": same,
            "small_book_threshold_millions": SMALL_BOOK_M,
            "small_book_rows": sum(r["small_book"] for r in rows), "insurers": len(by)}
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
