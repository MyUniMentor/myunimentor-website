/* Date sheet pages: tick subjects, download them as a calendar file (.ics). Times in the table are IST. */
(function () {
  var art = document.querySelector('.article'); if (!art) return;
  var boxes = art.querySelectorAll('.ds-pick'); if (!boxes.length) return;
  art.classList.add('ds-on');
  var tools = art.querySelectorAll('.ds-tool'), btns = art.querySelectorAll('.ds-ics');
  tools.forEach(function (t) { t.hidden = false; });
  var KEY = 'ds:' + location.pathname;
  try { (JSON.parse(localStorage.getItem(KEY)) || []).forEach(function (i) { if (boxes[i]) boxes[i].checked = true; }); } catch (e) {}
  function picked() { return Array.prototype.filter.call(boxes, function (b) { return b.checked; }); }
  function sync() {
    var n = picked().length;
    btns.forEach(function (b) { b.disabled = !n; b.textContent = n ? 'Add ' + n + (n === 1 ? ' paper' : ' papers') + ' to my calendar' : 'Tick your subjects first'; });
    try { localStorage.setItem(KEY, JSON.stringify(Array.prototype.map.call(boxes, function (b, i) { return b.checked ? i : -1; }).filter(function (i) { return i >= 0; }))); } catch (e) {}
  }
  function utc(d, hm, minus) { /* IST wall clock -> UTC stamp */
    var t = Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10), +hm.slice(0, 2), +hm.slice(2, 4)) - 330 * 60000 - (minus || 0);
    return new Date(t).toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z';
  }
  function esc(s) { return s.replace(/[\\,;]/g, '\\$&'); }
  function ics() {
    var now = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z', url = location.href.split('#')[0];
    var L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//MyUniMentor//Date sheet//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH'];
    picked().forEach(function (b, i) {
      var d = b.dataset.d, s = b.dataset.s, t = b.dataset.t;
      var day = Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10)) - 86400000, prev = new Date(day).toISOString().slice(0, 10);
      L.push('BEGIN:VEVENT', 'UID:' + d + '-' + s + '-' + i + '-' + t.replace(/\W+/g, '').slice(0, 40) + '@myunimentor.in', 'DTSTAMP:' + now,
        'DTSTART:' + utc(d, s), 'DTEND:' + utc(d, b.dataset.e), 'SUMMARY:' + esc(t + ' exam'),
        'DESCRIPTION:' + esc('Check your admit card and the board website for any change. Date sheet: ' + url), 'URL:' + url,
        'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + esc('Tomorrow: ' + t), 'TRIGGER;VALUE=DATE-TIME:' + utc(prev, '1900'), 'END:VALARM', 'END:VEVENT');
    });
    L.push('END:VCALENDAR');
    return L.join('\r\n');
  }
  art.addEventListener('change', function (ev) { if (ev.target.classList && ev.target.classList.contains('ds-pick')) sync(); });
  btns.forEach(function (b) {
    b.addEventListener('click', function () {
      if (!picked().length) return;
      var a = document.createElement('a'), blob = new Blob([ics()], { type: 'text/calendar;charset=utf-8' });
      a.href = URL.createObjectURL(blob); a.download = (location.pathname.split('/').pop().replace('.html', '') || 'date-sheet') + '.ics';
      document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    });
  });
  sync();
})();
