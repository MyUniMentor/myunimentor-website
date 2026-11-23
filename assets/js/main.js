// MyUniMentor — dependency-free interactions
(function () {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Header shadow + scroll progress
  const header = document.querySelector('.site-header');
  const bar = document.querySelector('.progress');
  const onScroll = () => {
    const h = document.documentElement;
    if (bar) bar.style.setProperty('--p', (h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight)).toFixed(4));
    if (header) header.classList.toggle('scrolled', h.scrollTop > 10);
  };
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // Mobile nav
  const toggle = document.querySelector('.nav-toggle'), nav = document.getElementById('nav');
  if (toggle && nav) toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open); toggle.textContent = open ? 'Close' : 'Menu';
  });

  // Dropdowns
  const subs = $$('.has-sub');
  const desktop = () => matchMedia('(min-width: 961px)').matches;
  const closeAll = except => subs.forEach(li => { if (li !== except) { li.classList.remove('open'); li.querySelector('.sub-toggle').setAttribute('aria-expanded', 'false'); } });
  subs.forEach(li => {
    const btn = li.querySelector('.sub-toggle');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = !li.classList.contains('open'); closeAll(li); li.classList.toggle('open', o); btn.setAttribute('aria-expanded', o); });
    li.addEventListener('mouseenter', () => { if (desktop()) { closeAll(li); li.classList.add('open'); btn.setAttribute('aria-expanded', 'true'); } });
    li.addEventListener('mouseleave', () => { if (desktop()) { li.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); } });
  });
  document.addEventListener('click', () => closeAll());
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });

  // Hero roadmap ticks itself off
  const steps = $$('.roadmap li');
  if (steps.length) {
    const plan = [[0, 'done', 1300], [1, 'done', 1900], [2, 'active', 2500]];
    plan.forEach(([i, cls, t]) => reduce ? steps[i].classList.add(cls) : setTimeout(() => steps[i].classList.add(cls), t));
  }

  // Count-up numbers
  const fmt = n => n.toLocaleString('en-IN');
  function countUp(el) {
    const end = +el.dataset.count, suf = el.dataset.suffix || '', dur = 1400, t0 = performance.now();
    const tick = t => { const p = Math.min(1, (t - t0) / dur), v = Math.round(end * (1 - Math.pow(1 - p, 3))); el.textContent = fmt(v) + suf; if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  }

  // Reveal on scroll
  const io = 'IntersectionObserver' in window ? new IntersectionObserver(entries => entries.forEach(en => {
    if (!en.isIntersecting) return;
    en.target.classList.add('in');
    if (!reduce) $$('[data-count]', en.target).concat(en.target.matches('[data-count]') ? [en.target] : []).forEach(countUp);
    io.unobserve(en.target);
  }), { threshold: .15, rootMargin: '0px 0px -40px 0px' }) : null;
  $$('[data-reveal]').forEach(el => io ? io.observe(el) : el.classList.add('in'));
  $$('.float [data-count]').forEach(el => { if (!reduce) setTimeout(() => countUp(el), 600); });

  // Cursor spotlight on cards
  $$('.spot').forEach(card => card.addEventListener('pointermove', e => {
    const r = card.getBoundingClientRect();
    card.style.setProperty('--mx', (e.clientX - r.left) + 'px'); card.style.setProperty('--my', (e.clientY - r.top) + 'px');
  }));

  // Tabs
  function select(tab) {
    const list = tab.closest('[role="tablist"]');
    $$('[role="tab"]', list).forEach(t => {
      const on = t === tab; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1;
      const p = document.getElementById(t.getAttribute('aria-controls')); if (p) p.hidden = !on;
    });
  }
  $$('[role="tablist"]').forEach(list => {
    const tabs = $$('[role="tab"]', list);
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', e => {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        const n = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length]; select(n); n.focus();
      });
    });
  });
  if (location.hash === '#partner') { const t = document.getElementById('t-f2'); if (t) select(t); }
  $$('[data-tab="partner"]').forEach(a => { const h = a.getAttribute('href'); if (h === 'contact.html' || h === '/contact') a.setAttribute('href', h + '#partner'); });

  // Lead forms — connected to email, Google Sheet and WhatsApp alerts at launch
  $$('.lead-form').forEach(form => form.addEventListener('submit', e => {
    e.preventDefault();
    if (!form.checkValidity()) { form.reportValidity(); return; }
    const msg = { counselling: 'Thanks — your session request has been received. Our team will call you back.',
      partnership: 'Thanks — your enquiry has been received. Our team will get in touch.',
      testimonial: 'Thank you for sharing your story. We will contact you before publishing anything.',
      guide: 'Thanks! Your guide is ready.' };
    const data = new URLSearchParams(new FormData(form));
    data.append('form', form.dataset.form || 'enquiry'); data.append('page', location.pathname);
    const btn = form.querySelector('button[type=submit]'); if (btn) btn.disabled = true;
    const done = () => { form.querySelector('.form-status').textContent = msg[form.dataset.form] || msg.partnership; if (btn) btn.disabled = false; if (form.dataset.form !== 'guide') form.reset(); };
    if (window.MUM_FORM_URL) fetch(window.MUM_FORM_URL, { method: 'POST', mode: 'no-cors', body: data }).then(done, done); else done();
  }));

  // Filters + typo-tolerant search (schools and universities)
  const lev = (a, b) => { const m = a.length, n = b.length; let p = Array.from({ length: n + 1 }, (_, j) => j);
    for (let i = 1; i <= m; i++) { const c = [i]; for (let j = 1; j <= n; j++) c[j] = Math.min(p[j] + 1, c[j - 1] + 1, p[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); p = c; } return p[n]; };
  const norm = t => t.toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  const tokMatch = (q, words, hay) => {
    if (hay.includes(q)) return true;
    const tol = q.length >= 5 ? 2 : q.length >= 3 ? 1 : 0;
    return words.some(w => lev(q, w.slice(0, q.length)) <= tol || lev(q, w) <= tol);
  };
  const matches = (q, hay) => { if (!q) return true; const words = hay.split(' '); return q.split(' ').every(t => tokMatch(t, words, hay)); };
  function apply(section) {
    const grid = section.querySelector('.org-grid'), key = grid.dataset.filterTarget, active = grid.dataset.active || 'all';
    const q = norm(((section.querySelector('input[type=search]') || {}).value || ''));
    let shown = 0;
    $$('.org-card', grid).forEach(c => { const ok = (active === 'all' || c.dataset[key] === active) && matches(q, norm(c.dataset.search || '')); c.hidden = !ok; if (ok) { shown++; c.classList.add('in'); } });
    const empty = section.querySelector('.empty'); if (empty) empty.hidden = shown > 0;
  }
  $$('.filters').forEach(g => { if (!g.closest('.section').querySelector('.org-grid')) return; g.addEventListener('click', e => {
    const b = e.target.closest('.fbtn'); if (!b) return;
    $$('.fbtn', g).forEach(x => x.setAttribute('aria-pressed', x === b));
    const s = g.closest('.section'); s.querySelector('.org-grid').dataset.active = b.dataset.filter; apply(s);
  }); });
  $$('.org-search').forEach(inp => inp.addEventListener('input', () => apply(inp.closest('.section'))));

  // Viewer — Instagram loads only when someone taps play
  const viewer = document.getElementById('viewer'), body = viewer && viewer.querySelector('.viewer-body');
  const open = html => { body.innerHTML = html; viewer.showModal(); };
  if (viewer) {
    viewer.querySelector('.viewer-close').addEventListener('click', () => viewer.close());
    viewer.addEventListener('close', () => { body.innerHTML = ''; });
    viewer.addEventListener('click', e => { if (e.target === viewer) viewer.close(); });
  }
  $$('.reel, .reel-feature').forEach(btn => btn.addEventListener('click', () => {
    const url = btn.dataset.reel; if (!url) return;
    viewer.classList.remove('wide');
    open(`<blockquote class="instagram-media" data-instgrm-permalink="${url}" data-instgrm-version="14" style="width:100%;margin:0;min-height:420px"></blockquote><a class="ig-fallback" href="${url}" target="_blank" rel="noopener">Watch on Instagram</a>`);
    if (window.instgrm) window.instgrm.Embeds.process();
    else { const sc = document.createElement('script'); sc.src = 'https://www.instagram.com/embed.js'; sc.async = true; document.body.appendChild(sc); }
  }));
  $$('.photo').forEach(btn => btn.addEventListener('click', () => {
    const src = btn.dataset.src; if (!src) return;
    viewer.classList.add('wide', 'photo-view');
    open(`<img src="${src}" alt="${btn.dataset.cap || ''}" draggable="false"><p class="ph-cap">${btn.dataset.cap || ''}</p>`);
  }));
  if (viewer) viewer.addEventListener('close', () => viewer.classList.remove('photo-view'));
  // Light deterrent against casual saving (screenshots can't be blocked; the watermark is the real protection)
  document.addEventListener('contextmenu', ev => { if (ev.target.closest('.photo, .viewer img, .delegates-fig')) ev.preventDefault(); });
  document.addEventListener('dragstart', ev => { if (ev.target.closest('.photo, .viewer')) ev.preventDefault(); });
  $$('.lor').forEach(btn => btn.addEventListener('click', () => {
    const src = btn.dataset.src; if (!src) return;
    viewer.classList.add('wide');
    open(`<img src="${src}" alt="Letter of recommendation">`);
  }));
})();

// Prefill the counselling form from the career check
(function () {
  let d; try { d = JSON.parse(sessionStorage.getItem('mum-check') || 'null'); } catch (e) {}
  if (!d) return;
  const c = document.getElementById('s-class'), s = document.getElementById('s-stream');
  if (c && d.cls) c.value = d.cls;
  if (s && d.stream) s.value = d.stream;
})();

// ---------- Exam calendar: countdowns, next-up, stream filter ----------
(function () {
  const items = [...document.querySelectorAll('.ex')]; if (!items.length) return;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  let nextSet = false;
  items.forEach(li => {
    const d = new Date(li.dataset.date + 'T00:00:00'), days = Math.round((d - today) / 864e5);
    const c = li.querySelector('.ex-count'), exp = li.classList.contains('expected');
    if (days < 0) { li.classList.add('past'); c.textContent = 'Done'; }
    else if (days === 0) c.textContent = 'Today';
    else c.textContent = (exp ? 'about ' : '') + days + (days === 1 ? ' day to go' : ' days to go');
    if (days >= 0 && !nextSet) { li.classList.add('next-up'); nextSet = true; }
  });
  const g = document.querySelector('.cal-tools .filters');
  if (g) g.addEventListener('click', e => {
    const b = e.target.closest('.fbtn'); if (!b) return; e.stopPropagation();
    g.querySelectorAll('.fbtn').forEach(x => x.setAttribute('aria-pressed', x === b));
    let n = 0;
    items.forEach(li => { li.hidden = !(b.dataset.stream === 'all' || li.dataset.streams.split(' ').includes(b.dataset.stream)); if (!li.hidden) { li.classList.add('in'); n++; } });
    const cnt = document.querySelector('.cal-count');
    if (cnt) cnt.textContent = b.dataset.stream === 'all' ? '' : `Showing ${n} exam${n === 1 ? '' : 's'} open to ${b.textContent.trim()} students.`;
  }, true);
})();

// ---------- Free guide: reveal the download after the form ----------
(function () {
  const f = document.querySelector('.guide-form'); if (!f) return;
  f.addEventListener('submit', () => setTimeout(() => {
    if (!f.querySelector('.form-status').textContent) return;
    f.querySelector('.form-status').textContent = 'Thanks! Your guide is ready.';
    f.querySelector('.guide-dl').hidden = false;
    f.querySelector('button[type=submit]').hidden = true;
  }, 0));
})();

// ---------- Scroll journey: the path is drawn through every dot, then fills as you scroll ----------
(function () {
  const track = document.querySelector('.j-track'); if (!track) return;
  const svg = track.querySelector('.j-path'), bg = svg.querySelector('.j-bg'), fg = svg.querySelector('.j-fg');
  const stops = [...track.querySelectorAll('.j-stop')], reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let marks = [], ticking = false;
  function layout() {
    const t = track.getBoundingClientRect(), W = t.width, H = t.height;
    const pts = stops.map(s => { const d = s.querySelector('.j-dot').getBoundingClientRect(); return [d.left + d.width / 2 - t.left, d.top + d.height / 2 - t.top]; });
    if (!pts.length) return;
    const amp = Math.min(70, W * .06), all = [[pts[0][0], 0], ...pts, [pts[pts.length - 1][0], H]];
    let d = `M${all[0][0]} ${all[0][1]}`;
    for (let i = 1; i < all.length; i++) {
      const [x0, y0] = all[i - 1], [x1, y1] = all[i], dy = (y1 - y0) / 2, s = i % 2 ? amp : -amp;
      d += ` C${x0 + s} ${y0 + dy * .9}, ${x1 + s} ${y1 - dy * .9}, ${x1} ${y1}`;
    }
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`); bg.setAttribute('d', d); fg.setAttribute('d', d);
    // where each dot sits along the path = length of the curve up to that dot
    const tmp = document.createElementNS('http://www.w3.org/2000/svg', 'path'); svg.appendChild(tmp);
    const segs = d.split(' C'), L = fg.getTotalLength();
    marks = pts.map((_, i) => { tmp.setAttribute('d', segs.slice(0, i + 2).join(' C')); return tmp.getTotalLength() / L; });
    tmp.remove();
    update();
  }
  function update() {
    ticking = false;
    const r = track.getBoundingClientRect();
    const p = reduce ? 1 : Math.max(0, Math.min(1, (innerHeight * .6 - r.top) / r.height));
    fg.style.strokeDashoffset = (1 - p).toFixed(4);
    stops.forEach((s, i) => s.classList.toggle('on', p >= (marks[i] ?? 1) - .005));
  }
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  let lw = 0; new ResizeObserver(() => { if (track.offsetWidth !== lw || !marks.length) { lw = track.offsetWidth; layout(); } }).observe(track);
})();

// ---------- Letters of recommendation: swipe left/right, pick a school ----------
(function () {
  document.querySelectorAll('.lor-carousel').forEach(c => {
    const track = c.querySelector('.lc-track'), tabs = [...c.querySelectorAll('.lc-tab')], slides = [...track.children];
    const go = i => { i = Math.max(0, Math.min(slides.length - 1, i)); track.scrollTo({ left: slides[i].offsetLeft - track.offsetLeft, behavior: 'smooth' }); set(i); };
    const bar = c.querySelector('.lc-tabs');
    const set = i => tabs.forEach((t, j) => { t.classList.toggle('on', j === i); t.setAttribute('aria-selected', j === i); if (j === i && bar) bar.scrollTo({ left: t.offsetLeft - bar.offsetLeft - 8, behavior: 'smooth' }); });
    const cur = () => Math.round(track.scrollLeft / track.clientWidth);
    tabs.forEach((t, i) => t.addEventListener('click', () => go(i)));
    c.querySelector('.lc-prev')?.addEventListener('click', () => go(cur() - 1));
    c.querySelector('.lc-next')?.addEventListener('click', () => go(cur() + 1));
    let to; track.addEventListener('scroll', () => { clearTimeout(to); to = setTimeout(() => set(cur()), 80); }, { passive: true });
    if (slides.length > 1) autoplay(track, () => go(cur() >= slides.length - 1 ? 0 : cur() + 1), 5000);
  });
})();

// ---------- Hero: cross-fading photos from the Summit ----------
(function () {
  const f = document.querySelector('.hero-slides'); if (!f) return;
  const imgs = [...f.querySelectorAll('img')], dots = [...f.querySelectorAll('.hs-dot')], cap = f.querySelector('.hs-cap');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let i = 0, t;
  const load = () => imgs.forEach(im => { if (im.dataset.src) { im.src = im.dataset.src; im.removeAttribute('data-src'); } });
  const show = n => {
    i = (n + imgs.length) % imgs.length;
    imgs.forEach((im, j) => im.classList.toggle('on', j === i));
    dots.forEach((d, j) => d.classList.toggle('on', j === i));
    if (cap) cap.textContent = imgs[i].dataset.cap || '';
  };
  const play = () => { if (reduce) return; clearInterval(t); t = setInterval(() => show(i + 1), 4500); };
  dots.forEach((d, j) => d.addEventListener('click', () => { load(); show(j); play(); }));
  f.addEventListener('mouseenter', () => clearInterval(t)); f.addEventListener('mouseleave', play);
  addEventListener('load', () => setTimeout(() => { load(); play(); }, 1200));
})();

// ---------- Auto-advance helper: pauses on hover, touch, focus or when off-screen ----------
function autoplay(el, tick, ms = 3800) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  let paused = false, visible = false, resumeT;
  const pause = () => { paused = true; clearTimeout(resumeT); };
  const resume = (d = 2500) => { clearTimeout(resumeT); resumeT = setTimeout(() => paused = false, d); };
  const box = el.closest('.hs-wrap, .lor-carousel') || el;
  box.addEventListener('mouseenter', pause); box.addEventListener('mouseleave', () => resume(800));
  box.addEventListener('touchstart', pause, { passive: true }); box.addEventListener('touchend', () => resume(5000), { passive: true });
  box.addEventListener('focusin', pause); box.addEventListener('focusout', () => resume());
  box.addEventListener('click', () => { pause(); resume(6000); });
  new IntersectionObserver(es => es.forEach(x => visible = x.isIntersecting), { threshold: .35 }).observe(el);
  setInterval(() => { if (!paused && visible && !document.hidden) tick(); }, ms);
}

// ---------- Horizontal carousels: swipe or use arrows, both directions ----------
(function () {
  document.querySelectorAll('[data-hs]').forEach(t => {
    const wrap = document.createElement('div');
    wrap.className = 'hs-wrap ' + (t.dataset.hs === 'm' ? 'hs-m' : 'hs-a');
    t.parentNode.insertBefore(wrap, t);
    const nav = document.createElement('div'); nav.className = 'hs-nav';
    nav.innerHTML = '<button type="button" class="hs-prev" aria-label="Scroll left">‹</button><button type="button" class="hs-next" aria-label="Scroll right">›</button>';
    wrap.append(nav, t); t.classList.add('hs-track');
    const prev = nav.firstChild, next = nav.lastChild;
    const step = () => { const li = t.firstElementChild; return li ? li.getBoundingClientRect().width + 14 : 300; };
    const upd = () => { const max = t.scrollWidth - t.clientWidth; prev.disabled = t.scrollLeft < 4; next.disabled = t.scrollLeft > max - 4; nav.hidden = max < 4; };
    prev.addEventListener('click', () => t.scrollBy({ left: -step(), behavior: 'smooth' }));
    next.addEventListener('click', () => t.scrollBy({ left: step(), behavior: 'smooth' }));
    t.addEventListener('scroll', upd, { passive: true }); new ResizeObserver(upd).observe(t); upd();
    autoplay(t, () => {
      const max = t.scrollWidth - t.clientWidth; if (max < 4 || !t.offsetParent) return;
      t.scrollTo({ left: t.scrollLeft >= max - 4 ? 0 : t.scrollLeft + step(), behavior: 'smooth' });
    });
  });
})();

// ---------- Bulb cursor: soft glow that follows the mouse, burst + glow on click ----------
(function () {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const HOT = 'a, button, [role="button"], label, summary, select, .photo, .reel, .lor, .fbtn, .lc-tab';
  if (fine && !reduce) {
    const g = document.createElement('div'); g.className = 'cursor-glow'; g.setAttribute('aria-hidden', 'true'); document.body.appendChild(g);
    let x = -500, y = -500, cx = x, cy = y, raf = 0;
    const loop = () => { cx += (x - cx) * .18; cy += (y - cy) * .18; g.style.transform = `translate3d(${cx}px,${cy}px,0)`; raf = Math.abs(x - cx) + Math.abs(y - cy) > .5 ? requestAnimationFrame(loop) : 0; };
    addEventListener('pointermove', e => { if (e.pointerType !== 'mouse') return; x = e.clientX; y = e.clientY; g.classList.add('on'); g.classList.toggle('lit', !!e.target.closest(HOT)); if (!raf) raf = requestAnimationFrame(loop); }, { passive: true });
    document.addEventListener('mouseleave', () => g.classList.remove('on'));
  }
  if (reduce) return;
  addEventListener('pointerdown', e => {
    const b = document.createElement('span'); b.className = 'click-burst'; b.style.left = e.clientX + 'px'; b.style.top = e.clientY + 'px';
    document.body.appendChild(b); setTimeout(() => b.remove(), 650);
    const hit = e.target.closest('.btn, button, .fbtn, .lc-tab, .reel, .photo');
    if (hit) { hit.classList.remove('glow-hit'); void hit.offsetWidth; hit.classList.add('glow-hit'); setTimeout(() => hit.classList.remove('glow-hit'), 750); }
  }, { passive: true });
})();

/* footer wordmark: spotlight follows the cursor */
(function () {
  var m = document.querySelector('.foot-mark span'); if (!m) return;
  m.parentNode.addEventListener('pointermove', function (e) {
    var r = m.getBoundingClientRect();
    m.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    m.style.setProperty('--my', (e.clientY - r.top) + 'px');
  });
})();

/* Welcome tour: loaded only after the page has finished loading, and only when needed */
(function () {
  const me = document.querySelector('script[src*="main.min.js"]'); if (!me) return;
  const src = me.src.replace('main.min.js', 'tour.min.js');
  let asked = false;
  const load = () => { if (asked) return; asked = true; const s = document.createElement('script'); s.src = src; s.async = true; document.body.appendChild(s); };
  document.querySelectorAll('.tour-open').forEach(b => b.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); if (window.MUMTour) window.MUMTour.open(); else { window.__mumTourOpen = true; load(); } }));
  let seen = null; try { seen = localStorage.getItem('mum-tour'); } catch (e) { seen = 'x'; }
  if (seen || /(^|\/)(contact|career-check)(\.html)?$/.test(location.pathname.replace(/\/$/, ''))) return;
  const later = () => ('requestIdleCallback' in window ? requestIdleCallback(load, { timeout: 3000 }) : setTimeout(load, 1500));
  if (document.readyState === 'complete') later(); else addEventListener('load', later);
})();

/* Save for later: stored on this device; copied into the account when the student logs in */
(function () {
  const acc = document.querySelector('.nav-account'), art = document.querySelector('article.article'), hero = document.querySelector('.page-hero .wrap');
  if (!acc || !art || !hero) return;
  const slug = location.pathname.replace(/\/$/, '').split('/').pop().replace('.html', ''), title = (hero.querySelector('h1') || {}).textContent || document.title;
  const get = () => { try { return JSON.parse(localStorage.getItem('mum-saved') || '[]'); } catch (e) { return []; } };
  const b = document.createElement('button'); b.type = 'button'; b.className = 'save-btn';
  const paint = () => { const on = get().some(x => x.slug === slug); b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); b.innerHTML = on ? 'Saved <span>· see it in <a href="' + acc.getAttribute('href') + '">your account</a></span>' : 'Save for later'; };
  b.addEventListener('click', e => {
    if (e.target.closest('a')) return;
    let s = get(); s = s.some(x => x.slug === slug) ? s.filter(x => x.slug !== slug) : s.concat({ slug, title: title.trim(), url: location.pathname });
    try { localStorage.setItem('mum-saved', JSON.stringify(s.slice(-60))); } catch (x) {}
    paint();
  });
  paint(); hero.appendChild(b);
})();

/* Header: show "My account" once someone has logged in on this device */
(function () {
  const a = document.querySelector('.nav-account'); if (!a) return;
  try { if (localStorage.getItem('mum-acct')) a.textContent = 'My account'; } catch (e) {}
})();
