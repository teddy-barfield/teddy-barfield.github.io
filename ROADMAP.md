# Portfolio Roadmap — NY Open Data Projects

Owner: Teddy Barfield · Repo: `teddy-barfield/teddy-barfield.github.io` (plain HTML/CSS/JS, GitHub Pages)
Goal: Show that I care about New York issues and can analyze state data with an actuarial eye. Mix serious topics with optimistic ones.
Cadence: one task per night, pushed straight to `main`.

For the scheduled agent: this file is the source of truth. Each night, do the first unchecked task below, follow the Nightly Run Protocol, check the task off, and add a line to `LOG.md`.

## Nightly Run Protocol

1. Clone the repo. Read `ROADMAP.md` and the last 5 entries in `LOG.md`.
2. Pick the first `- [ ]` task. Do only that task. If it's too big for one night, split it into sub-tasks in this file, do the first one, and commit the split.
3. Data rules
   * Pull from the data.ny.gov SODA API (`https://data.ny.gov/resource/<id>.json` or `.csv`). Use `$select`, `$where` and `$group` to aggregate on the server.
   * Keep a reproducible script in `scripts/` (Python) that writes small processed files to `data/<project>/`. Never commit raw dumps over 5 MB.
   * Every project page shows the dataset name, a link, the agency and the date the data was pulled.
4. Quality gate (required before pushing to main)
   * Open every changed page in headless Chromium. It must have no console errors, every chart must render, and the page must fit a 390px-wide phone screen.
   * Check every internal link and every data.ny.gov link.
   * Cross-check every number quoted in the text against the processed data file.
   * If any check fails: push to a `wip/<task>` branch instead of `main`, leave the task unchecked, and explain why in `LOG.md`.
5. Off-limits unless a task names them: resume, About/bio text, contact info, and the existing projects (math practice book, term life visualizer, NYC causes-of-death project). Never invent personal experiences or opinions in Teddy's voice. Write-ups stay analytical.
6. Commit with clear messages, push, check the task off, and append to `LOG.md`: date · task · what shipped · anything Teddy should review.

## Milestone 0 — Foundations (nights 1–3)

- [x] 0.1 Audit: Inventory the existing site (pages, styles, nav, projects). Write `docs/site-audit.md`. Create `LOG.md`. Don't restyle anything yet.
- [x] 0.2 Shared kit: Create `assets/css/projects.css`, a project-page template (`projects/_template.html`) and a chart setup (Chart.js from cdnjs, one consistent palette). Keep the existing site's look.
- [x] 0.3 Hub page: Create `projects/ny-data/index.html`, a "New York by the Numbers" hub with project cards. Link it from the homepage nav. The nav is duplicated in every page, so this task may also edit the nav block (and only the nav block) of the existing project pages to keep it consistent.

## Milestone 1 — Insurance: Auto Insurer Complaint Rankings (nights 4–6)

Dataset: Automobile Insurance Company Complaint Rankings: Beginning 2009 (DFS)

- [x] 1.1 Write the fetch and clean script. Build a ranking-over-time table and a complaint-ratio distribution.
- [x] 1.2 Build the page: a sortable insurer table, a trend line per insurer and a "best and most improved" callout.
- [x] 1.3 Write the analysis and methodology: what a complaint ratio is, why it's normalized by premium, and its limitations. Use actuarial framing.

## Milestone 2 — Fun: NY State Parks Attendance (nights 7–9)

Dataset: State Park Annual Attendance Figures by Facility: Beginning 2003 (OPRHP)

- [x] 2.1 Write the fetch and clean script. Total attendance by year, region and facility.
- [x] 2.2 Build the page: the record-attendance trend, the top 15 parks, the fastest-growing parks and a "hidden gems" list.
- [x] 2.3 Write it up with an optimistic headline ("New Yorkers keep going outside"). Add a small "find a park near you" filter by region.

## Milestone 3 — Transportation & Safety: Motor Vehicle Crashes (nights 10–13)

Dataset: Motor Vehicle Crashes – Case / Individual / Vehicle Information (DMV)

- [x] 3.1 Aggregate crash counts and severity by county, month, hour, weather and road condition, using server-side aggregation.
- [x] 3.2 Add a frequency and severity analysis (the actuarial angle): crash frequency vs. severity mix by county and time of day.
- [x] 3.3 Build the page: a county map or ranked bars, an hour-by-day heatmap and condition breakdowns.
- [x] 3.4 Write up the methodology and caveats (reporting thresholds, exposure not normalized → add county population or VMT if feasible).

## Milestone 4 — Labor & Economy: Unemployment Across NY (nights 14–16)

Dataset: Local Area Unemployment Statistics: Beginning 1976 (DOL)

- [x] 4.1 Fetch the data and build county and metro-area series.
- [x] 4.2 Build the page: a county small-multiples chart, the 2020 shock and recovery, and a regional comparison.
- [x] 4.3 Write up a "recovery" storyline: which regions bounced back fastest.

## Milestone 5 — Optimistic: The Subway Comeback (nights 17–19)

Dataset: MTA Daily Ridership and Traffic: Beginning 2020

- [x] 5.1 Fetch the data. Daily ridership by mode as a share of pre-pandemic levels.
- [x] 5.2 Build the page: recovery curves by mode, weekday vs. weekend and the biggest days.
- [ ] 5.3 Write it up as a positive comeback story, with honest caveats.

## Milestone 6 — Polish (nights 20–22)

- [ ] 6.1 Refresh the homepage so the NY Data hub is featured. Make cards and nav consistent.
- [ ] 6.2 Accessibility and performance pass: alt text, contrast, keyboard navigation, chart text alternatives, Lighthouse-style checks.
- [ ] 6.3 Add Open Graph and meta tags to every project page, and update the repo README with a project list.

## Milestone 7 — Ongoing

* 7.x Monthly refresh (first night of each month): re-run all `scripts/`, update the data and "last pulled" dates, and fix anything broken.
* Backlog of ideas (Teddy promotes one to a numbered task when ready):
   * DFS health insurance premium rate filings / rate requests
   * NY Lottery: where the prize money goes (fun)
   * DEC fish stocking: what's in your local lake (fun)
   * Farmers markets / Pride of NY farm products (fun)
   * Life insurance or annuity data from DFS, tying into the term life visualizer
