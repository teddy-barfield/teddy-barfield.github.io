#!/usr/bin/env python3
"""Fetch OPRHP State Park annual attendance (data.ny.gov 8f3n-xj78) and write small processed files.

Usage: python3 scripts/fetch_parks_attendance.py
Writes to data/parks-attendance/: attendance_long.csv (facility-year), facility_summary.csv
(one row per facility), region_year.csv, year_total.csv, meta.json
"""
import csv, json, os, time, urllib.parse, urllib.request
from collections import defaultdict
from datetime import date

ID = "8f3n-xj78"
BASE = f"https://data.ny.gov/resource/{ID}.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "parks-attendance")
MIN_BASE = 50000  # a facility needs this many visits in the base period to get a growth rate


def get(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-data-script/1.0", "Accept": "application/json"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa
            last = e
            time.sleep(2 ** attempt)
    raise last


def fetch_all():
    rows, off = [], 0
    while True:
        page = get({"$select": "year,oprhp_region,county,facility,attendance",
                    "$order": "year,oprhp_region,county,facility", "$limit": 1000, "$offset": off})
        rows += page
        if len(page) < 1000:
            return rows
        off += 1000


def clean(raw):
    out, dropped, seen = [], {"missing_field": 0, "duplicate": 0}, set()
    for r in raw:
        if not all(r.get(k) for k in ("year", "facility", "oprhp_region", "attendance")):
            dropped["missing_field"] += 1
            continue
        o = {"year": int(r["year"]), "region": " ".join(r["oprhp_region"].split()),
             "county": " ".join(r.get("county", "").split()), "facility": " ".join(r["facility"].split()),
             "attendance": int(float(r["attendance"]))}
        key = (o["year"], o["region"], o["county"], o["facility"])
        if key in seen:
            dropped["duplicate"] += 1
            continue
        seen.add(key)
        out.append(o)
    # Two different parks can share a name (Robert Moses): if a name appears twice in one year, add the county.
    cnt = defaultdict(int)
    for o in out:
        cnt[(o["facility"], o["year"])] += 1
    dup_names = {o["facility"] for o in out if cnt[(o["facility"], o["year"])] > 1}
    for o in out:
        if o["facility"] in dup_names:
            o["facility"] = f'{o["facility"]} ({o["county"]})'
        if o["region"] == "Saratoga":  # same region, two spellings across years
            o["region"] = "Saratoga/Capital"
    return out, dropped


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    raw = fetch_all()
    rows, dropped = clean(raw)
    years = sorted({r["year"] for r in rows})
    y0, y1 = years[0], years[-1]
    write("attendance_long.csv", ["year", "region", "county", "facility", "attendance"],
          [[r["year"], r["region"], r["county"], r["facility"], r["attendance"]] for r in rows])

    tot, reg = defaultdict(int), defaultdict(int)
    nfac = defaultdict(int)
    for r in rows:
        tot[r["year"]] += r["attendance"]; nfac[r["year"]] += 1
        reg[(r["year"], r["region"])] += r["attendance"]
    write("year_total.csv", ["year", "facilities", "attendance"], [[y, nfac[y], tot[y]] for y in years])
    regions = sorted({r["region"] for r in rows})
    write("region_year.csv", ["year", "region", "attendance"],
          [[y, g, reg[(y, g)]] for y in years for g in regions if (y, g) in reg])

    # One entry per facility name; region/county come from the facility's latest year (names and counties
    # are re-typed inconsistently across years in the source, e.g. "Onedia", "Orange/Rockland").
    fac, latest = defaultdict(dict), {}
    for r in sorted(rows, key=lambda r: r["year"]):
        fac[r["facility"]][r["year"]] = r["attendance"]
        latest[r["facility"]] = (r["region"], r["county"])
    avg = lambda d, ys: (sum(d[y] for y in ys if y in d) / sum(1 for y in ys if y in d)) if any(y in d for y in ys) else ""
    early, late = list(range(y0, y0 + 3)), list(range(y1 - 2, y1 + 1))
    hdr = ["region", "county", "facility", "years_listed", "first_year", "latest_year", f"att_{y1}", f"avg_{early[0]}_{early[-1]}",
           f"avg_{late[0]}_{late[-1]}", "growth_pct", "continuous"] + [f"y{y}" for y in years]
    table = []
    for f, d in sorted(fac.items()):
        g, c = latest[f]
        a, b = avg(d, early), avg(d, late)
        full = all(d.get(y, 0) > 0 for y in years)  # reported, and above zero, every year
        growth = round((b / a - 1) * 100, 1) if full and a != "" and a >= MIN_BASE and b != "" else ""
        table.append([g, c, f, len(d), min(d), max(d), d.get(y1, ""), round(a, 1) if a != "" else "",
                      round(b, 1) if b != "" else "", growth, int(full)] + [d.get(y, "") for y in years])
    write("facility_summary.csv", hdr, table)

    meta = {"dataset": "State Park Annual Attendance Figures by Facility: Beginning 2003",
            "agency": "New York State Office of Parks, Recreation and Historic Preservation (OPRHP)",
            "resource_id": ID, "url": f"https://data.ny.gov/d/{ID}", "api": BASE,
            "pulled": date.today().isoformat(), "rows_fetched": len(raw), "rows_kept": len(rows),
            "dropped": dropped, "years": [y0, y1], "facilities": len(fac), "regions": regions,
            "facilities_continuous": sum(1 for r in table if r[10] == 1),
            "growth_rule": f"reported above zero in every year, average of {early[0]}-{early[-1]} at least {MIN_BASE}, "
                           f"growth = avg {late[0]}-{late[-1]} / avg {early[0]}-{early[-1]} - 1",
            "zero_attendance_rows": sum(1 for r in rows if r["attendance"] == 0)}
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
