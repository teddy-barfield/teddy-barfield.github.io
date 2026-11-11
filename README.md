# Teddy Barfield — Actuarial Portfolio

Source for https://teddy-barfield.github.io/ — plain HTML, CSS and JavaScript on GitHub Pages. No build step.

## New York by the Numbers

Data projects built on New York State open data (data.ny.gov). The hub is at [/projects/ny-data/](https://teddy-barfield.github.io/projects/ny-data/).

| Project | Page | Source dataset (agency) | Data folder | Script |
|---|---|---|---|---|
| Auto insurer complaint rankings | [auto-complaints](https://teddy-barfield.github.io/projects/auto-complaints.html) | Automobile Insurance Company Complaint Rankings: Beginning 2009 (Dept. of Financial Services, `h2wd-9xfe`) | `data/auto-complaints/` | `scripts/fetch_auto_complaints.py` |
| State park attendance | [state-parks](https://teddy-barfield.github.io/projects/state-parks.html) | State Park Annual Attendance Figures by Facility: Beginning 2003 (Parks, Recreation and Historic Preservation, `8f3n-xj78`) | `data/parks-attendance/` | `scripts/fetch_parks_attendance.py` |
| Motor vehicle crashes | [motor-vehicle-crashes](https://teddy-barfield.github.io/projects/motor-vehicle-crashes.html) | Motor Vehicle Crashes - Case Information: Four Year Window (DMV, `e8ky-4vqe`); county population from NYS Dept. of Labor (`krt9-ym2k`) | `data/crashes/` | `scripts/fetch_crashes.py`, `scripts/analyze_crash_severity.py` |
| Unemployment across New York | [unemployment](https://teddy-barfield.github.io/projects/unemployment.html) | Local Area Unemployment Statistics: Beginning 1976 (Dept. of Labor, `5hyu-bdh8`) | `data/unemployment/` | `scripts/fetch_unemployment.py` |
| The subway comeback | [subway-comeback](https://teddy-barfield.github.io/projects/subway-comeback.html) | MTA Daily Ridership and Traffic: Beginning 2020 (MTA, `sayj-mze2`) | `data/mta-ridership/` | `scripts/fetch_mta_ridership.py` |

Each page states its dataset, link, agency and the date the data was pulled. Figures on the pages are computed in the browser from the small processed files in `data/`; see each folder's `meta.json` for the pull date and cleaning counts.

## Other projects

- [Life insurance policy decoder](https://teddy-barfield.github.io/projects/term-life-decoder.html)
- [NYC leading causes of death](https://teddy-barfield.github.io/projects/nyc-causes-of-death.html)
- [Math practice book](https://teddy-barfield.github.io/projects/math-practice-book.html)

## Refreshing the data

Run a script from the repository root, for example `python3 scripts/fetch_auto_complaints.py`. Each script queries the data.ny.gov SODA API, aggregates on the server where possible and writes small files to `data/<project>/`.

After a refresh, run `node scripts/make_og_images.js` (needs Node and Playwright with Chromium) to rebuild the link preview images in `assets/img/`. Each image is a 1200 x 630 card made from the page's own title and one of its own charts, so it is a snapshot that goes stale when the data changes.

## Layout

- `assets/css/projects.css`, `assets/js/charts.js` — shared styles and chart setup (Chart.js from cdnjs).
- `assets/img/og-*.png` — link preview images (`og:image`), built by `scripts/make_og_images.js`.
- `projects/_template.html` — starting point for a new project page. Each data page carries a breadcrumb and previous/next project links in plain HTML; when adding a page, extend that chain as well as the hub cards and the Projects menu.
- `ROADMAP.md`, `LOG.md`, `docs/site-audit.md` — plan, run log and site inventory.
