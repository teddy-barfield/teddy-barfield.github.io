#!/usr/bin/env python3
"""Fetch NYS DOL Local Area Unemployment Statistics (data.ny.gov 5hyu-bdh8) and write small processed files.

Usage: python3 scripts/fetch_unemployment.py
Writes to data/unemployment/: areas.csv (one row per area), monthly.csv (area x month, 2000 onward),
annual.csv (area x year), recovery_summary.csv (2020 shock and recovery metrics), meta.json
Notes: the series is NOT seasonally adjusted, so month-to-month changes include seasonal swings. Recovery metrics
therefore compare each month with the SAME calendar month of 2019.
"""
import csv, json, os, time, urllib.parse, urllib.request
from collections import defaultdict
from datetime import date

ID = "5hyu-bdh8"
BASE = f"https://data.ny.gov/resource/{ID}.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "unemployment")
START = 2000
TYPES = {"State": "state", "County": "county", "Metropolitan Statistical Area": "metro", "Labor Market Area": "region"}
TOL = 1.0  # percentage points above the same month of 2019 that still counts as "recovered" (my choice)


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
    types = ",".join(repr(t) for t in TYPES)
    rows, off = [], 0
    while True:
        page = get({"$select": "area_type,area,year,month,laborforce,employed,unemployed,unemployment_rate",
                    "$where": f"area_type in ({types}) and year >= {START}",
                    "$order": "area_type,area,year,month", "$limit": 5000, "$offset": off})
        rows += page
        if len(page) < 5000:
            return rows
        off += 5000


def wr(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows([[r[h] for h in header] for r in rows])


def main():
    os.makedirs(OUT, exist_ok=True)
    raw = fetch_all()
    clean, dropped, seen = [], {"missing_field": 0, "duplicate": 0}, set()
    for r in raw:
        try:
            o = {"kind": TYPES[r["area_type"]], "area": " ".join(r["area"].split()), "year": int(r["year"]),
                 "month": int(r["month"]), "labor_force": int(r["laborforce"]), "employed": int(r["employed"]),
                 "unemployed": int(r["unemployed"]), "rate": float(r["unemployment_rate"])}
        except (KeyError, ValueError):
            dropped["missing_field"] += 1; continue
        k = (o["kind"], o["area"], o["year"], o["month"])
        if k in seen:
            dropped["duplicate"] += 1; continue
        seen.add(k); clean.append(o)
    # the metro area and the labor market region are both called "New York City": keep them apart
    for o in clean:
        if o["kind"] == "metro" and o["area"] == "New York City":
            o["area"] = "New York City Metro Area"
    clean.sort(key=lambda o: (o["kind"], o["area"], o["year"], o["month"]))
    wr("monthly.csv", ["kind", "area", "year", "month", "labor_force", "employed", "unemployed", "rate"], clean)

    areas = sorted({(o["kind"], o["area"]) for o in clean})
    wr("areas.csv", ["kind", "area"], [{"kind": k, "area": a} for k, a in areas])

    ann = defaultdict(lambda: [0, 0, 0, 0])  # months, LF sum, unemployed sum, employed sum
    for o in clean:
        a = ann[(o["kind"], o["area"], o["year"])]
        a[0] += 1; a[1] += o["labor_force"]; a[2] += o["unemployed"]; a[3] += o["employed"]
    arows = [{"kind": k, "area": a, "year": y, "months": v[0],
              "avg_labor_force": round(v[1] / v[0]), "rate": round(100 * v[2] / v[1], 2)}
             for (k, a, y), v in sorted(ann.items())]
    wr("annual.csv", ["kind", "area", "year", "months", "avg_labor_force", "rate"], arows)

    by = defaultdict(dict)
    for o in clean:
        by[(o["kind"], o["area"])][(o["year"], o["month"])] = o
    last = max((o["year"], o["month"]) for o in clean)
    srows = []
    for (k, a), s in sorted(by.items()):
        pre = s.get((2020, 2)); base19 = {m: s[(2019, m)]["rate"] for m in range(1, 13) if (2019, m) in s}
        shock = [s[(2020, m)] for m in range(3, 13) if (2020, m) in s]
        if not (pre and shock and len(base19) == 12):
            continue
        pk = max(shock, key=lambda o: o["rate"])
        rec = None
        for ym in sorted(x for x in s if x > (2020, pk["month"])):
            if ym[0] < 2020 or (ym[0] == 2020 and ym[1] <= pk["month"]):
                continue
            if s[ym]["rate"] <= base19[ym[1]] + TOL:
                rec = ym; break
        lm = s[last] if last in s else s[max(s)]
        months_back = (rec[0] - 2020) * 12 + rec[1] - pk["month"] if rec else ""
        srows.append({"kind": k, "area": a, "feb2020_rate": pre["rate"], "peak_rate": pk["rate"],
                      "peak_month": f"2020-{pk['month']:02d}", "jump_pts": round(pk["rate"] - pre["rate"], 1),
                      "avg2019_rate": round(sum(base19.values()) / 12, 2),
                      "recovered_month": f"{rec[0]}-{rec[1]:02d}" if rec else "",
                      "months_peak_to_recovery": months_back,
                      "latest_month": f"{lm['year']}-{lm['month']:02d}", "latest_rate": lm["rate"],
                      "latest_vs_same_month_2019": round(lm["rate"] - base19[lm["month"]], 1)})
    wr("recovery_summary.csv", ["kind", "area", "feb2020_rate", "peak_rate", "peak_month", "jump_pts", "avg2019_rate",
                                "recovered_month", "months_peak_to_recovery", "latest_month", "latest_rate",
                                "latest_vs_same_month_2019"], srows)

    present = {(o["year"], o["month"]) for o in clean if o["kind"] == "state"}
    allm = [(y, m) for y in range(START, last[0] + 1) for m in range(1, 13) if (y, m) <= last]
    meta = {"dataset": "Local Area Unemployment Statistics: Beginning 1976", "agency": "New York State Department of Labor",
            "resource_id": ID, "url": f"https://data.ny.gov/d/{ID}", "api": BASE, "pulled": date.today().isoformat(),
            "rows_fetched": len(raw), "rows_kept": len(clean), "dropped": dropped, "first_year_kept": START,
            "latest_month": f"{last[0]}-{last[1]:02d}", "missing_months_statewide": [f"{y}-{m:02d}" for y, m in allm if (y, m) not in present],
            "areas": {t: sum(1 for k, _ in areas if k == t) for t in TYPES.values()},
            "seasonally_adjusted": False, "recovery_tolerance_pts": TOL,
            "recovery_definition": "first month after the 2020 peak whose rate is within 1.0 point of the same calendar month of 2019"}
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=2)
    print(json.dumps(meta, indent=1)[:900])


if __name__ == "__main__":
    main()
