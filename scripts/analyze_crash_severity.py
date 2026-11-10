#!/usr/bin/env python3
"""Frequency vs severity tables for NYS DMV crashes (roadmap task 3.2).

Usage: python3 scripts/analyze_crash_severity.py   (run scripts/fetch_crashes.py first)
Reads data/crashes/county_severity.csv and hour_dow_severity.csv, pulls county population from data.ny.gov
(NYS Department of Labor, "Annual Population Estimates for New York State and Counties: Beginning 1970", krt9-ym2k)
and writes to data/crashes/: population_county.csv, county_frequency_severity.csv, hour_frequency_severity.csv,
daytype_hour_severity.csv, analysis_meta.json
Definitions: frequency = crashes per 1,000 residents per year (4-year total / sum of yearly populations).
Severity = share of crashes that are Fatal, and share with any injury or death (Fatal + Injury + Property Damage & Injury).
"""
import csv, json, os, time, urllib.parse, urllib.request
from collections import defaultdict
from datetime import date

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "crashes")
POP_ID = "krt9-ym2k"
FATAL = "Fatal Accident"
INJ = {"Fatal Accident", "Injury Accident", "Property Damage & Injury Accident"}
LOW_FATAL = 20  # fewer fatal crashes than this over 4 years: rate is noisy


def get(params):
    url = f"https://data.ny.gov/resource/{POP_ID}.json?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-data-script/1.0"})
    last = None
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa
            last = e; time.sleep(2 ** a)
    raise last


def rd(name):
    with open(os.path.join(D, name)) as f:
        return list(csv.DictReader(f))


def wr(name, header, rows):
    with open(os.path.join(D, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows([[r[h] for h in header] for r in rows])


def median(v):
    v = sorted(v); n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def main():
    meta_in = json.load(open(os.path.join(D, "meta.json")))
    years = meta_in["years"]
    # --- population (counties only: FIPS 36001..36123, odd numbers) ---
    rows = get({"$where": f"year in ({','.join(repr(str(y)) for y in years)}) and fips_code != '36000'", "$limit": 5000})
    pop = {}
    for r in rows:
        name = r["geography"].replace(" County", "").upper()
        pop[(name, int(r["year"]))] = int(r["population"])
    counties = sorted({k[0] for k in pop})
    poprows = [{"county": c, "year": y, "population": pop[(c, y)]} for c in counties for y in years if (c, y) in pop]
    wr("population_county.csv", ["county", "year", "population"], poprows)

    # --- county table ---
    cs = defaultdict(lambda: defaultdict(int))
    for r in rd("county_severity.csv"):
        cs[r["county"]][r["severity"]] += int(r["crashes"])
    out, unmatched = [], []
    for c, sev in cs.items():
        tot = sum(sev.values())
        py = sum(pop.get((c, y), 0) for y in years)  # person-years
        if py == 0:
            unmatched.append((c, tot)); continue
        fat = sev[FATAL]; inj = sum(v for k, v in sev.items() if k in INJ)
        out.append({"county": c, "population_avg": round(py / len(years)), "crashes": tot,
                    "fatal": fat, "injury": sev["Injury Accident"], "pd_injury": sev["Property Damage & Injury Accident"],
                    "pd_only": sev["Property Damage Accident"],
                    "crashes_per_1000_per_year": round(tot / py * 1000, 2),
                    "fatal_per_100k_per_year": round(fat / py * 100000, 2),
                    "fatal_share_pct": round(fat / tot * 100, 3),
                    "injury_or_fatal_share_pct": round(inj / tot * 100, 2),
                    "low_fatal_count": int(fat < LOW_FATAL)})
    fm = median([r["crashes_per_1000_per_year"] for r in out])
    sm = median([r["injury_or_fatal_share_pct"] for r in out])
    for r in out:
        hf, hs = r["crashes_per_1000_per_year"] >= fm, r["injury_or_fatal_share_pct"] >= sm
        r["quadrant"] = ("High frequency, high severity" if hf and hs else "High frequency, low severity" if hf
                         else "Low frequency, high severity" if hs else "Low frequency, low severity")
    out.sort(key=lambda r: -r["crashes_per_1000_per_year"])
    wr("county_frequency_severity.csv", list(out[0].keys()), out)

    # --- hour of day (statewide) and weekday/weekend ---
    h = defaultdict(lambda: defaultdict(int)); dt = defaultdict(lambda: defaultdict(int))
    for r in rd("hour_dow_severity.csv"):
        n = int(r["crashes"]); h[int(r["hour"])][r["severity"]] += n
        dt[("Weekend" if r["day"] in ("Saturday", "Sunday") else "Weekday", int(r["hour"]))][r["severity"]] += n
    grand = sum(sum(s.values()) for s in h.values())

    def hrow(key, sev, extra):
        tot = sum(sev.values()); inj = sum(v for k, v in sev.items() if k in INJ)
        return {**extra, "crashes": tot, "fatal": sev[FATAL], "injury_or_fatal": inj,
                "fatal_per_1000_crashes": round(sev[FATAL] / tot * 1000, 2),
                "injury_or_fatal_share_pct": round(inj / tot * 100, 2)}
    hr = []
    for k in range(24):
        r = hrow(k, h[k], {"hour": k}); r["share_of_all_crashes_pct"] = round(r["crashes"] / grand * 100, 2); hr.append(r)
    wr("hour_frequency_severity.csv", list(hr[0].keys()), hr)
    dr = [hrow(k, dt[k], {"daytype": k[0], "hour": k[1]}) for k in sorted(dt)]
    wr("daytype_hour_severity.csv", list(dr[0].keys()), dr)

    state_tot = sum(r["crashes"] for r in out)
    meta = {"pulled": date.today().isoformat(), "script": "scripts/analyze_crash_severity.py",
            "population_dataset": "Annual Population Estimates for New York State and Counties: Beginning 1970",
            "population_agency": "NYS Department of Labor", "population_link": f"https://data.ny.gov/d/{POP_ID}",
            "population_years": years, "counties_matched": len(out), "crashes_matched": state_tot,
            "crashes_total": meta_in["total_crashes"], "unmatched_counties": unmatched,
            "median_frequency": fm, "median_injury_or_fatal_share_pct": sm, "low_fatal_threshold": LOW_FATAL,
            "hour_total_check": grand}
    json.dump(meta, open(os.path.join(D, "analysis_meta.json"), "w"), indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
