#!/usr/bin/env python3
"""Aggregate NYS DMV motor vehicle crash cases (data.ny.gov e8ky-4vqe) on the server and write small files.

Usage: python3 scripts/fetch_crashes.py
Every table is a SoQL $group query, so no crash-level rows are downloaded. Each file is long format:
dimension columns + severity + crashes. Writes to data/crashes/: county_severity.csv, month_severity.csv,
hour_dow_severity.csv, weather_severity.csv, road_surface_severity.csv, lighting_severity.csv,
year_severity.csv, meta.json
"""
import csv, json, os, time, urllib.parse, urllib.request
from datetime import date

ID = "e8ky-4vqe"
BASE = f"https://data.ny.gov/resource/{ID}.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "crashes")
SEV = "accident_descriptor"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-data-script/1.0", "Accept": "application/json"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa
            last = e
            time.sleep(2 ** attempt)
    raise last


def agg(select_dims, where=None):
    """select_dims: list of (soql_expression, alias). Returns list of dicts with alias keys + severity + crashes."""
    sel = ",".join(f"{e} as {a}" for e, a in select_dims) + f",{SEV} as severity,count(*) as crashes"
    grp = ",".join([a for _, a in select_dims] + ["severity"])
    p = {"$select": sel, "$group": grp, "$limit": 50000}
    if where:
        p["$where"] = where
    rows = get(p)
    return [{**{a: r.get(a) for _, a in select_dims}, "severity": r["severity"], "crashes": int(r["crashes"])} for r in rows]


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header)
        w.writerows([[r[h] for h in header] for r in rows])
    return sum(r["crashes"] for r in rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    yr = agg([("year", "year")])
    for r in yr:
        r["year"] = int(r["year"])
    yr.sort(key=lambda r: (r["year"], r["severity"]))
    total = write("year_severity.csv", ["year", "severity", "crashes"], yr)
    totals = {}

    def tidy(rows, keys, ints=()):
        for r in rows:
            for k in ints:
                r[k] = int(r[k])
            for k in keys:
                r[k] = " ".join((r[k] or "Missing").split())
        return sorted(rows, key=lambda r: tuple(r[k] for k in keys) + (r["severity"],))

    county = tidy(agg([("year", "year"), ("county_name", "county")]), ["county"], ["year"])
    month = tidy(agg([("year", "year"), ("date_extract_m(date)", "month")]), [], ["year", "month"])
    month.sort(key=lambda r: (r["year"], r["month"], r["severity"]))
    weather = tidy(agg([("year", "year"), ("weather_conditions", "weather")]), ["weather"], ["year"])
    road = tidy(agg([("year", "year"), ("road_surface_conditions", "road_surface")]), ["road_surface"], ["year"])
    light = tidy(agg([("year", "year"), ("lighting_conditions", "lighting")]), ["lighting"], ["year"])

    # Hour of day: `time` is text like "5:12" or "17:40" (no leading zero), so one grouped query per hour via LIKE.
    hd = []
    for h in range(24):
        for r in agg([("day_of_week", "day")], where=f"time like '{h}:%'"):
            r["hour"] = h
            hd.append(r)
    hd.sort(key=lambda r: (DAYS.index(r["day"]), r["hour"], r["severity"]))

    totals["county_severity.csv"] = write("county_severity.csv", ["year", "county", "severity", "crashes"], county)
    totals["month_severity.csv"] = write("month_severity.csv", ["year", "month", "severity", "crashes"], month)
    totals["hour_dow_severity.csv"] = write("hour_dow_severity.csv", ["day", "hour", "severity", "crashes"], hd)
    totals["weather_severity.csv"] = write("weather_severity.csv", ["year", "weather", "severity", "crashes"], weather)
    totals["road_surface_severity.csv"] = write("road_surface_severity.csv", ["year", "road_surface", "severity", "crashes"], road)
    totals["lighting_severity.csv"] = write("lighting_severity.csv", ["year", "lighting", "severity", "crashes"], light)
    totals["year_severity.csv"] = total
    bad = {k: v for k, v in totals.items() if v != total}
    meta = {
        "dataset": "Motor Vehicle Crashes - Case Information: Four Year Window",
        "agency": "NYS Department of Motor Vehicles",
        "dataset_id": ID,
        "link": f"https://data.ny.gov/d/{ID}",
        "pulled": date.today().isoformat(),
        "years": sorted({r["year"] for r in yr}),
        "total_crashes": total,
        "file_totals": totals,
        "files_not_matching_total": bad,
        "severity_levels": sorted({r["severity"] for r in yr}),
        "method": "server-side SoQL $group aggregation; counts of crash cases, no row-level download",
    }
    with open(os.path.join(OUT, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))
    if bad:
        raise SystemExit(f"file totals disagree with the overall count: {bad}")


if __name__ == "__main__":
    main()
