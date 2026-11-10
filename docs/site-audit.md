# Site Audit (Roadmap task 0.1)

Audited 2026-11-10 at commit `b0b109a`. Nothing on the site was changed by this audit.

Method: read every tracked file, then loaded every page in headless Chromium at 390px and 1280px wide, recording console errors, chart rendering, horizontal overflow and internal-link status. One caveat: the audit sandbox could not reach `cdnjs.cloudflare.com`, so for the chart checks Chart.js 4.4.1 (the same version, taken from npm) was substituted locally. See §8.

## 1. Summary

- The site is 7 files, 196 KB in total: a homepage, three project pages, an unused template, one stylesheet and one script. There is no build step, no README, no `_config.yml` and no `.nojekyll`.
- There are **two separate visual systems**. The homepage, the math practice book page and the template share `style.css`. The two interactive projects (life insurance decoder, NYC causes of death) are self-contained "app" pages with all CSS, JS and data inline; they do not load `style.css`.
- The nav is **copy-pasted into all five pages**, in two slightly different versions. Adding a nav link means editing every page.
- Chart.js 4.4.1 from cdnjs is already the charting library on both interactive pages, which matches what task 0.2 asks for.
- Issues found (none fixed, since these pages are off-limits): the causes-of-death page scrolls sideways on a phone, and two linked PDFs do not exist.

## 2. File inventory

| File | Size | Role |
|---|---|---|
| `index.html` | 3.3 KB | Homepage: hero, About, exams, contact |
| `style.css` | 4.7 KB | Shared stylesheet (homepage, math book page, template) |
| `menu.js` | 0.7 KB | Projects dropdown behaviour, loaded by all five pages |
| `projects/term-life-decoder.html` | 40 KB | Life insurance policy decoder (interactive, self-contained) |
| `projects/nyc-causes-of-death.html` | 142 KB | NYC leading causes of death dashboard (self-contained, data inline) |
| `projects/math-practice-book.html` | 2.4 KB | Math practice book (mostly placeholders) |
| `projects/project-template.html` | 2.7 KB | Blank project template, not linked from anywhere but publicly reachable |

Not present: `files/` (resume and sample chapter are linked but not uploaded), `assets/`, `scripts/`, `data/`, `README.md`, favicon, 404 page, sitemap, any Open Graph tags.

## 3. Pages

### `index.html` (homepage)

- Title: "Teddy Barfield — Actuarial Portfolio". No meta description.
- Sections: hero (`h1` + lede), `#about`, `#exams`, `#contact`, footer.
- **About is still a placeholder** (`[placeholder - About section]`).
- Exams listed: FM (June 2025), P (July 2026), SRM (September 2026, preliminary).
- Contact: email, LinkedIn, GitHub, and a "Download resume (PDF)" button pointing to `files/resume.pdf`, which **returns 404**.
- There are no project cards on the homepage. Projects are reachable only through the nav dropdown.

### `projects/term-life-decoder.html` (Life insurance policy decoder)

The roadmap calls this the "term life visualizer".

- Inputs panel (policy type, age, term, payment period, sex, health class, death benefit, premium, payment mode, discount rate, underwriting toggle) and a results area: a verdict sentence, a 600×240 inline-SVG dot "crowd" chart, four headline figures, a plain-language reading, and one Chart.js canvas switched between four tabs (outcomes, expected value, return multiple, survival).
- Collapsible methodology section (Makeham mortality, UDD timing, EPV formulas, exclusions).
- All CSS (about 110 lines) and JS (about 375 lines) are inline. Does not load `style.css`; loads `../menu.js`.
- Layout: 1200px max width, two-column grid (300px inputs + results) that collapses to one column under 900px.
- Has a meta description (the only page that does).
- Accessibility is reasonably good: `aria-live` results, tab roles, `aria-invalid` field errors, reduced-motion handling.
- Fits 390px with no horizontal scroll. Chart renders.

### `projects/nyc-causes-of-death.html` (NYC leading causes of death)

- Dashboard: sticky 300px filter sidebar (year range, sex, race/ethnicity, searchable cause list, measure, compare-by) and a main column with a generated headline, a line chart ("Over time"), a horizontal bar chart ("Ranked by cause"), an HTML-table heatmap ("Cause by year"), a sortable summary table with CSV download, and an "About the data" notes list.
- Data is **embedded in the page**: a `RAW` array of 2,080 rows (33 causes, 2007–2021) and a `POP` object of 120 population entries. This accounts for most of the 142 KB.
- Source is named in the notes (NYC DOHMH, *New York City Leading Causes of Death*, via NYC Open Data) but there is **no link to the dataset and no pull date**, which the roadmap's data rules require of new pages.
- All CSS and JS inline. Does not load `style.css`; loads `../menu.js`.
- No meta description. Base font is 15px (the rest of the site uses 17px).
- **Horizontal overflow**: the page is 952px wide on a 390px screen and 1336px wide on a 1280px screen. Cause: the `.wrap` and `.grid` grid columns are declared `1fr`, which cannot shrink below their content's minimum width. Overriding them with `minmax(0, 1fr)` in a test brought the page back to exactly 390px and 1280px. This is a two-line fix but the page is off-limits, so it was left alone.
- Charts render with no console errors.

### `projects/math-practice-book.html`

- Uses `style.css`. Header with "Back to home", title, and a meta line ("Written in LaTeX on Overleaf").
- Both sections ("Overview", "How it's built") are **placeholders**.
- Links to `files/sample-chapter.pdf`, which **returns 404**.

### `projects/project-template.html`

- Uses `style.css`. Sections: "The question", "Approach", "Results", plus placeholder links.
- Not linked from the nav, but it is published at `/projects/project-template.html` with placeholder text and a dead `files/[report].pdf` link.

## 4. Shared CSS (`style.css`)

Design tokens (the comment in the file says the palette is taken from the resume):

| Token | Value | Use |
|---|---|---|
| `--paper` | `#FFFFFF` | Page background |
| `--sheet` | `#DCE6F2` | Light blue fills (exam cards, dropdown) |
| `--ink` | `#000000` | Text |
| `--muted` | `#4D4D4D` | Secondary text |
| `--rule` | `#D9D9D9` | Hairlines |
| `--accent` | `#376092` | Links, buttons |
| `--mark` | `#254061` | Darkest blue, hover |
| `--band-1` … `--band-5` | `#DCE6F2`, `#B9CDE5`, `#95B3D7`, `#376092`, `#254061` | Stepped stripe down the left edge |

- Type: Newsreader (serif, headings) and Public Sans (body), both from Google Fonts. Body is 17px / 1.6.
- Signature element: a fixed five-step blue stripe on the left edge (`body::before`), 1.75rem wide, narrowing to 0.6rem under 600px.
- Layout: a single `.wrap` column, 46rem max width. This suits prose but is too narrow for charts and wide tables.
- Components: `nav`, `.menu` dropdown, hero (`h1`, `.lede`), `section` + underlined `h2`, `.exams` card grid, `.back` / `.meta` / `.links` for project pages, `.contact-list`, `.button`, `footer`, `.placeholder`.
- There are no card, table, chart-container, callout or figure styles yet.
- One 600px breakpoint. Light theme only.

The two interactive pages restate a close variant of these tokens inline, with differences worth knowing about for 0.2:

| | `style.css` | Life insurance decoder | Causes of death |
|---|---|---|---|
| Light fill | `--sheet: #DCE6F2` | `--sheet: #F4F7FB` | `--panel: #F4F7FB`, `--tint: #DCE6F2` |
| Main blue | `--accent: #376092` | `--teal: #376092` | `--teal: #376092` |
| Negative / alert | none | `--brick: #B3473B` | `--ox: #9B2C2C` |
| Third colour | none | `--ochre: #C29A2E` | (palette) `#C08A2B` |
| Body size | 17px | 17px | 15px |
| Max width | 46rem | 1200px | 1240px |

The blue is identical everywhere, but it has three different names, and the two reds differ.

## 5. Shared JS (`menu.js`)

- 18 lines, no dependencies. Toggles the Projects dropdown, closes on outside click and Escape, and keeps `aria-expanded` in sync.
- Loaded at the end of `<body>` on all five pages, with a relative path (`menu.js` or `../menu.js`).
- It only handles behaviour. The nav markup itself is duplicated in each page.

## 6. Navigation

Structure on every page:

- Home
- Projects (dropdown)
  - *Actuarial*: Life insurance policy decoder
  - *Data analysis*: NYC leading causes of death
  - *Teaching*: Math practice book
- Exams (`index.html#exams`)
- Contact (`index.html#contact`)

Two variants exist:

| | Homepage, math book, template | Life insurance decoder, causes of death |
|---|---|---|
| Markup | `<nav aria-label="Main">` + `.wrap` | `<nav class="site-bar" aria-label="Site">` + `.bar` |
| Home link text | "Home" | "Teddy Barfield" (bold) |
| Styles from | `style.css` | Inline copy scoped under `.site-bar` |
| Bottom border | none | 1px rule |

Consequences:

- Any new nav entry has to be added to five files by hand, and three of those are project pages the roadmap marks off-limits.
- All links are relative (`../index.html`). A page one level deeper, such as `projects/ny-data/index.html`, needs `../../` paths, so the nav block cannot be pasted unchanged.
- The dropdown is 16rem wide and anchored left. It fits a 390px screen today.

## 7. Charts and libraries

External resources, site-wide:

| Resource | Where | Notes |
|---|---|---|
| Google Fonts: Newsreader, Public Sans | all pages | The two app pages request a slightly different weight set (adds 500, drops italic) |
| Chart.js 4.4.1, `cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js` | both app pages | Loaded in `<head>`, blocking, no `integrity` attribute |

No other libraries, frameworks, analytics or trackers.

Chart usage:

| Page | Chart | Type | Notes |
|---|---|---|---|
| Life insurance decoder | `#chart` (four tabs, one canvas) | Bar + line combo, bar, bar on a log axis, line | Colours read from CSS variables at runtime. Sets `Chart.defaults` font (Public Sans, 13px), text colour (`--muted`) and grid colour (`--rule`) |
| Life insurance decoder | `#crowd` | Hand-built inline SVG dots | Not Chart.js |
| Causes of death | `#trend` | Line | Up to 10 series, legend at bottom, 11px Public Sans |
| Causes of death | `#rank` | Horizontal bar | Single or grouped series |
| Causes of death | `#heat` | HTML table with shaded cells | Not Chart.js |

Existing categorical palette (causes-of-death page, `PAL`):

`#376092` `#9B2C2C` `#C08A2B` `#4C7A3D` `#6A4C93` `#2E86AB` `#B0607A` `#7A6A55` `#3D9970` `#8E8E3E`

Chart containers on both pages follow the same pattern: a `position: relative` box with a fixed height (360–390px) wrapping the canvas. Canvases have an `aria-label` or `aria-describedby` but no text alternative beyond the surrounding caption.

## 8. Baseline quality check

| Page | Console errors | Charts render | Fits 390px | Broken internal links |
|---|---|---|---|---|
| `index.html` | none | n/a | yes | `files/resume.pdf` (404) |
| `projects/term-life-decoder.html` | none* | yes* | yes | none |
| `projects/nyc-causes-of-death.html` | none* | yes* | **no** (952px) | none |
| `projects/math-practice-book.html` | none | n/a | yes | `files/sample-chapter.pdf` (404) |
| `projects/project-template.html` | none | n/a | yes | `files/[report].pdf` (404, placeholder) |

\* With Chart.js 4.4.1 served locally. **In the sandbox this audit ran in, requests to `cdnjs.cloudflare.com` and `data.ny.gov` were refused by the environment's network policy** (proxy answered 403). Google Fonts and npm were reachable. Unless those two hosts are allowed for the nightly runs:

- the quality gate's "every chart must render" check fails on any page that loads Chart.js from cdnjs, unless the agent substitutes a local copy as this audit did;
- no data can be pulled from the SODA API, and data.ny.gov links cannot be checked, so Milestones 1–5 cannot start.

## 9. Recommendations for task 0.2 (shared kit)

1. **Layer, don't fork.** Have new project pages load `style.css` first and `assets/css/projects.css` second. `projects.css` should add only what is missing and reuse the existing tokens (`--accent`, `--sheet`, `--rule`, `--mark`), so the stripe, fonts and nav come for free and stay in sync with the homepage.
2. **Add a wide container.** The 46rem `.wrap` is too narrow for charts. Add a wider variant (about 68–72rem) for chart and table sections and keep prose at the current measure.
3. **Components to include:** chart box (relative, fixed height, shorter on phones), figure caption, stat/figure tiles, callout, data table with a horizontal-scroll wrapper, card grid (needed by the hub in 0.3), and a "data source" block with slots for dataset name, link, agency and pull date, since the roadmap requires all four on every project page.
4. **Avoid the overflow bug by construction.** Use `minmax(0, 1fr)` for every grid column and wrap every table in an `overflow-x: auto` container. This is the exact cause of the sideways scroll on the causes-of-death page.
5. **Chart setup in one file**, for example `assets/js/charts.js`: set `Chart.defaults` the way the life insurance page already does (Public Sans, `--muted` text, `--rule` gridlines), turn on `maintainAspectRatio: false`, and export one palette. Start the palette from the existing one (`#376092`, `#9B2C2C`, `#C08A2B`, `#4C7A3D`, `#6A4C93`, …) so new charts match the old ones, and pick one red for "negative" rather than keeping both `#B3473B` and `#9B2C2C`.
6. **Stay on Chart.js 4.4.1 from cdnjs**, the version already in use, and add `defer` plus an `integrity` hash. Chart.js has no built-in map or heatmap, which matters for task 3.3: ranked bars and an HTML-table heatmap (the approach the causes-of-death page already uses) need no extra library.
7. **Template naming.** The roadmap asks for `projects/_template.html`. GitHub Pages builds with Jekyll by default, and Jekyll does not publish files whose names start with an underscore, so the new template will stay out of the live site. That is the desired behaviour, but it only holds while there is no `.nojekyll` file. The old `projects/project-template.html` is public and becomes redundant; removing it needs Teddy's approval.
8. **Load data from files, not inline.** New pages should `fetch()` small JSON files from `data/<project>/` rather than embedding arrays, in line with the roadmap's data rules. Use paths relative to the page.
9. **Give every new page** a meta description and a visible "last pulled" date from the start, so tasks 6.2 and 6.3 are a check rather than a retrofit.

## 10. Recommendations for task 0.3 (hub page)

1. **Paths.** `projects/ny-data/index.html` sits two levels deep, so its nav, stylesheet and script links need `../../`. Consider making the template use root-relative paths (`/style.css`); this works because the site is a user page served from the domain root, but such pages can no longer be previewed by opening the file directly.
2. **The nav edit touches off-limits pages.** The roadmap says "link it from the homepage nav". The homepage nav can be edited, but the same nav is duplicated in the three project pages that the protocol marks off-limits. Options:
   - (a) edit the nav block only in all pages, which keeps the nav consistent but needs Teddy to allow nav-only edits to the existing projects;
   - (b) add the link to the homepage (and the template) only, and accept that the three older pages show a nav without it until 6.1;
   - (c) move the nav into `menu.js` so it is defined once, which is the durable fix but a larger change to every page.

   Recommended: (a) now, since it is a one-line `<li>` per page, and consider (c) at 6.1.
3. **Where the link goes.** Either a new "New York data" group in the Projects dropdown with one "New York by the Numbers" entry, or a top-level nav link beside "Projects". The dropdown group is the smaller change and avoids crowding the nav on a phone.
4. **Cards.** Each card: title, one-line question, topic tag (Insurance, Parks, Safety, Labor, Transit), source agency and a status. Show unbuilt projects as "Coming soon" cards with no link, or leave them off until they ship. This is a choice for Teddy, since "coming soon" cards are visible to anyone reading the portfolio.
5. **Use the homepage nav variant** (`<nav aria-label="Main">`, styled by `style.css`) for the hub and all new pages, rather than the inline `.site-bar` copy.
6. **Homepage.** There are no project cards on the homepage today, so the hub will be reachable only from the dropdown until 6.1. That is consistent with the roadmap but worth knowing.

## 11. Open questions for Teddy

These are listed in the run report as well.

1. Allow `data.ny.gov` and `cdnjs.cloudflare.com` in the scheduled run's environment (§8).
2. Rule on nav-only edits to the off-limits project pages (§10, item 2).
3. `ROADMAP.md`, `LOG.md` and `docs/` are in the published repo. GitHub Pages' default Jekyll build is expected to render Markdown files as public pages (for example `/ROADMAP.html`). If that is unwanted, add a `_config.yml` with an `exclude:` list. This was not verified against the live site from the sandbox.
4. Fix the off-limits issues yourself or name them in a task: causes-of-death overflow, missing `files/resume.pdf` and `files/sample-chapter.pdf`, About and math-book placeholders.
5. Decide whether "coming soon" cards appear on the hub (§10, item 4).
