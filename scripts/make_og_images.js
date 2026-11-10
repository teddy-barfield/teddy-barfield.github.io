#!/usr/bin/env node
// Builds the link preview images (og:image / twitter:image) for the NY data hub and the data pages.
//
//   node scripts/make_og_images.js            (from the repository root; needs Node and Playwright with Chromium)
//
// For each page it opens the real page in headless Chromium, takes a picture of one of that page's
// own charts (drawn from the processed files in data/), and sets it on a 1200 x 630 card next to the
// page's own <h1>, in the site's palette, fonts and stepped stripe (all read from style.css).
// The hub has no chart, so its card lists the project names from the hub's own cards.
// Nothing is typed here except which chart to use: titles, chart headings and numbers come from the pages.
// The images are snapshots: re-run this after a data refresh so the picture matches the page.

const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'assets', 'img');
const MAX_BYTES = 300 * 1024;
const W = 1200, H = 630, SCALE = 1.5;       // card is laid out at 800 x 420 CSS px and captured at 1.5x
const CHART_W = 456, CHART_H = 324;         // CSS px; close to the size the chart has on a phone

const PAGES = [
  { out: 'og-ny-data.png',               page: 'projects/ny-data/index.html' },
  { out: 'og-auto-complaints.png',       page: 'projects/auto-complaints.html',       canvas: '#chart-trend', chartH: 382 },   // taller: four legend rows and a long axis title
  { out: 'og-state-parks.png',           page: 'projects/state-parks.html',           canvas: '#c-total' },
  { out: 'og-motor-vehicle-crashes.png', page: 'projects/motor-vehicle-crashes.html', canvas: '#c-hour' },
  { out: 'og-unemployment.png',          page: 'projects/unemployment.html',          canvas: '#c-state' },
  { out: 'og-subway-comeback.png',       page: 'projects/subway-comeback.html',       canvas: '#c-mode' }
];

const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.csv': 'text/csv', '.png': 'image/png' };

function serve() {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split('?')[0]);
    if (p.endsWith('/')) p += 'index.html';
    const file = path.join(ROOT, p);
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server)));
}

function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function cardHtml(base, info, chartPng) {
  const CHART_H = info.chartH;
  const right = chartPng
    ? `<figure><figcaption>${esc(info.chartHeading)}</figcaption><img src="data:image/png;base64,${chartPng.toString('base64')}" width="${CHART_W}" height="${CHART_H}" alt=""></figure>`
    : `<ul>${info.projects.map(p => `<li>${esc(p)}</li>`).join('')}</ul>`;
  return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="${base}/style.css">
<style>
  html,body{width:800px;height:420px;overflow:hidden}
  body{padding-left:0;font:400 15px/1.4 var(--sans);color:var(--ink);background:var(--paper)}
  body::before{width:24px}
  .card{position:absolute;inset:0 0 0 24px;display:flex;align-items:stretch}
  .text{flex:1 1 0;min-width:0;padding:36px 16px 30px 28px;display:flex;flex-direction:column}
  .eyebrow{font:600 12.5px/1.3 var(--sans);letter-spacing:.09em;text-transform:uppercase;color:var(--accent)}
  h1{font:600 37px/1.1 var(--serif);color:var(--mark);margin-top:14px}
  .site{margin-top:auto;font:500 14px/1.4 var(--sans);color:var(--muted)}
  .site b{display:block;font-weight:600;color:var(--ink);font-size:16px}
  .pic{flex:0 0 ${CHART_W + 24}px;display:flex;align-items:center;padding-right:24px}
  figure{width:${CHART_W}px}
  figcaption{font:600 15px/1.3 var(--sans);color:var(--ink);margin:0 0 8px;border-left:4px solid var(--accent);padding-left:9px}
  figure img{display:block}
  ul{list-style:none;width:${CHART_W}px;background:var(--tint,#F4F7FB);border-left:4px solid var(--accent);padding:12px 22px}
  li{font:600 21px/1.25 var(--serif);color:var(--mark);padding:10px 0;border-bottom:1px solid var(--rule)}
  li:last-child{border-bottom:0}
</style></head><body>
<div class="card">
  <div class="text">
    <div class="eyebrow">${esc(info.eyebrow)}</div>
    <h1>${esc(info.title)}</h1>
    <div class="site"><b>${esc(info.owner)}</b>teddy-barfield.github.io</div>
  </div>
  <div class="pic">${right}</div>
</div></body></html>`;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();
  let failed = false;
  try {
    // The hub's own <h1> is the label printed above every project title.
    const ctx = await browser.newContext({ viewport: { width: 600, height: 900 }, deviceScaleFactor: SCALE });
    const hub = await ctx.newPage();
    await hub.goto(`${base}/projects/ny-data/index.html`, { waitUntil: 'networkidle' });
    const hubTitle = (await hub.textContent('header h1')).trim();
    const owner = (await hub.getAttribute('meta[property="og:site_name"]', 'content')).trim();
    const projects = await hub.$$eval('.cards .card h3', els => els.map(e => e.textContent.trim()));
    await hub.close();

    for (const p of PAGES) {
      const page = await ctx.newPage();
      const errors = [];
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      page.on('pageerror', e => errors.push(String(e)));
      const chartH = p.chartH || CHART_H;
      if (p.canvas) {
        // Size the chart's own box before the page draws it, so Chart.js lays the chart out once at card size.
        await page.addInitScript(a => {
          document.addEventListener('DOMContentLoaded', () => {
            const st = document.createElement('style');
            st.textContent = `.chart-box:has(${a.sel}){width:${a.w}px!important;height:${a.h}px!important}`;
            document.head.appendChild(st);
          });
        }, { sel: p.canvas, w: CHART_W, h: chartH });
      }
      await page.goto(`${base}/${p.page}`, { waitUntil: 'networkidle' });
      const title = (await page.textContent('header h1')).trim();
      const info = { title, owner, projects, chartH, eyebrow: p.canvas ? hubTitle : 'New York State open data' };
      let chartPng = null;
      if (p.canvas) {
        info.chartHeading = await page.$eval(p.canvas, c => c.closest('section').querySelector('h2').textContent.trim());
        await page.waitForTimeout(1500);                           // let Chart.js finish its opening animation
        const painted = await page.$eval(p.canvas, c => {
          const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
          for (let i = 3; i < d.length; i += 4) if (d[i]) return true;
          return false;
        });
        if (!painted) throw new Error(`${p.page}: chart ${p.canvas} is blank`);
        chartPng = await page.locator(p.canvas).screenshot({ omitBackground: false });
      }
      if (errors.length) throw new Error(`${p.page}: console errors: ${errors.join(' | ')}`);
      await page.close();

      const card = await ctx.newPage();
      await card.setViewportSize({ width: W / SCALE, height: H / SCALE });
      await card.goto(`${base}/style.css`);                       // same origin, so the card can load the site's CSS
      await card.setContent(cardHtml(base, info, chartPng), { waitUntil: 'networkidle' });
      await card.evaluate(() => document.fonts.ready);
      const fontsOk = await card.evaluate(() => document.fonts.check('600 37px Newsreader') && document.fonts.check('600 15px "Public Sans"'));
      const overflow = await card.evaluate(() => {
        const t = document.querySelector('.text');
        return t.scrollHeight > t.clientHeight + 1 || t.scrollWidth > t.clientWidth + 1 || document.documentElement.scrollWidth > 800 || document.querySelector('.pic').scrollHeight > 420;
      });
      const file = path.join(OUT, p.out);
      await card.screenshot({ path: file, clip: { x: 0, y: 0, width: W / SCALE, height: H / SCALE } });
      await card.close();
      const bytes = fs.statSync(file).size;
      const problems = [];
      if (!fontsOk) problems.push('site fonts did not load');
      if (overflow) problems.push('text overflows the card');
      if (bytes > MAX_BYTES) problems.push('over 300 KB');
      if (problems.length) failed = true;
      console.log(`${p.out}  ${W}x${H}  ${(bytes / 1024).toFixed(1)} KB  "${title}"${info.chartHeading ? '  chart: ' + info.chartHeading : ''}${problems.length ? '  PROBLEM: ' + problems.join(', ') : ''}`);
    }
  } finally {
    await browser.close();
    server.close();
  }
  if (failed) process.exit(1);
})().catch(e => { console.error(e.message || e); process.exit(1); });
