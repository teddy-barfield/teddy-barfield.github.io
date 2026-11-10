// Shared Chart.js setup. Load Chart.js first, then this file.
// Usage:  NYCharts.line(canvas, labels, [{label:'A', data:[...]}], {yTitle:'Rate'})
//         NYCharts.bar(canvas, labels, datasets, {horizontal:true})
(function () {
  var css = getComputedStyle(document.documentElement);
  function v(name, fallback) { return (css.getPropertyValue(name) || '').trim() || fallback; }

  var PALETTE = ['--c1','--c2','--c3','--c4','--c5','--c6','--c7','--c8','--c9'].map(function (n, i) {
    return v(n, ['#376092','#C08A2B','#4C7A3D','#6A4C93','#2E86AB','#B0607A','#7A6A55','#3D9970','#8E8E3E'][i]);
  });

  if (!window.Chart) {
    // Chart.js failed to load (offline, blocked): show the text fallback instead of an empty box.
    document.querySelectorAll('.chart-box').forEach(function (box) {
      var p = document.createElement('p');
      p.className = 'chart-fallback';
      p.textContent = 'The chart could not be loaded. The numbers are in the table below it.';
      box.appendChild(p);
    });
    window.NYCharts = { palette: PALETTE, line: function () {}, bar: function () {} };
    return;
  }

  Chart.defaults.font.family = '"Public Sans", system-ui, sans-serif';
  Chart.defaults.font.size = 13;
  Chart.defaults.color = v('--muted', '#4D4D4D');
  Chart.defaults.borderColor = v('--rule', '#D9D9D9');
  Chart.defaults.maintainAspectRatio = false;   // height comes from .chart-box
  Chart.defaults.plugins.legend.position = 'bottom';
  Chart.defaults.plugins.legend.labels.boxWidth = 12;

  function color(i) { return PALETTE[i % PALETTE.length]; }

  function axisTitle(text) { return text ? { display: true, text: text } : { display: false }; }

  function build(type, canvas, labels, datasets, o) {
    o = o || {};
    var horizontal = !!o.horizontal;
    datasets = datasets.map(function (d, i) {
      var c = d.color || color(i);
      var out = Object.assign({ backgroundColor: c, borderColor: c }, d);
      if (type === 'line') { out.borderWidth = out.borderWidth || 2; out.pointRadius = out.pointRadius == null ? 2 : out.pointRadius; out.tension = out.tension || 0; }
      return out;
    });
    var chart = new Chart(canvas, {
      type: type,
      data: { labels: labels, datasets: datasets },
      options: {
        indexAxis: horizontal ? 'y' : 'x',
        interaction: { mode: type === 'line' ? 'index' : 'nearest', intersect: false },
        plugins: { legend: { display: o.legend != null ? o.legend : datasets.length > 1 } },
        scales: {
          x: { title: axisTitle(horizontal ? o.yTitle : o.xTitle), grid: { display: horizontal } },
          y: { title: axisTitle(horizontal ? o.xTitle : o.yTitle), beginAtZero: o.beginAtZero !== false, grid: { display: !horizontal } }
        }
      }
    });
    if (!canvas.hasAttribute('data-has-table')) attachTable(chart, canvas);
    return chart;
  }

  // Text alternative: a collapsed "Show chart data as a table" under any chart that has no table of its own.
  // Rebuilt whenever the chart is updated, so it always matches what is drawn.
  function attachTable(chart, canvas) {
    var box = canvas.closest('.chart-box') || canvas.parentNode;
    var det = document.createElement('details');
    det.className = 'chart-data';
    var sum = document.createElement('summary');
    sum.textContent = 'Show chart data as a table';
    var scroll = document.createElement('div');
    scroll.className = 'table-scroll chart-data-scroll';
    scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region');
    scroll.setAttribute('aria-label', 'Chart data table');
    det.appendChild(sum); det.appendChild(scroll);
    box.parentNode.insertBefore(det, box.nextSibling);
    function fmt(x) { return x == null || (typeof x === 'number' && isNaN(x)) ? '' : String(x); }
    function render() {
      var d = chart.data, t = document.createElement('table');
      t.className = 'data';
      var cap = document.createElement('caption');
      cap.textContent = canvas.getAttribute('aria-label') || 'Chart data';
      t.appendChild(cap);
      var tr = document.createElement('tr');
      ['Label'].concat(d.datasets.map(function (ds) { return ds.label; })).forEach(function (h, i) {
        var th = document.createElement('th'); th.scope = 'col'; th.textContent = h; if (i) th.className = 'num'; tr.appendChild(th);
      });
      var thead = document.createElement('thead'); thead.appendChild(tr); t.appendChild(thead);
      var tb = document.createElement('tbody');
      d.labels.forEach(function (lab, i) {
        var r = document.createElement('tr');
        var th = document.createElement('th'); th.scope = 'row'; th.textContent = lab; r.appendChild(th);
        d.datasets.forEach(function (ds) {
          var td = document.createElement('td'); td.className = 'num';
          var y = ds.data[i]; td.textContent = fmt(y && typeof y === 'object' ? y.y : y); r.appendChild(td);
        });
        tb.appendChild(r);
      });
      t.appendChild(tb);
      scroll.replaceChildren(t);
    }
    var upd = chart.update.bind(chart);
    chart.update = function (m) { var r = upd(m); if (det.open) render(); return r; };
    det.addEventListener('toggle', function () { if (det.open) render(); });
  }

  window.NYCharts = {
    palette: PALETTE,
    negative: v('--neg', '#9B2C2C'),
    line: function (c, l, d, o) { return build('line', c, l, d, o); },
    bar:  function (c, l, d, o) { return build('bar', c, l, d, o); }
  };
})();
