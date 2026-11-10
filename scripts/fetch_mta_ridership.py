#!/usr/bin/env python3
"""Fetch MTA Daily Ridership and Traffic: Beginning 2020 (data.ny.gov sayj-mze2) and write small processed files.

Usage: python3 scripts/fetch_mta_ridership.py
Writes to data/mta-ridership/: baseline.csv, daily_share.csv, monthly_share.csv, top_days.csv, latest_summary.csv, meta.json

The published table is long format: one row per date and mode with a single `count`. It has NO pre-pandemic
comparison column, and it starts on 2020-03-01. So the "pre-pandemic level" here is my own baseline: the last
full week before the March 2020 collapse, Sun 2020-03-01 to Sat 2020-03-07. Baselines are kept by day type
(weekday = mean of Mon-Fri, Saturday, Sunday) because weekend ridership is far lower than weekday ridership.
Saturday and Sunday baselines are single days, so they are noisier than the weekday baseline.
"""
import csv, json, os, time, urllib.parse, urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone

ID = "sayj-mze2"
BASE = f"https://data.ny.gov/resource/{ID}.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "mta-ridership")
MODES = ["Subway", "Bus", "LIRR", "MNR", "SIR", "AAR", "BT"]  # have a March 2020 baseline
OTHER = ["CBD Entries", "CRZ Entries"]  # start January 2025, no baseline: kept as raw counts only
BASE_START, BASE_END = date(2020, 3, 1), date(2020, 3, 7)


def get(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-data-script/1.0", "Accept": "application/json"})
    last = None
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa
            last = e; time.sleep(2 ** a)
    raise last


def fetch_all():
    rows, off = [], 0
    while True:
        page = get({"$select": "date,mode,count", "$order": "mode,date", "$limit": 5000, "$offset": off})
        rows += page
        if len(page) < 5000:
            return rows
        off += 5000


def daytype(d):
    return "weekday" if d.weekday() < 5 else ("saturday" if d.weekday() == 5 else "sunday")


def wr(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    raw = fetch_all()
    clean, dropped, seen = {}, {"missing_or_bad_count": 0, "duplicate": 0, "negative_or_zero": 0}, set()
    for r in raw:
        try:
            d = datetime.strptime(r["date"][:10], "%Y-%m-%d").date(); c = int(float(r["count"])); m = r["mode"].strip()
        except (KeyError, ValueError):
            dropped["missing_or_bad_count"] += 1; continue
        if (m, d) in seen:
            dropped["duplicate"] += 1; continue
        if c <= 0:
            dropped["negative_or_zero"] += 1; continue
        seen.add((m, d)); clean[(m, d)] = c

    base = {}
    for m in MODES:
        wk = [clean[(m, d)] for (mm, d) in clean if mm == m and BASE_START <= d <= BASE_END and daytype(d) == "weekday"]
        sa = [clean[(m, d)] for (mm, d) in clean if mm == m and BASE_START <= d <= BASE_END and daytype(d) == "saturday"]
        su = [clean[(m, d)] for (mm, d) in clean if mm == m and BASE_START <= d <= BASE_END and daytype(d) == "sunday"]
        assert len(wk) == 5 and len(sa) == 1 and len(su) == 1, (m, len(wk), len(sa), len(su))
        base[m] = {"weekday": sum(wk) / 5, "saturday": sa[0], "sunday": su[0]}
    wr("baseline.csv", ["mode", "weekday_baseline", "saturday_baseline", "sunday_baseline"],
       [[m, round(b["weekday"]), b["saturday"], b["sunday"]] for m, b in base.items()])

    daily = []
    for (m, d), c in sorted(clean.items()):
        if m in base:
            dt = daytype(d)
            daily.append([m, d.isoformat(), dt, c, round(c / base[m][dt], 4)])
        elif m in OTHER:
            daily.append([m, d.isoformat(), daytype(d), c, ""])
    daily.sort(key=lambda x: (x[0], x[1]))
    wr("daily_share.csv", ["mode", "date", "day_type", "count", "share_of_baseline"], daily)

    # monthly: mean share for weekdays and for weekend days (Sat+Sun), plus all days
    agg = defaultdict(lambda: {"wk": [], "we": [], "all": []})
    for m, ds, dt, c, s in daily:
        if s == "":
            continue
        k = (m, ds[:7]); agg[k]["all"].append(s); agg[k]["wk" if dt == "weekday" else "we"].append(s)
    mean = lambda v: round(sum(v) / len(v), 4) if v else ""
    wr("monthly_share.csv", ["mode", "month", "days", "mean_share_all", "mean_share_weekday", "mean_share_weekend"],
       [[m, mo, len(v["all"]), mean(v["all"]), mean(v["wk"]), mean(v["we"])] for (m, mo), v in sorted(agg.items())])

    # top 10 days by raw count for each mode (excluding the pandemic-era days is automatic: they are low)
    top = []
    for m in MODES + OTHER:
        rows = sorted([r for r in daily if r[0] == m], key=lambda r: -r[3])[:10]
        top += [[m, i + 1, r[1], r[3], r[4]] for i, r in enumerate(rows)]
    wr("top_days.csv", ["mode", "rank", "date", "count", "share_of_baseline"], top)

    # latest 28 days vs same weekday-type baseline, and the pandemic low point
    last = max(d for (_, d) in clean)
    summ = []
    for m in MODES:
        rows = [r for r in daily if r[0] == m]
        recent = [r for r in rows if (last - date.fromisoformat(r[1])).days < 28]
        low = min(rows, key=lambda r: r[4])
        peak = max(rows, key=lambda r: r[4])
        summ.append([m, mean([r[4] for r in recent]), mean([r[4] for r in recent if r[2] == "weekday"]),
                     mean([r[4] for r in recent if r[2] != "weekday"]), low[1], low[4], peak[1], peak[4]])
    wr("latest_summary.csv", ["mode", "last28_mean_share", "last28_weekday_share", "last28_weekend_share",
                              "low_date", "low_share", "peak_share_date", "peak_share"], summ)

    modes_found = sorted({m for (m, _) in clean})
    meta = {"dataset": "MTA Daily Ridership and Traffic: Beginning 2020", "agency": "Metropolitan Transportation Authority (MTA)",
            "id": ID, "link": f"https://data.ny.gov/d/{ID}", "api": BASE, "pulled": date.today().isoformat(),
            "raw_rows": len(raw), "clean_rows": len(clean), "dropped": dropped, "first_date": min(d for (_, d) in clean).isoformat(),
            "last_date": last.isoformat(), "modes_in_source": modes_found, "modes_with_baseline": MODES, "modes_raw_only": OTHER,
            "baseline_window": [BASE_START.isoformat(), BASE_END.isoformat()],
            "baseline_note": "Own baseline: Sun 2020-03-01 to Sat 2020-03-07, by day type. Saturday and Sunday are single days. Not the MTA's own 2019-based comparison.",
            "missing_dates": {m: [(min(d for (mm, d) in clean if mm == m) + __import__('datetime').timedelta(days=i)).isoformat()
                                  for i in range((max(d for (mm, d) in clean if mm == m) - min(d for (mm, d) in clean if mm == m)).days + 1)
                                  if (min(d for (mm, d) in clean if mm == m) + __import__('datetime').timedelta(days=i), ) and
                                  (m, min(d for (mm, d) in clean if mm == m) + __import__('datetime').timedelta(days=i)) not in clean][:20]
                              for m in MODES}}
    with open(os.path.join(OUT, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("rows", len(raw), "clean", len(clean), "dropped", dropped, "last", last)


if __name__ == "__main__":
    main()
