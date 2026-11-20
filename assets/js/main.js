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
  $$('[data-tab="partner"]').forEach(a => { if (a.getAttribute('href') === 'contact.html') a.setAttribute('href', 'contact.html#partner'); });

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

// ---------- Free career check (12 questions, scored across 8 career areas) ----------
(function () {
  const quiz = document.getElementById('quiz'); if (!quiz) return;
  const AREAS = {
    tech: { name: 'Technology & engineering', careers: 'Software engineer, data scientist, AI engineer, electronics or mechanical engineer' },
    health: { name: 'Medicine & healthcare', careers: 'Doctor, dentist, physiotherapist, pharmacist, nurse, clinical psychologist' },
    business: { name: 'Business, finance & management', careers: 'Entrepreneur, chartered accountant, marketing manager, financial analyst' },
    design: { name: 'Design & creative arts', careers: 'Product or UX designer, fashion designer, architect, animator' },
    law: { name: 'Law & justice', careers: 'Lawyer, corporate counsel, judicial services, legal analyst' },
    media: { name: 'Media & communication', careers: 'Journalist, content creator, advertising and PR, filmmaker' },
    science: { name: 'Science & research', careers: 'Scientist, researcher, lab analyst, professor' },
    society: { name: 'Society & public service', careers: 'Civil services (UPSC), policy analyst, social worker, counsellor' }
  };
  const ANY = ['pcm', 'pcb', 'com', 'hum'];
  const C = (name, why, exams, years, streams) => ({ name, why, exams, years, streams });
  const COURSES = {
    tech: [C('B.Tech / B.E. (CSE, AI, Electronics, Mechanical)', 'Build software, machines and systems.', ['JEE Main', 'JEE Advanced', 'University tests'], 4, ['pcm']),
           C('BCA or B.Sc Computer Science', 'Programming and IT, with a quicker route into tech jobs.', ['CUET', 'University tests'], 3, ['pcm', 'com', 'hum']),
           C('B.Tech Biotechnology or B.Sc Bioinformatics', 'Where biology meets computing.', ['JEE Main', 'CUET'], 4, ['pcb'])],
    health: [C('MBBS, BDS or BAMS', 'Become a doctor or dentist.', ['NEET UG'], 5.5, ['pcb']),
             C('B.Sc Nursing, Physiotherapy (BPT) or Allied Health', 'Hands-on healthcare careers with steady demand.', ['NEET UG', 'CUET', 'University tests'], 4, ['pcb']),
             C('B.Pharm', 'Medicines and the pharma industry.', ['University tests', 'CUET'], 4, ['pcm', 'pcb']),
             C('BA or B.Sc Psychology', 'Mental health, behaviour and counselling.', ['CUET'], 3, ANY)],
    business: [C('BBA', 'Management, marketing and entrepreneurship.', ['CUET', 'University tests'], 3, ANY),
               C('B.Com (Hons)', 'Accounting, finance and commerce.', ['CUET'], 3, ['com', 'pcm', 'hum']),
               C('Integrated MBA (IPM)', 'Five-year management programme straight after Class 12.', ['IPMAT', 'JIPMAT'], 5, ANY),
               C('CA, CS or CMA', 'Professional finance and corporate law careers.', ['CA Foundation', 'CSEET'], 4, ['com'])],
    design: [C('B.Des (Product, Fashion, Communication, UX)', 'Design products, brands, fashion and digital experiences.', ['NID DAT', 'NIFT', 'UCEED'], 4, ANY),
             C('B.Arch', 'Design buildings and spaces.', ['NATA', 'JEE Main Paper 2'], 5, ['pcm']),
             C('BFA or Animation', 'Fine arts, illustration and animation.', ['University tests'], 4, ANY)],
    law: [C('BA LLB or BBA LLB', 'Five-year integrated law degree.', ['CLAT', 'AILET', 'University tests'], 5, ANY)],
    media: [C('BJMC or BA Mass Communication', 'Journalism, content, advertising and PR.', ['CUET', 'University tests'], 3, ANY),
            C('BA English or Film and Media Studies', 'Writing, storytelling and digital media.', ['CUET'], 3, ANY)],
    science: [C('B.Sc or BS-MS in Physics, Chemistry or Maths', 'Research and higher studies in the core sciences.', ['CUET', 'IISER Aptitude Test'], 4, ['pcm']),
              C('B.Sc or BS-MS in Biology or Biotechnology', 'Life sciences, labs and research.', ['CUET', 'IISER Aptitude Test'], 4, ['pcb']),
              C('BA or B.Sc Economics', 'Data, policy and how economies work.', ['CUET'], 3, ['com', 'hum', 'pcm'])],
    society: [C('BA in Political Science, History or Sociology', 'A strong base for civil services and policy.', ['CUET'], 3, ANY),
              C('Bachelor of Social Work (BSW)', 'Work with communities and NGOs.', ['CUET', 'University tests'], 3, ANY)]
  };
  const STEPS = [
    { id: 'cls', q: 'Which class are you in?', type: 'one', opts: [['10', 'Class 10'], ['11', 'Class 11'], ['12', 'Class 12'], ['p12', 'Passed Class 12']] },
    { id: 'stream', q: 'Which stream have you taken, or are planning to take?', type: 'one', opts: [['pcm', 'Science (PCM)'], ['pcb', 'Science (PCB)'], ['pcmb', 'Science (PCMB)'], ['com', 'Commerce'], ['hum', 'Humanities'], ['none', 'Not decided yet']] },
    { id: 'subj', q: 'Which subjects do you enjoy most?', hint: 'Pick up to three.', type: 'many', max: 3, opts: [['maths', 'Maths'], ['phy', 'Physics'], ['chem', 'Chemistry'], ['bio', 'Biology'], ['cs', 'Computer Science'], ['acc', 'Accounts or Business Studies'], ['eco', 'Economics'], ['eng', 'English or languages'], ['hist', 'History or Political Science'], ['psy', 'Psychology or Sociology'], ['art', 'Art or design']] },
    { id: 'p1', q: 'Which sounds more like you?', type: 'one', pair: true, opts: [['tech', 'Building an app, a robot or a machine'], ['health', 'Helping people get healthy again']] },
    { id: 'p2', q: 'Which sounds more like you?', type: 'one', pair: true, opts: [['business', 'Running my own business one day'], ['design', 'Designing how things look and feel']] },
    { id: 'p3', q: 'Which sounds more like you?', type: 'one', pair: true, opts: [['law', 'Arguing a case and winning a debate'], ['media', 'Telling stories through video or writing']] },
    { id: 'p4', q: 'Which sounds more like you?', type: 'one', pair: true, opts: [['science', 'Running experiments to find out why'], ['society', 'Working to change society for the better']] },
    { id: 'p5', q: 'Which sounds more like you?', type: 'one', pair: true, opts: [['lead', 'Leading a team and making decisions'], ['mind', 'Understanding how the body or mind works']] },
    { id: 'prio', q: 'What matters most to you in a career?', hint: 'Pick up to two.', type: 'many', max: 2, opts: [['money', 'A high income'], ['secure', 'Job security'], ['create', 'Creativity and freedom'], ['help', 'Helping people'], ['abroad', 'Working abroad someday'], ['boss', 'Being my own boss']] },
    { id: 'years', q: 'How many years would you like to study after Class 12?', type: 'one', opts: [['3', 'About 3 years'], ['4', 'About 4 years'], ['5', '5 years or more is fine'], ['ns', 'Not sure yet']] },
    { id: 'budget', q: 'What is your family\'s budget for the full course fees?', type: 'one', opts: [['lt3', 'Under ₹3 lakh'], ['3to8', '₹3–8 lakh'], ['8to15', '₹8–15 lakh'], ['gt15', 'Above ₹15 lakh'], ['ns', 'Not sure yet']] },
    { id: 'where', q: 'Where would you like to study?', type: 'one', opts: [['near', 'Close to home (Uttarakhand, UP or nearby)'], ['india', 'Anywhere in India'], ['abroad', 'Abroad, if possible']] }
  ];
  const SUBJ = { maths: { tech: 2, business: 1, science: 1 }, phy: { tech: 2, science: 1 }, chem: { science: 2, health: 1 }, bio: { health: 2, science: 1 }, cs: { tech: 3 }, acc: { business: 3 }, eco: { business: 2, society: 1 }, eng: { media: 2, law: 1 }, hist: { society: 2, law: 2 }, psy: { society: 2, health: 1 }, art: { design: 3, media: 1 } };
  const STREAMB = { pcm: { tech: 1, science: 1 }, pcb: { health: 1, science: 1 }, pcmb: { tech: .5, health: .5, science: 1 }, com: { business: 1.5 }, hum: { society: 1, law: 1, media: 1 } };
  const PAIR = { tech: { tech: 3 }, health: { health: 3 }, business: { business: 3 }, design: { design: 3 }, law: { law: 3 }, media: { media: 3 }, science: { science: 3 }, society: { society: 3 }, lead: { business: 1.5, law: 1, society: 1 }, mind: { health: 1.5, science: 1.5 } };
  const PRIO = { money: { tech: .7, business: .7, health: .5 }, secure: { health: .7, society: .7 }, create: { design: 1.2, media: 1.2 }, help: { health: 1.2, society: 1.2 }, abroad: { tech: .6, science: .6 }, boss: { business: 1.2, design: .5 } };
  const STREAM_NAME = { pcm: 'Science (PCM)', pcb: 'Science (PCB)', pcmb: 'Science (PCMB)', com: 'Commerce', hum: 'Humanities', none: 'an undecided stream' };
  const SUGGEST_STREAM = { tech: 'Science (PCM)', health: 'Science (PCB)', business: 'Commerce', design: 'any stream (PCM if you want Architecture)', law: 'any stream (Humanities is a popular choice)', media: 'any stream (Humanities is a popular choice)', science: 'Science (PCM or PCB)', society: 'Humanities' };

  const ans = {}; let i = 0;
  quiz.innerHTML = `<div class="quiz-top"><span class="q-count"></span><div class="quiz-progress" aria-hidden="true"><span></span></div></div><div class="q-stage" aria-live="polite"></div>
    <div class="quiz-nav"><button type="button" class="btn btn-outline" data-back>Back</button><button type="button" class="btn" data-next>Next</button></div>`;
  const stage = quiz.querySelector('.q-stage'), next = quiz.querySelector('[data-next]'), back = quiz.querySelector('[data-back]'), bar = quiz.querySelector('.quiz-progress span'), count = quiz.querySelector('.q-count');

  function render() {
    const s = STEPS[i], val = ans[s.id] || (s.type === 'many' ? [] : null);
    count.textContent = `Question ${i + 1} of ${STEPS.length}`;
    bar.style.width = ((i + 1) / STEPS.length * 100) + '%';
    const type = s.type === 'many' ? 'checkbox' : 'radio';
    stage.innerHTML = `<fieldset class="q${s.pair ? ' q-pair' : ''}"><legend>${s.q}${s.hint ? `<span class="q-hint">${s.hint}</span>` : ''}</legend><div class="opts${s.pair ? ' opts-pair' : ''}${s.opts.length > 6 ? ' opts-3' : ''}">` +
      s.opts.map(([v, l]) => `<label><input type="${type}" name="${s.id}" value="${v}" ${(s.type === 'many' ? val.includes(v) : val === v) ? 'checked' : ''}><span>${l}</span></label>`).join('') + '</div></fieldset>';
    back.hidden = i === 0; next.textContent = i === STEPS.length - 1 ? 'See my results' : 'Next';
    sync();
  }
  function sync() {
    const s = STEPS[i];
    if (s.type === 'many') {
      const picked = [...stage.querySelectorAll('input:checked')].map(x => x.value); ans[s.id] = picked;
      stage.querySelectorAll('input:not(:checked)').forEach(x => x.disabled = picked.length >= s.max);
      next.disabled = picked.length === 0;
    } else { const c = stage.querySelector('input:checked'); ans[s.id] = c ? c.value : null; next.disabled = !c; }
  }
  stage.addEventListener('change', e => { sync(); if (STEPS[i].type === 'one' && i < STEPS.length - 1) setTimeout(() => { i++; render(); }, 240); });
  back.addEventListener('click', () => { if (i > 0) { i--; render(); } });
  next.addEventListener('click', () => { if (next.disabled) return; if (i < STEPS.length - 1) { i++; render(); } else finish(); });

  function add(score, map, w = 1) { for (const k in map) score[k] += map[k] * w; }
  function finish() {
    const score = Object.fromEntries(Object.keys(AREAS).map(k => [k, 0]));
    (ans.subj || []).forEach(s => add(score, SUBJ[s]));
    if (STREAMB[ans.stream]) add(score, STREAMB[ans.stream]);
    ['p1', 'p2', 'p3', 'p4', 'p5'].forEach(p => ans[p] && add(score, PAIR[ans[p]]));
    (ans.prio || []).forEach(p => add(score, PRIO[p]));
    const ranked = Object.keys(score).sort((a, b) => score[b] - score[a]).slice(0, 3);
    const top = score[ranked[0]] || 1;
    const streams = ans.stream === 'pcmb' ? ['pcm', 'pcb'] : ans.stream === 'none' ? ANY : [ans.stream];
    const label = v => v / top > .85 ? 'Strong match' : v / top > .6 ? 'Good match' : 'Worth exploring';
    const cards = ranked.map((k, n) => {
      const list = COURSES[k].filter(c => c.streams.some(s => streams.includes(s)));
      const courses = list.length ? list.map(c => `<li><strong>${c.name}</strong><span>${c.why} About ${c.years} years.</span><div class="exams">${c.exams.map(x => `<span>${x}</span>`).join('')}</div></li>`).join('')
        : `<li><strong>Needs a different stream</strong><span>Most courses here need ${SUGGEST_STREAM[k]}. A counsellor can show you the routes that are still open.</span></li>`;
      return `<article class="area"><div class="area-head"><span class="area-rank">${n + 1}</span><div><h3>${AREAS[k].name}</h3><p class="area-careers">${AREAS[k].careers}</p></div><span class="area-tag t${n}">${label(score[k])}</span></div>
        <div class="area-bar"><span style="--w:${Math.max(18, Math.round(score[k] / top * 100))}%"></span></div><ul class="area-courses">${courses}</ul></article>`;
    }).join('');
    const tips = [];
    if (ans.cls === '10') tips.push(`You are choosing your stream now — the most important step. Your answers point towards <strong>${SUGGEST_STREAM[ranked[0]]}</strong>.`);
    if (ans.cls === 'p12') tips.push('Some 2027 entrance registrations may already be closed. Check the <a href="exam-calendar.html">exam calendar</a> and ask us about direct-admission options.');
    if (ans.budget === 'lt3') tips.push('Aim for government and central universities through JEE, NEET and CUET — their fees are far lower. Merit scholarships at private universities can help too.');
    if (ans.budget === '3to8') tips.push('Many good private universities fall in this range, and scholarships based on Class 12 marks or entrance scores can lower fees further.');
    if (ans.budget === '8to15' || ans.budget === 'gt15') tips.push('You have wide options. Compare placements, faculty and recognition — not just the brand.');
    if (ans.where === 'near') tips.push('Uttarakhand and nearby states have strong options. See our <a href="network.html#universities">29 partner universities</a>.');
    if (ans.where === 'abroad' || (ans.prio || []).includes('abroad')) tips.push('If you want to study or work abroad later, plan early for English tests like IELTS or TOEFL and build a strong profile from Class 11.');
    if (ans.years === '3' && ranked.some(k => ['health', 'law'].includes(k))) tips.push('Some courses in your results take 4–5 years or more. A counsellor can show you shorter routes into the same field.');
    if ((ans.prio || []).includes('secure')) tips.push('Government jobs through UPSC, state PSCs, SSC and banking are open to graduates of any stream.');
    tips.push('Use the <a href="free-guide.html">free Class 12 Decision Guide</a> to shortlist universities with a checklist.');
    stage.innerHTML = `<div class="result"><p class="res-k">Your results</p><h2>Your best-fit career areas</h2>
      <p class="muted">Based on your answers as a ${ans.cls === 'p12' ? 'student who has passed Class 12' : 'Class ' + ans.cls + ' student'} in ${STREAM_NAME[ans.stream]}.</p>
      <div class="areas">${cards}</div>
      <div class="tips"><h3>Tips for you</h3><ul>${tips.map(t => `<li>${t}</li>`).join('')}</ul></div>
      <div class="result-cta"><p><strong>This is a starting point, not a final answer.</strong> A counsellor will look at your marks, strengths and budget and build your actual plan.</p>
      <div class="hero-actions"><a href="contact.html" class="btn btn-cyan btn-lg">Get my plan — book free counselling</a><button type="button" class="btn btn-outline" data-restart>Start again</button></div>
      </div></div>`;
    quiz.querySelector('.quiz-nav').hidden = true; quiz.querySelector('.quiz-top').hidden = true;
    stage.querySelector('[data-restart]').addEventListener('click', () => { for (const k in ans) delete ans[k]; i = 0; quiz.querySelector('.quiz-nav').hidden = false; quiz.querySelector('.quiz-top').hidden = false; render(); quiz.scrollIntoView({ behavior: 'smooth' }); });
    requestAnimationFrame(() => stage.querySelectorAll('.area-bar span').forEach(s => s.classList.add('go')));
    const formClass = { '11': 'Class 11', '12': 'Class 12' }[ans.cls] || '';
    const formStream = { pcm: 'Science (PCM)', pcmb: 'Science (PCM)', pcb: 'Science (PCB)', com: 'Commerce', hum: 'Humanities' }[ans.stream] || '';
    try { sessionStorage.setItem('mum-check', JSON.stringify({ cls: formClass, stream: formStream })); } catch (e) {}
    quiz.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  render();
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
