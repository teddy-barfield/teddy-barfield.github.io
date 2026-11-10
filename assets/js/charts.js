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
    return new Chart(canvas, {
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
  }

  window.NYCharts = {
    palette: PALETTE,
    negative: v('--neg', '#9B2C2C'),
    line: function (c, l, d, o) { return build('line', c, l, d, o); },
    bar:  function (c, l, d, o) { return build('bar', c, l, d, o); }
  };
})();
