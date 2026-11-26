/* MyUniMentor admin panel (/admin). Only accounts in the ADMINS list (admin claim) can read anything; Firestore rules enforce it.
   Loaded only on /admin. Nothing is ever deleted outright: profiles, test reports, test unlocks and drafts go to the Bin first. */
if (window.top !== window.self) { try { window.top.location = location.href; } catch (e) {} document.documentElement.style.display = 'none'; }   // never inside someone else's frame (clickjacking)
const ROOT = document.getElementById('adm');
const CFG = window.MUM_ACCOUNT || {};
const FB_VER = '12.11.0';
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const $ = s => ROOT.querySelector(s), $$ = s => [...ROOT.querySelectorAll(s)];
const link = k => { const a = document.querySelector('.acct-links a[data-k="' + k + '"]'); return a ? a.getAttribute('href') : '#'; };
const STREAMS = { pcm: 'Science (PCM)', pcb: 'Science (PCB)', pcmb: 'Science (PCMB)', comm: 'Commerce with Maths', com: 'Commerce without Maths', hum: 'Humanities (Arts)', und: 'Not decided yet' };
const CLASSES = ['Class 9', 'Class 10', 'Class 11', 'Class 12', 'Gap year / dropper'];
const TARGETS = ['Engineering', 'Medicine', 'Design', 'Law', 'Management (BBA/IPM)', 'Commerce / CA', 'Science and research', 'Psychology', 'Media and journalism', 'Humanities', 'Hotel management', 'Defence', 'Not sure yet'];
const RSTAT = { requested: 'Requested', booked: 'Booked', done: 'Completed', cancelled: 'Cancelled' };
const STAGES = { new: 'New', contacted: 'Contacted', counselled: 'Counselled', joined: 'Joined', lost: 'Not interested' };
const KINDS = { account: 'Account', report: 'Test report', test: 'Test unlock', announcement: 'Announcement draft' };
const toDate = t => t && t.toDate ? t.toDate() : t && t.seconds ? new Date(t.seconds * 1000) : t ? new Date(t) : null;
const fmt = (t, time) => { const d = toDate(t); return d ? d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) + (time ? ', ' + d.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' }) : '') : '—'; };
const ago = t => { const d = toDate(t); return d ? (Date.now() - d) / 864e5 : 1e9; };
const ymd = (n = 0) => new Date(Date.now() + 5.5 * 36e5 + n * 864e5).toISOString().slice(0, 10);   // a day in India time, n days from today
const day = s => s ? new Date(s + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '';
const initials = n => String(n || '?').trim().split(/\s+/).slice(0, 2).map(w => w[0]).join('').toUpperCase();
const enc = o => btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const clean = o => { const c = Object.assign({}, o); delete c.id; return c; };
/* ---------- school year: the class moves up every 1 April; after Class 12, alerts run till 31 July for that year's entrance exams, then stop ---------- */
const ORDER = ['Class 9', 'Class 10', 'Class 11', 'Class 12'];
const sessionOf = d => d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1;
function school(p, now) {
  now = now || new Date();
  const cur = sessionOf(now), base = p.clsSession != null ? p.clsSession : sessionOf(toDate(p.created) || now), yrs = Math.max(0, cur - base);
  const left = p.cls === 'Gap year / dropper' ? 1 : ORDER.includes(p.cls) ? 4 - ORDER.indexOf(p.cls) : 99;
  if (yrs < left) return { cls: p.cls === 'Gap year / dropper' ? p.cls : ORDER[ORDER.indexOf(p.cls) + yrs] || p.cls, done: false, active: true, moved: yrs > 0, cur };
  const until = new Date(base + left, 6, 31, 23, 59);
  return { cls: 'Finished Class 12', done: true, active: now <= until, until, moved: true, cur };
}
/* ---------- city names: spelling slips ("saharnapur") are grouped under the right city ---------- */
let CITIES = [];
const low = s => String(s || '').toLowerCase().replace(/\s+/g, ' ').trim();
const title = s => String(s || '').replace(/\s+/g, ' ').trim().toLowerCase().replace(/(^|[\s-])\S/g, m => m.toUpperCase());
const dist = (a, b) => { const d = []; for (let i = 0; i <= a.length; i++) { d[i] = [i]; for (let j = 1; j <= b.length; j++) d[i][j] = i ? Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1), i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1] ? d[i - 2][j - 2] + 1 : 99) : j; } return d[a.length][b.length]; };
const CITY_MEMO = {};
function cityFix(raw) {   // the proper spelling, or null if it is already right or we can't tell
  const v = low(raw); if (!v) return null;
  if (v in CITY_MEMO) return CITY_MEMO[v];
  let out = null; const exact = CITIES.find(c => low(c) === v);
  if (exact) out = exact === raw.trim() ? null : exact;
  else if (v.length >= 4) { let best = [], min = 9; CITIES.forEach(c => { const n = dist(v, low(c)); if (n < min) { min = n; best = [c]; } else if (n === min) best.push(c); }); if (min <= (v.length <= 5 ? 1 : 2) && best.length === 1) out = best[0]; }
  return (CITY_MEMO[v] = out);
}
const cityOf = u => { const f = cityFix(u.city || ''); return f || title(u.city); };

let fb = null, ME = '', TAB = 'overview';
let S = { users: [], requests: [], ann: [], bin: [], links: [], sentToday: 0, exams: [], access: [], results: [], codes: [], crm: {} };
const P0 = { q: '', role: '', cls: '', stream: '', city: '', stage: '', follow: '', test: '', family: '', joined: '', sort: 'new', shown: 50 };
let P = Object.assign({}, P0), SEL = new Set(), RF = 'open', RQ = '', TF = '', TQ = '', BK = '', BQ = '';

async function loadFb() {
  const base = 'https://www.gstatic.com/firebasejs/' + FB_VER + '/';
  const [app, auth, fs] = await Promise.all([import(base + 'firebase-app.js'), import(base + 'firebase-auth.js'), import(base + 'firebase-firestore.js')]);
  const a = app.initializeApp(CFG.firebase);
  fb = { auth: auth.getAuth(a), A: auth, db: fs.getFirestore(a), F: fs };
}
function shell(h) { ROOT.innerHTML = h; ROOT.classList.remove('is-loading'); }
function gate(title, text, btn) { shell(`<div class="acct-card"><h2>${title}</h2><p class="acct-sub">${text}</p>${btn || ''}</div>`); }
const rulesMsg = x => /permission|insufficient/i.test(x && x.message || '') ? 'Firestore said no. Publish the latest firestore.rules in the Firebase console, then try again.' : (x && x.message || 'Something went wrong.') + ' Try again.';

async function load() {
  const F = fb.F, all = async col => (await F.getDocs(F.collection(fb.db, col))).docs.map(d => Object.assign({ id: d.id }, d.data()));
  const [users, requests, ann, bin, links, stat, crm] = await Promise.all([all('users'), all('requests'), all('announcements'), all('archive').catch(() => []), all('links'), F.getDoc(F.doc(fb.db, 'stats', 'mail-' + ymd())).catch(() => null), all('crm').catch(() => [])]);
  Object.assign(S, { users: users.map(u => Object.assign(u, { uid: u.id })), requests, ann, bin, links, sentToday: stat && stat.exists() ? stat.data().sent || 0 : 0, crm: Object.fromEntries(crm.map(c => [c.id, c])) });
  if (link('test') !== '#') { const [access, results, codes] = await Promise.all([all('access').catch(() => []), all('results').catch(() => []), all('codes').catch(() => [])]); Object.assign(S, { access, results, codes }); }
  sortAll();
}
function sortAll() {
  const byTime = (a, b) => (toDate(b.created) || 0) - (toDate(a.created) || 0);
  S.users.sort(byTime); S.requests.sort(byTime); S.ann.sort(byTime); S.bin.sort((a, b) => (toDate(b.deletedAt) || 0) - (toDate(a.deletedAt) || 0));
}

/* ---------- small lookups ---------- */
const userOf = uid => S.users.find(u => u.uid === uid);
const crmOf = uid => S.crm[uid] || {};
const stageOf = uid => crmOf(uid).stage || 'new';
const kidsOf = u => S.users.filter(s => (s.parents || []).includes(u.uid));
const linked = u => u.role === 'parent' ? kidsOf(u).length > 0 : (u.parents || []).length > 0;
const accessOf = uid => S.access.find(a => a.id === uid);
const resultOf = uid => S.results.find(r => r.id === uid);
function dueOf(uid) {   // overdue | today | week | later | ''
  const f = crmOf(uid).follow; if (!f) return '';
  const t = ymd(); return f < t ? 'overdue' : f === t ? 'today' : f <= ymd(7) ? 'week' : 'later';
}
const dueLabel = uid => { const f = crmOf(uid).follow, d = dueOf(uid); return !f ? '' : d === 'overdue' ? 'Overdue: ' + day(f) : d === 'today' ? 'Today' : f === ymd(1) ? 'Tomorrow' : day(f); };
const binId = (key, kind) => key + '-' + kind + '-' + Date.now();
const uidOf = b => b.uid || ((/^u[0-9a-f]{27}/.exec(b.id || '') || [])[0]) || '';

/* ---------- layout ---------- */
function render() {
  const a = document.activeElement, keep = a && ROOT.contains(a) && a.dataset && a.dataset.keep ? { k: a.dataset.keep, s: a.selectionStart, e: a.selectionEnd } : null;
  const open = S.requests.filter(r => r.status === 'requested').length, drafts = S.ann.filter(x => x.status === 'draft').length;
  const due = S.users.filter(u => ['overdue', 'today'].includes(dueOf(u.uid))).length;
  const tabs = [['overview', 'Overview'], ['people', `People <i${due ? ' class="hot" title="Follow-ups due"' : ''}>${due ? due + ' due' : S.users.length}</i>`], ['requests', `Counselling${open ? ` <i class="hot">${open}</i>` : ''}`],
    ['ann', `Announcements${drafts ? ` <i class="hot">${drafts}</i>` : ''}`]].concat(link('test') !== '#' ? [['test', `Psychometric test <i>${S.results.filter(r => r.done).length}</i>`]] : []).concat([['bin', `Bin <i>${S.bin.length}</i>`]]);
  const TITLES = { overview: 'Today at a glance', people: 'Students and parents', requests: 'Counselling requests', ann: 'Announcements', test: 'Psychometric test', bin: 'Bin' };
  shell(`<div class="adm">
    <header class="adm-top"><div><p class="acct-k">MyUniMentor admin${ME ? ` <span>· ${esc(ME)}</span>` : ''}</p><h2>${TITLES[TAB]}</h2></div>
      <div class="adm-top-btns"><button type="button" class="btn btn-outline btn-small adm-refresh">Refresh</button><a class="btn btn-outline btn-small" href="${link('account')}">My account</a></div></header>
    <nav class="adm-tabs" role="tablist" aria-label="Admin sections">${tabs.map(([k, t]) => `<button type="button" role="tab" data-t="${k}" aria-selected="${TAB === k}">${t}</button>`).join('')}</nav>
    <div class="adm-body">${({ overview, people, requests: reqs, ann: annTab, test: testTab, bin: binTab })[TAB]()}</div></div>`);
  $$('.adm-tabs button').forEach(b => b.addEventListener('click', () => { TAB = b.dataset.t; render(); window.scrollTo({ top: 0 }); }));
  $('.adm-refresh').addEventListener('click', async () => { $('.adm-refresh').textContent = 'Loading…'; await load(); render(); });
  $$('[data-open]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); drawer(b.dataset.open); }));
  ({ overview: wireOverview, people: wirePeople, requests: wireReqs, ann: wireAnn, test: wireTest, bin: wireBin })[TAB]();
  if (keep) { const n = ROOT.querySelector(`[data-keep="${keep.k}"]`); if (n) { n.focus(); try { n.setSelectionRange(keep.s, keep.e); } catch (_) {} } }
}
const tile = (k, v, s, go) => `<${go ? `button type="button" data-go="${go}"` : 'div'} class="adm-tile"><span>${k}</span><b>${v}</b>${s ? `<small>${s}</small>` : ''}</${go ? 'button' : 'div'}>`;
const searchBox = (key, val, ph) => `<label class="adm-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg><input type="search" data-keep="${key}" value="${esc(val)}" placeholder="${ph}" aria-label="${ph}"></label>`;

/* ---------- overview ---------- */
function bars(rows, f) {   // rows: [label, n, filter value]; clicking a row opens People with that filter
  const max = Math.max(1, ...rows.map(r => r[1]));
  return rows.length ? `<ul class="adm-bars">${rows.map(([k, n, v]) => `<li>${f ? `<button type="button" data-f="${f}" data-v="${esc(v == null ? k : v)}">` : '<div>'}<span>${esc(k)}</span><b style="--w:${Math.round(n / max * 100)}%"><i></i></b><em>${n}</em>${f ? '</button>' : '</div>'}</li>`).join('')}</ul>` : '<p class="acct-muted">Nothing yet.</p>';
}
function count(list, f) { const m = {}; list.forEach(x => [].concat(f(x) || []).forEach(k => { if (k) m[k] = (m[k] || 0) + 1; })); return Object.entries(m).sort((a, b) => b[1] - a[1]); }
function overview() {
  const st = S.users.filter(u => u.role === 'student'), pa = S.users.filter(u => u.role === 'parent');
  const exName = id => (S.exams.find(e => e.id === id) || {}).exam || id;
  const due = S.users.filter(u => ['overdue', 'today'].includes(dueOf(u.uid))).sort((a, b) => (crmOf(a.uid).follow || '').localeCompare(crmOf(b.uid).follow || ''));
  const typos = S.users.filter(u => cityFix(u.city || ''));
  return `<div class="adm-tiles">${tile('Students', st.length, `${st.filter(u => ago(u.created) < 7).length} joined this week`, 'student')}${tile('Parents', pa.length, `${S.links.filter(l => l.status === 'accepted').length} linked to a child`, 'parent')}
    ${tile('Follow-ups due', due.length, due.length ? 'Today or overdue' : 'All caught up', 'due')}${tile('Open counselling', S.requests.filter(r => r.status === 'requested').length, `${S.requests.filter(r => r.status === 'booked').length} booked`, 'requests')}${tile('Emails today', S.sentToday, 'Limit about 300 a day')}</div>
    <div class="adm-grid">
      <section class="acct-box adm-due-box"><h3>Follow-ups due</h3>${due.length ? `<ul class="adm-mini">${due.slice(0, 8).map(u => `<li><a href="#" data-open="${esc(u.uid)}"><b>${esc(u.name)}</b></a><span class="adm-due d-${dueOf(u.uid)}">${dueLabel(u.uid)}</span></li>`).join('')}</ul>` : '<p class="acct-muted">Nothing due. Set a follow-up date on any profile and it shows up here on the day.</p>'}</section>
      <section class="acct-box"><h3>Where they are</h3>${bars(Object.keys(STAGES).map(k => [STAGES[k], S.users.filter(u => stageOf(u.uid) === k).length, k]).filter(r => r[1]), 'stage')}</section>
      <section class="acct-box"><h3>Students by class</h3>${bars(CLASSES.concat('Finished Class 12').map(c => [c, st.filter(u => school(u).cls === c).length, c]).filter(r => r[1]), 'cls')}</section>
      <section class="acct-box"><h3>Students by stream</h3>${bars(Object.keys(STREAMS).map(k => [STREAMS[k], st.filter(u => u.stream === k).length, k]).filter(r => r[1]).sort((a, b) => b[1] - a[1]), 'stream')}</section>
      <section class="acct-box"><h3>Top cities</h3>${bars(count(S.users, cityOf).slice(0, 8), 'city')}${typos.length ? `<p class="adm-note">${typos.length} ${typos.length === 1 ? 'city looks' : 'cities look'} misspelt. <button type="button" class="acct-link adm-fix-cities">Fix spellings</button></p>` : ''}</section>
      <section class="acct-box"><h3>Most followed exams</h3>${bars(count(st, u => (u.exams || []).map(exName)).slice(0, 8))}</section>
      <section class="acct-box"><h3>Courses they’re interested in</h3>${bars(count(st, u => u.targets).slice(0, 8))}</section>
      <section class="acct-box"><h3>Latest sign-ups</h3><ul class="adm-mini">${S.users.slice(0, 6).map(u => `<li><a href="#" data-open="${esc(u.uid)}"><b>${esc(u.name)}</b></a><span>${u.role === 'parent' ? 'Parent' : esc(school(u).cls || '')}, ${fmt(u.created)}</span></li>`).join('') || '<li>None yet.</li>'}</ul></section>
    </div>`;
}
function wireOverview() {
  $$('.adm-bars button').forEach(b => b.addEventListener('click', () => { P = Object.assign({}, P0, { [b.dataset.f]: b.dataset.v }); TAB = 'people'; render(); }));
  $$('[data-go]').forEach(b => b.addEventListener('click', () => {
    const g = b.dataset.go; if (g === 'requests') { RF = 'requested'; TAB = 'requests'; } else { P = Object.assign({}, P0, g === 'due' ? { follow: 'due', sort: 'follow' } : { role: g }); TAB = 'people'; }
    render();
  }));
  const fx = $('.adm-fix-cities'); if (fx) fx.addEventListener('click', fixCities);
}
async function fixCities() {
  const list = S.users.filter(u => cityFix(u.city || ''));
  if (!list.length || !confirm(`Correct ${list.length} city ${list.length === 1 ? 'name' : 'names'}?\n\n${list.slice(0, 12).map(u => `${u.city} → ${cityFix(u.city)}  (${u.name})`).join('\n')}${list.length > 12 ? '\n…' : ''}`)) return;
  const F = fb.F, b = F.writeBatch(fb.db);
  list.forEach(u => b.update(F.doc(fb.db, 'users', u.uid), { city: cityFix(u.city) }));
  try { await b.commit(); list.forEach(u => { u.city = cityFix(u.city); }); render(); } catch (x) { alert(rulesMsg(x)); }
}

/* ---------- people ---------- */
function peopleRows() {
  const q = low(P.q), t = link('test') !== '#';
  const rows = S.users.filter(u => {
    if (P.role && u.role !== P.role) return false;
    if (q && !low([u.name, u.email, u.whatsapp, u.city, u.school, crmOf(u.uid).note].join(' ')).includes(q)) return false;
    if (P.cls && !(u.role === 'student' && school(u).cls === P.cls)) return false;
    if (P.stream && u.stream !== P.stream) return false;
    if (P.city && cityOf(u) !== P.city) return false;
    if (P.stage && stageOf(u.uid) !== P.stage) return false;
    if (P.joined && ago(u.created) > +P.joined) return false;
    if (P.follow) { const d = dueOf(u.uid); if (P.follow === 'due' ? !['overdue', 'today'].includes(d) : P.follow === 'week' ? !d || d === 'later' : !!d) return false; }
    if (t && P.test) { const a = !!accessOf(u.uid), r = resultOf(u.uid); if (P.test === 'done' ? !(r && r.done) : P.test === 'unlocked' ? !a : a) return false; }
    if (P.family && (P.family === 'yes') !== linked(u)) return false;
    return true;
  });
  const by = { new: null, old: (a, b) => (toDate(a.created) || 0) - (toDate(b.created) || 0), name: (a, b) => String(a.name).localeCompare(String(b.name)),
    follow: (a, b) => (crmOf(a.uid).follow || '9999').localeCompare(crmOf(b.uid).follow || '9999') }[P.sort];
  return by ? rows.slice().sort(by) : rows;
}
function people() {
  const rows = peopleRows(), shown = rows.slice(0, P.shown), t = link('test') !== '#';
  const cities = count(S.users, cityOf).map(([c, n]) => [c, `${c} (${n})`]);
  const sel = (k, all, opts) => `<select class="adm-f${P[k] ? ' is-on' : ''}" data-k="${k}" aria-label="${all}"><option value="">${all}</option>${opts.map(([v, x]) => `<option value="${esc(v)}"${P[k] === v ? ' selected' : ''}>${esc(x)}</option>`).join('')}</select>`;
  const on = ['role', 'cls', 'stream', 'city', 'stage', 'follow', 'test', 'family', 'joined'].filter(k => P[k]).length;
  const typos = S.users.filter(u => cityFix(u.city || '')).length;
  return `<div class="adm-tools">
      <div class="adm-tools-row">${searchBox('pq', P.q, 'Search name, email, phone, city, school or notes')}
        <select class="adm-sort" aria-label="Sort">${[['new', 'Newest first'], ['old', 'Oldest first'], ['name', 'Name A–Z'], ['follow', 'Follow-up date']].map(([k, x]) => `<option value="${k}"${P.sort === k ? ' selected' : ''}>${x}</option>`).join('')}</select>
        <button type="button" class="btn btn-outline btn-small adm-csv">Download CSV</button></div>
      <div class="adm-filters" role="group" aria-label="Filters">
        ${sel('role', 'Everyone', [['student', 'Students'], ['parent', 'Parents']])}
        ${sel('cls', 'All classes', CLASSES.concat('Finished Class 12').map(c => [c, c]))}
        ${sel('stream', 'All streams', Object.entries(STREAMS))}
        ${sel('city', 'All cities', cities)}
        ${sel('stage', 'Any stage', Object.entries(STAGES))}
        ${sel('follow', 'Any follow-up', [['due', 'Due today or overdue'], ['week', 'Due this week'], ['none', 'No follow-up set']])}
        ${t ? sel('test', 'Psychometric: any', [['done', 'Finished the test'], ['unlocked', 'Test unlocked'], ['locked', 'Test not unlocked']]) : ''}
        ${sel('family', 'Family: any', [['yes', 'Parent and child linked'], ['no', 'Not linked']])}
        ${sel('joined', 'Joined: any time', [['1', 'Last 24 hours'], ['7', 'Last 7 days'], ['30', 'Last 30 days']])}
        ${on ? `<button type="button" class="acct-link adm-clear">Clear ${on} ${on === 1 ? 'filter' : 'filters'}</button>` : ''}</div></div>
    <div class="adm-count-row"><p><b>${rows.length}</b> of ${S.users.length} people${typos ? ` · <button type="button" class="acct-link adm-fix-cities">Fix ${typos} misspelt ${typos === 1 ? 'city' : 'cities'}</button>` : ''}</p>
      <div class="adm-bulk"${SEL.size ? '' : ' hidden'}><b class="adm-bulk-n">${SEL.size} selected</b>
        <select class="adm-bulk-stage" aria-label="Set stage for selected"><option value="">Set stage…</option>${Object.entries(STAGES).map(([k, x]) => `<option value="${k}">${x}</option>`).join('')}</select>
        <button type="button" class="btn btn-outline btn-small adm-bulk-csv">Download CSV</button><button type="button" class="btn btn-outline btn-small adm-bulk-bin">Move to Bin</button><button type="button" class="acct-link adm-bulk-clear">Clear</button></div></div>
    <div class="adm-table-wrap"><table class="adm-table adm-people adm-cards"><thead><tr><th class="adm-ck"><input type="checkbox" class="adm-ck-all" aria-label="Select everyone shown"${shown.length && shown.every(u => SEL.has(u.uid)) ? ' checked' : ''}></th><th>Person</th><th>WhatsApp</th><th>Class and stream</th><th>City</th><th>Stage</th><th>Follow-up</th><th>Joined</th><th><span class="sr-only">Open</span></th></tr></thead><tbody>
    ${shown.map(u => { const s = school(u), kids = kidsOf(u), st = stageOf(u.uid), d = dueOf(u.uid);
      return `<tr>
      <td class="adm-ck"><input type="checkbox" class="adm-ck-one" value="${esc(u.uid)}" aria-label="Select ${esc(u.name)}"${SEL.has(u.uid) ? ' checked' : ''}></td>
      <td class="adm-person"><span class="adm-av r-${esc(u.role)}" aria-hidden="true">${esc(initials(u.name))}</span><div><a href="#" class="adm-name" data-open="${esc(u.uid)}">${esc(u.name)}</a> <span class="adm-role r-${esc(u.role)}">${u.role === 'parent' ? 'Parent' : 'Student'}</span><small>${esc(u.email)}</small></div></td>
      <td data-l="WhatsApp" class="adm-nw">${u.whatsapp ? `<a href="https://wa.me/91${esc(u.whatsapp)}" target="_blank" rel="noopener">+91 ${esc(u.whatsapp)}</a>` : '—'}</td>
      <td data-l="Class">${u.role === 'student' ? `${esc(s.cls)}${s.done && !s.active ? ' <small class="adm-off">Alerts stopped</small>' : ''}<small>${esc(STREAMS[u.stream] || '')}</small>` : kids.length ? `Parent of ${kids.map(k => `<a href="#" data-open="${esc(k.uid)}">${esc(k.name)}</a>`).join(', ')}` : '<small>Not linked to a child</small>'}</td>
      <td data-l="City">${esc(u.city || '—')}${cityFix(u.city || '') ? ` <small class="adm-off" title="Probably ${esc(cityFix(u.city))}">Check spelling</small>` : ''}${u.school ? `<small>${esc(u.school)}</small>` : ''}</td>
      <td data-l="Stage"><span class="adm-stage s-${st}">${STAGES[st]}</span></td>
      <td data-l="Follow-up" class="adm-nw">${d ? `<span class="adm-due d-${d}">${dueLabel(u.uid)}</span>` : '<span class="adm-dim">—</span>'}</td>
      <td data-l="Joined" class="adm-nw">${fmt(u.created)}</td>
      <td class="adm-go"><button type="button" class="btn btn-outline btn-small" data-open="${esc(u.uid)}">Open</button></td></tr>`; }).join('') || `<tr><td colspan="9" class="adm-empty">No one matches.${on || P.q ? ' <button type="button" class="acct-link adm-clear">Clear search and filters</button>' : ''}</td></tr>`}
    </tbody></table></div>
    ${rows.length > P.shown ? `<p class="adm-more-row"><button type="button" class="btn btn-outline btn-small adm-more">Show ${Math.min(50, rows.length - P.shown)} more</button></p>` : ''}`;
}
function csv(list, name) {
  const cols = ['name', 'role', 'email', 'whatsapp', 'cls', 'stream', 'city', 'school', 'targets', 'exams', 'parentEmails', 'created', 'stage', 'followUp', 'lastNote'];
  const cell = v => '"' + String(Array.isArray(v) ? v.join('; ') : v && (v.toDate || v instanceof Date) ? fmt(v, true) : v == null ? '' : v).replace(/"/g, '""') + '"';
  const val = (u, c) => c === 'stream' ? STREAMS[u.stream] || u.stream : c === 'cls' ? (u.role === 'student' ? school(u).cls : '') : c === 'stage' ? STAGES[stageOf(u.uid)] : c === 'followUp' ? crmOf(u.uid).follow : c === 'lastNote' ? ((crmOf(u.uid).log || []).slice(-1)[0] || {}).text : u[c];
  const out = [cols.join(',')].concat(list.map(u => cols.map(c => cell(val(u, c))).join(','))).join('\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + out], { type: 'text/csv' })); a.download = `myunimentor-${name}-${ymd()}.csv`; a.click();
}
function wirePeople() {
  const s = $('[data-keep="pq"]'); s.addEventListener('input', () => { P.q = s.value; P.shown = 50; render(); });
  $('.adm-sort').addEventListener('change', e => { P.sort = e.target.value; render(); });
  $$('.adm-f').forEach(x => x.addEventListener('change', () => { P[x.dataset.k] = x.value; P.shown = 50; render(); }));
  $$('.adm-clear').forEach(b => b.addEventListener('click', () => { P = Object.assign({}, P0, { sort: P.sort }); render(); }));
  $('.adm-csv').addEventListener('click', () => csv(peopleRows(), 'accounts'));
  const fx = $('.adm-fix-cities'); if (fx) fx.addEventListener('click', fixCities);
  const more = $('.adm-more'); if (more) more.addEventListener('click', () => { P.shown += 50; render(); });
  // selection: updates in place so the page doesn't jump
  const bulk = () => { $('.adm-bulk').hidden = !SEL.size; $('.adm-bulk-n').textContent = SEL.size + ' selected'; const all = $$('.adm-ck-one'); $('.adm-ck-all').checked = all.length > 0 && all.every(c => c.checked); };
  $$('.adm-ck-one').forEach(c => c.addEventListener('change', () => { c.checked ? SEL.add(c.value) : SEL.delete(c.value); bulk(); }));
  $('.adm-ck-all').addEventListener('change', e => { $$('.adm-ck-one').forEach(c => { c.checked = e.target.checked; c.checked ? SEL.add(c.value) : SEL.delete(c.value); }); bulk(); });
  $('.adm-bulk-clear').addEventListener('click', () => { SEL.clear(); render(); });
  const picked = () => S.users.filter(u => SEL.has(u.uid));
  $('.adm-bulk-csv').addEventListener('click', () => csv(picked(), 'selected'));
  $('.adm-bulk-stage').addEventListener('change', async e => {
    const st = e.target.value; if (!st) return; const list = picked(), F = fb.F, b = F.writeBatch(fb.db);
    list.forEach(u => b.set(F.doc(fb.db, 'crm', u.uid), { stage: st, updated: F.serverTimestamp(), by: ME }, { merge: true }));
    try { await b.commit(); list.forEach(u => { S.crm[u.uid] = Object.assign(crmOf(u.uid), { stage: st }); }); SEL.clear(); render(); } catch (x) { alert(rulesMsg(x)); e.target.value = ''; }
  });
  $('.adm-bulk-bin').addEventListener('click', async () => {
    const list = picked(); if (!confirm(`Move ${list.length} ${list.length === 1 ? 'account' : 'accounts'} to the Bin?\n\n${list.slice(0, 10).map(u => u.name).join(', ')}${list.length > 10 ? '…' : ''}\n\nTheir dashboards and emails stop. You can restore them from the Bin.`)) return;
    try { for (const u of list) await binAccount(u); SEL.clear(); render(); } catch (x) { alert(rulesMsg(x)); render(); }
  });
}

/* ---------- one person: details, follow-up, edit, actions (a side panel) ---------- */
let DR = null, DR_BACK = null;
function closeDrawer() { if (!DR) return; DR.remove(); DR = null; document.documentElement.classList.remove('adm-lock'); document.removeEventListener('keydown', drKey); if (DR_BACK && DR_BACK.isConnected) DR_BACK.focus(); }
function drKey(e) {
  if (e.key === 'Escape') return closeDrawer();
  if (e.key === 'Tab') { const f = [...DR.querySelectorAll('a[href],button:not([disabled]),input:not([type=hidden]),select,textarea')].filter(x => x.offsetParent); if (!f.length) return; const a = f[0], z = f[f.length - 1]; if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); } else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); } }
}
function drawer(uid, editing) {
  const u = userOf(uid); if (!u) return;
  const first = !DR; if (first) DR_BACK = document.activeElement;
  if (DR) DR.remove();
  const s = school(u), c = crmOf(uid), st = stageOf(uid), kids = kidsOf(u), t = link('test') !== '#', acc = accessOf(uid), res = resultOf(uid);
  const reqs = S.requests.filter(r => r.uid === uid || r.by === uid);
  const exName = id => (S.exams.find(e => e.id === id) || {}).exam || id;
  const inviter = u.ref ? userOf(u.ref) : null, fix = cityFix(u.city || '');
  const n = u.notify || {}, alerts = ['instant', 'reminders', 'digest'].filter(k => n[k] !== false);
  const row = (k, v) => v ? `<div><dt>${k}</dt><dd>${v}</dd></div>` : '';
  const log = (c.log || []).slice().reverse();
  DR = document.createElement('div'); DR.className = 'adm-dr-wrap';
  DR.innerHTML = `<div class="adm-dr-back"></div><aside class="adm-dr" role="dialog" aria-modal="true" aria-labelledby="adm-dr-h">
    <header class="adm-dr-head"><span class="adm-av r-${esc(u.role)}" aria-hidden="true">${esc(initials(u.name))}</span><div><h3 id="adm-dr-h">${esc(u.name)}</h3><p>${u.role === 'parent' ? 'Parent' : esc(s.cls) + (u.stream ? ', ' + esc(STREAMS[u.stream] || u.stream) : '')}${u.city ? ', ' + esc(u.city) : ''}</p></div><button type="button" class="adm-dr-x" aria-label="Close">×</button></header>
    <div class="adm-dr-body">
      <div class="adm-dr-acts">${u.whatsapp ? `<a class="btn btn-cyan btn-small" href="https://wa.me/91${esc(u.whatsapp)}" target="_blank" rel="noopener">WhatsApp</a><a class="btn btn-outline btn-small" href="tel:+91${esc(u.whatsapp)}">Call</a>` : ''}<a class="btn btn-outline btn-small" href="mailto:${esc(u.email)}">Email</a><button type="button" class="btn btn-outline btn-small adm-dr-edit"${editing ? ' hidden' : ''}>Edit profile</button></div>
      ${editing ? editForm(u) : ''}
      <section class="adm-dr-sec adm-crm"><h4>Follow-up <span class="adm-saved" hidden>Saved</span></h4>
        <div class="adm-seg" role="radiogroup" aria-label="Stage">${Object.entries(STAGES).map(([k, x]) => `<label><input type="radio" name="stage" value="${k}"${st === k ? ' checked' : ''}><span class="s-${k}">${x}</span></label>`).join('')}</div>
        <div class="adm-follow"><label>Next follow-up<input type="date" name="follow" value="${esc(c.follow || '')}" min="${ymd(-365)}"></label>
          <div class="adm-quick">${[[1, 'Tomorrow'], [3, 'In 3 days'], [7, 'In a week']].map(([d, x]) => `<button type="button" data-d="${d}">${x}</button>`).join('')}${c.follow ? '<button type="button" data-d="">Clear</button>' : ''}</div></div>
        <form class="adm-note-form"><label class="sr-only" for="adm-note">Add a note</label><textarea id="adm-note" name="note" rows="2" maxlength="1000" placeholder="Add a note: what you discussed, what they need next…"></textarea><button class="btn btn-cyan btn-small" type="submit">Add note</button></form>
        ${log.length ? `<ol class="adm-log">${log.map(l => `<li><p>${esc(l.text).replace(/\n/g, '<br>')}</p><small>${fmt(l.at, true)}${l.by ? ' · ' + esc(l.by) : ''}</small></li>`).join('')}</ol>` : '<p class="adm-dim">No notes yet. Only staff can see notes.</p>'}
        <p class="acct-err" hidden></p></section>
      <section class="adm-dr-sec"><h4>Profile</h4><dl class="adm-dl">
        ${row('Email', `<a href="mailto:${esc(u.email)}">${esc(u.email)}</a>`)}${row('WhatsApp', u.whatsapp ? '+91 ' + esc(u.whatsapp) : '—')}
        ${u.role === 'student' ? row('Class', esc(s.cls) + (s.moved && !s.done ? ` <small>(joined in ${esc(u.cls)}, moved up on 1 April)</small>` : '') + (s.done ? ` <small>${s.active ? 'alerts run till 31 July' : 'alerts stopped'}</small>` : '')) + row('Stream', esc(STREAMS[u.stream] || '—')) + row('School', esc(u.school || '—')) : ''}
        ${row('City', esc(u.city || '—') + (fix ? ` <button type="button" class="acct-link adm-dr-city" data-v="${esc(fix)}">Change to ${esc(fix)}</button>` : ''))}
        ${row('Joined', fmt(u.created, true))}${inviter ? row('Invited by', `<a href="#" data-open="${esc(inviter.uid)}">${esc(inviter.name)}</a>`) : ''}
        ${row('Email alerts', alerts.length === 3 ? 'All on' : alerts.length ? alerts.map(k => ({ instant: 'Instant', reminders: 'Reminders', digest: 'Weekly digest' }[k])).join(', ') + ' only' : '<span class="adm-off">All turned off</span>')}
        ${u.role === 'student' ? row('Parents', (u.parentEmails || []).map(esc).join('<br>') || '<span class="adm-dim">Not linked</span>') : row('Children', kids.map(k => `<a href="#" data-open="${esc(k.uid)}">${esc(k.name)}</a>`).join(', ') || '<span class="adm-dim">Not linked</span>')}
      </dl>
      ${(u.targets || []).length ? `<p class="adm-dr-lab">Courses they’re interested in</p><p class="adm-tags">${u.targets.map(x => `<span>${esc(x)}</span>`).join('')}</p>` : ''}
      ${(u.exams || []).length ? `<p class="adm-dr-lab">Exams they follow (${u.exams.length})</p><p class="adm-tags">${u.exams.map(x => `<span>${esc(exName(x))}</span>`).join('')}</p>` : ''}
      ${(u.saved || []).length ? `<p class="adm-dr-lab">Saved pages (${u.saved.length})</p><p class="adm-tags">${u.saved.map(x => `<span>${esc(x.title || x.slug)}</span>`).join('')}</p>` : ''}</section>
      ${u.role === 'student' ? `<section class="adm-dr-sec"><h4>Career check</h4>${u.check && u.check.top ? `<p class="adm-dim">Taken ${fmt(u.check.at)}. Top matches:</p><ol class="adm-top3">${u.check.top.map(x => `<li>${esc(x)}</li>`).join('')}</ol>${u.check.a && link('check') !== '#' ? `<a class="btn btn-outline btn-small" href="${link('check')}#r=${enc(u.check.a)}" target="_blank" rel="noopener">Open full result</a>` : ''}` : '<p class="adm-dim">Not taken yet.</p>'}</section>` : ''}
      ${t && u.role === 'student' ? `<section class="adm-dr-sec"><h4>Psychometric test</h4><p>${res && res.done ? `Finished ${fmt(res.done)}${res.code ? `, interest code <b>${esc(res.code)}</b>` : ''}${(res.topN || [])[0] ? `. Top match: ${esc(res.topN[0])}` : ''}` : res && res.state ? 'In progress' : acc ? 'Unlocked, not started' : 'Not unlocked'}${acc ? ` <small class="adm-dim">(${esc(VIA[acc.via] || acc.via)})</small>` : ''}</p>
        <div class="adm-dr-acts">${res && res.done ? `<a class="btn btn-outline btn-small" href="${link('test')}?u=${esc(uid)}" target="_blank" rel="noopener">View report</a><button type="button" class="acct-link adm-dr-retake">Let them retake</button>` : ''}${acc ? '<button type="button" class="acct-link adm-dr-lock">Take back access</button>' : '<button type="button" class="btn btn-cyan btn-small adm-dr-unlock">Unlock the test for free</button>'}</div></section>` : ''}
      <section class="adm-dr-sec"><h4>Counselling requests</h4>${reqs.length ? `<ul class="adm-mini">${reqs.map(r => `<li><span><b>${esc(r.topic || 'No topic written')}</b><small>${fmt(r.created)}${r.when ? ', session ' + esc(r.when) : ''}</small></span><span class="acct-pill p-${esc(r.status)}">${RSTAT[r.status] || esc(r.status)}</span></li>`).join('')}</ul>` : '<p class="adm-dim">None.</p>'}</section>
      <section class="adm-dr-sec adm-dr-danger"><button type="button" class="acct-link adm-dr-bin">Move ${esc(u.name.split(' ')[0])} to the Bin</button><small>Their dashboard and emails stop${t ? ', and their test unlock and report go with them' : ''}. You can restore everything from the Bin.</small></section>
    </div></aside>`;
  document.body.appendChild(DR); document.documentElement.classList.add('adm-lock');
  if (first) document.addEventListener('keydown', drKey);
  const q = s => DR.querySelector(s), F = fb.F;
  q('.adm-dr-back').addEventListener('click', closeDrawer); q('.adm-dr-x').addEventListener('click', closeDrawer);
  DR.querySelectorAll('[data-open]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); drawer(a.dataset.open); }));
  (editing ? q('.adm-edit [name=name]') : q('.adm-dr-x')).focus();
  const err = q('.adm-crm .acct-err'), saved = q('.adm-crm .adm-saved');
  const save = async (data, logEntry) => {
    err.hidden = true;
    const up = Object.assign({}, data, { updated: F.serverTimestamp(), by: ME });
    if (logEntry) up.log = F.arrayUnion(logEntry);
    try {
      await F.setDoc(F.doc(fb.db, 'crm', uid), up, { merge: true });
      const cur = S.crm[uid] = Object.assign(crmOf(uid), data); if (logEntry) cur.log = (cur.log || []).concat(logEntry);
      saved.hidden = false; setTimeout(() => { saved.hidden = true; }, 1600); return true;
    } catch (x) { err.textContent = rulesMsg(x); err.hidden = false; return false; }
  };
  DR.querySelectorAll('[name=stage]').forEach(r => r.addEventListener('change', async () => { await save({ stage: r.value }); refreshBehind(); }));
  const fd = q('[name=follow]');
  fd.addEventListener('change', async () => { await save({ follow: fd.value || '' }); refreshBehind(); drawer(uid); });
  DR.querySelectorAll('.adm-quick button').forEach(b => b.addEventListener('click', () => { fd.value = b.dataset.d ? ymd(+b.dataset.d) : ''; fd.dispatchEvent(new Event('change')); }));
  q('.adm-note-form').addEventListener('submit', async e => {
    e.preventDefault(); const text = e.target.note.value.trim(); if (!text) return;
    const b = e.target.querySelector('button'); b.disabled = true;
    const entry = { at: Date.now(), by: ME, text };
    const ok = await save(stageOf(uid) === 'new' ? { stage: 'contacted' } : {}, entry);   // a note means someone has been in touch
    b.disabled = false; if (ok) { refreshBehind(); drawer(uid); }
  });
  const ed = q('.adm-dr-edit'); if (ed) ed.addEventListener('click', () => drawer(uid, true));
  if (editing) wireEdit(u);
  const cf = q('.adm-dr-city'); if (cf) cf.addEventListener('click', async () => {
    try { await F.updateDoc(F.doc(fb.db, 'users', uid), { city: cf.dataset.v }); u.city = cf.dataset.v; refreshBehind(); drawer(uid); } catch (x) { alert(rulesMsg(x)); }
  });
  const un = q('.adm-dr-unlock'); if (un) un.addEventListener('click', async () => {
    const d = { via: 'admin', by: fb.auth && fb.auth.currentUser ? fb.auth.currentUser.uid : '', at: F.serverTimestamp() };
    try { await F.setDoc(F.doc(fb.db, 'access', uid), d); S.access.push(Object.assign({ id: uid }, d, { at: new Date() })); refreshBehind(); drawer(uid); } catch (x) { alert(rulesMsg(x)); }
  });
  const rt = q('.adm-dr-retake'); if (rt) rt.addEventListener('click', async () => { if (await binReport(uid)) { refreshBehind(); drawer(uid); } });
  const lk = q('.adm-dr-lock'); if (lk) lk.addEventListener('click', async () => { if (await binTest(uid)) { refreshBehind(); drawer(uid); } });
  q('.adm-dr-bin').addEventListener('click', async () => {
    if (!confirm(`Move ${u.name} (${u.email}) to the Bin?\n\nTheir dashboard and emails stop. You can restore them from the Bin.`)) return;
    try { await binAccount(u); closeDrawer(); render(); } catch (x) { alert(rulesMsg(x)); }
  });
}
const refreshBehind = () => { const y = window.scrollY; render(); window.scrollTo(0, y); };

/* edit a profile (staff powers): email and role stay as they are, because the login depends on them */
function editForm(u) {
  const st = u.role === 'student', n = u.notify || {};
  const opt = (list, cur) => list.map(([v, x]) => `<option value="${esc(v)}"${cur === v ? ' selected' : ''}>${esc(x)}</option>`).join('');
  return `<form class="adm-dr-sec adm-edit acct-form" novalidate><h4>Edit profile</h4>
    <div class="acct-grid"><label>Full name<input name="name" value="${esc(u.name)}" maxlength="80" required></label>
      <label>WhatsApp number<span class="acct-ph"><span>+91</span><input name="whatsapp" inputmode="numeric" maxlength="10" value="${esc(u.whatsapp || '')}"></span></label>
      ${st ? `<label>Class now<select name="cls">${opt(CLASSES.map(c => [c, c]), school(u).done ? '' : school(u).cls)}${school(u).done ? '<option value="" selected>Finished Class 12</option>' : ''}</select></label>
      <label>Stream<select name="stream">${opt(Object.entries(STREAMS), u.stream)}</select></label>` : ''}
      <label>City<input name="city" value="${esc(u.city || '')}" maxlength="60" autocomplete="off"></label>
      ${st ? `<label>School<input name="school" value="${esc(u.school || '')}" maxlength="120"></label>` : ''}</div>
    ${st ? `<fieldset class="acct-targets"><legend>Courses they’re interested in</legend><div class="acct-chips">${TARGETS.map(x => `<label><input type="checkbox" name="targets" value="${esc(x)}"${(u.targets || []).includes(x) ? ' checked' : ''}><span>${esc(x)}</span></label>`).join('')}</div></fieldset>
    ${S.exams.length ? `<fieldset class="acct-targets"><legend>Exams they follow</legend><div class="acct-chips adm-chips-sm">${S.exams.map(e => `<label><input type="checkbox" name="exams" value="${esc(e.id)}"${(u.exams || []).includes(e.id) ? ' checked' : ''}><span>${esc(e.exam)}</span></label>`).join('')}</div></fieldset>` : ''}` : ''}
    <fieldset class="acct-targets"><legend>Email alerts</legend><div class="acct-chips">${[['instant', 'Instant'], ['reminders', 'Reminders'], ['digest', 'Weekly digest']].map(([k, x]) => `<label><input type="checkbox" name="notify" value="${k}"${n[k] !== false ? ' checked' : ''}><span>${x}</span></label>`).join('')}</div></fieldset>
    <p class="adm-dim">Email (${esc(u.email)}) and account type can’t be changed here, because the login uses them.</p>
    <p class="acct-err" hidden></p><div class="acct-actions"><button type="button" class="acct-link adm-edit-cancel">Cancel</button><button class="btn btn-cyan btn-small" type="submit">Save changes</button></div></form>`;
}
function wireEdit(u) {
  const f = DR.querySelector('.adm-edit'), er = f.querySelector('.acct-err'), F = fb.F;
  f.querySelector('.adm-edit-cancel').addEventListener('click', () => drawer(u.uid));
  f.addEventListener('submit', async e => {
    e.preventDefault(); er.hidden = true; const fail = m => { er.textContent = m; er.hidden = false; };
    const name = f.name.value.trim().replace(/\s+/g, ' '), wa = f.whatsapp.value.replace(/\D/g, ''), city = f.city.value.trim();
    if (name.length < 2) return fail('Enter their name.');
    if (wa && !/^[6-9]\d{9}$/.test(wa)) return fail('Enter a 10-digit WhatsApp number starting with 6, 7, 8 or 9.');
    const up = { name, city: cityFix(city) || title(city), notify: Object.fromEntries(['instant', 'reminders', 'digest'].map(k => [k, !!f.querySelector(`[name=notify][value=${k}]`).checked])) };
    if (u.role === 'student') {
      Object.assign(up, { stream: f.stream.value, school: f.school.value.trim(), targets: [...f.querySelectorAll('[name=targets]:checked')].map(x => x.value) });
      if (f.querySelector('[name=exams]')) up.exams = [...f.querySelectorAll('[name=exams]:checked')].map(x => x.value);
      if (f.cls.value && f.cls.value !== school(u).cls) Object.assign(up, { cls: f.cls.value, clsSession: sessionOf(new Date()) });   // class as of this school year
    }
    const b = f.querySelector('button[type=submit]'); b.disabled = true; b.textContent = 'Saving…';
    try {
      const batch = F.writeBatch(fb.db);
      if (wa && wa !== (u.whatsapp || '')) {   // one number = one account: claim the new number, free the old one
        const p = await F.getDoc(F.doc(fb.db, 'phones', wa));
        if (p.exists() && p.data().uid !== u.uid) { b.disabled = false; b.textContent = 'Save changes'; const o = userOf(p.data().uid); return fail(`+91 ${wa} already belongs to ${o ? o.name : 'another account'}.`); }
        batch.set(F.doc(fb.db, 'phones', wa), { uid: u.uid, created: F.serverTimestamp() });
        if (u.whatsapp) batch.delete(F.doc(fb.db, 'phones', u.whatsapp));
        up.whatsapp = wa;
      }
      batch.update(F.doc(fb.db, 'users', u.uid), up); await batch.commit();
      Object.assign(u, up); refreshBehind(); drawer(u.uid);
    } catch (x) { b.disabled = false; b.textContent = 'Save changes'; fail(rulesMsg(x)); }
  });
}

/* ---------- the Bin: everything deleted lands here first, and can be restored ---------- */
const stamp = () => ({ deletedAt: fb.F.serverTimestamp(), deletedBy: 'admin', deletedByEmail: ME });
const local = o => Object.assign(o, { deletedAt: new Date() });
async function binAccount(u) {
  const F = fb.F, b = F.writeBatch(fb.db), acc = accessOf(u.uid), res = resultOf(u.uid), test = {};
  if (acc) test.access = clean(acc); if (res) test.result = clean(res);
  const id = binId(u.uid, 'account'), item = Object.assign(clean(u), { kind: 'account', uid: u.uid }, stamp(), Object.keys(test).length ? { test } : {});
  b.set(F.doc(fb.db, 'archive', id), item);
  if (u.whatsapp) b.delete(F.doc(fb.db, 'phones', u.whatsapp));
  b.delete(F.doc(fb.db, 'users', u.uid));
  if (acc) b.delete(F.doc(fb.db, 'access', u.uid)); if (res) b.delete(F.doc(fb.db, 'results', u.uid));
  await b.commit();
  S.users = S.users.filter(x => x.uid !== u.uid); S.access = S.access.filter(x => x.id !== u.uid); S.results = S.results.filter(x => x.id !== u.uid); SEL.delete(u.uid);
  S.bin.unshift(local(Object.assign(item, { id })));
}
async function binReport(uid) {
  const u = userOf(uid) || {}, r = resultOf(uid);
  if (!r || !confirm(`Move ${u.name || 'this student'}’s report to the Bin so they can take the test again?\n\nYou can restore the old report from the Bin.`)) return false;
  const F = fb.F, b = F.writeBatch(fb.db), id = binId(uid, 'report'), item = Object.assign({ kind: 'report', uid, name: u.name || r.name || uid, email: u.email || '', data: clean(r) }, stamp());
  b.set(F.doc(fb.db, 'archive', id), item); b.delete(F.doc(fb.db, 'results', uid));
  try { await b.commit(); } catch (x) { alert(rulesMsg(x)); return false; }
  S.results = S.results.filter(x => x.id !== uid); S.bin.unshift(local(Object.assign(item, { id }))); return true;
}
async function binTest(uid) {
  const u = userOf(uid) || {}, a = accessOf(uid), r = resultOf(uid), who = u.name || (r && r.name) || 'this student';
  if (!a || !confirm(u.uid ? `Take back ${who}’s free access to the test?${r ? ' Their report goes to the Bin too.' : ''}\n\nYou can restore it from the Bin.` : `${who}’s account was deleted. Remove their test unlock${r ? ' and report' : ''}?\n\nIt goes to the Bin, where you can delete it forever.`)) return false;
  const F = fb.F, b = F.writeBatch(fb.db), id = binId(uid, 'test'), item = Object.assign({ kind: 'test', uid, name: who, email: u.email || '', data: Object.assign({ access: clean(a) }, r ? { result: clean(r) } : {}) }, stamp());
  b.set(F.doc(fb.db, 'archive', id), item); b.delete(F.doc(fb.db, 'access', uid)); if (r) b.delete(F.doc(fb.db, 'results', uid));
  try { await b.commit(); } catch (x) { alert(rulesMsg(x)); return false; }
  S.access = S.access.filter(x => x.id !== uid); S.results = S.results.filter(x => x.id !== uid); S.bin.unshift(local(Object.assign(item, { id }))); return true;
}
async function binAnn(a) {
  const F = fb.F, b = F.writeBatch(fb.db), id = binId(a.id, 'announcement'), item = Object.assign({ kind: 'announcement', annId: a.id, name: a.subject, data: clean(a) }, stamp());
  b.set(F.doc(fb.db, 'archive', id), item); b.delete(F.doc(fb.db, 'announcements', a.id)); await b.commit();
  S.ann = S.ann.filter(x => x.id !== a.id); S.bin.unshift(local(Object.assign(item, { id })));
}
async function restore(it) {
  const F = fb.F, b = F.writeBatch(fb.db), kind = it.kind || 'account', uid = uidOf(it);
  const back = { account: () => {}, report: () => {}, test: () => {}, announcement: () => {} };
  if (kind === 'account') {
    if (!uid) throw new Error('This entry was saved without an account ID, so it can’t be restored. Ask them to sign up again.');
    if (userOf(uid)) throw new Error(`${it.name} has signed up again since, so there’s nothing to restore. Delete this entry instead.`);
    if (it.whatsapp) {
      const p = await F.getDoc(F.doc(fb.db, 'phones', it.whatsapp));
      if (p.exists() && p.data().uid !== uid) throw new Error(`+91 ${it.whatsapp} now belongs to another account, so this one can’t be restored as it was.`);
      b.set(F.doc(fb.db, 'phones', it.whatsapp), { uid, created: F.serverTimestamp() });
    }
    const prof = Object.assign({}, it); ['id', 'uid', 'kind', 'deletedAt', 'deletedBy', 'deletedByEmail', 'test'].forEach(k => delete prof[k]);
    b.set(F.doc(fb.db, 'users', uid), prof);
    const tt = it.test || {};
    if (tt.access && !accessOf(uid)) b.set(F.doc(fb.db, 'access', uid), tt.access);
    if (tt.result && !resultOf(uid)) b.set(F.doc(fb.db, 'results', uid), tt.result);
    back.account = () => { S.users.push(Object.assign(prof, { id: uid, uid })); if (tt.access && !accessOf(uid)) S.access.push(Object.assign({ id: uid }, tt.access)); if (tt.result && !resultOf(uid)) S.results.push(Object.assign({ id: uid }, tt.result)); };
  } else if (kind === 'report' || kind === 'test') {
    const d = kind === 'report' ? { result: it.data } : it.data || {};
    if (d.result && resultOf(uid)) throw new Error(`${it.name} has a newer report. Move that one to the Bin first if you want this one back.`);
    if (d.result && !accessOf(uid) && !d.access) throw new Error(`${it.name}’s test isn’t unlocked any more. Restore their test unlock first.`);
    if (d.access && !accessOf(uid)) b.set(F.doc(fb.db, 'access', uid), d.access);
    if (d.result) b.set(F.doc(fb.db, 'results', uid), d.result);
    back[kind] = () => { if (d.access && !accessOf(uid)) S.access.push(Object.assign({ id: uid }, d.access)); if (d.result) S.results.push(Object.assign({ id: uid }, d.result)); };
  } else if (kind === 'announcement') {
    b.set(F.doc(fb.db, 'announcements', it.annId), it.data);
    back.announcement = () => S.ann.push(Object.assign({ id: it.annId }, it.data));
  }
  b.delete(F.doc(fb.db, 'archive', it.id));
  await b.commit();
  back[kind](); S.bin = S.bin.filter(x => x.id !== it.id); sortAll();
}
function binRows() {
  const q = low(BQ);
  return S.bin.filter(b => (!BK || (b.kind || 'account') === BK) && (!q || low([b.name, b.email, b.whatsapp, b.city].join(' ')).includes(q)));
}
function binTab() {
  const rows = binRows(), n = k => S.bin.filter(b => (b.kind || 'account') === k).length;
  return `<div class="adm-tools"><div class="adm-tools-row">${searchBox('bq', BQ, 'Search the Bin')}
      <select class="adm-bk adm-f${BK ? ' is-on' : ''}" aria-label="Show"><option value="">Everything (${S.bin.length})</option>${Object.entries(KINDS).map(([k, x]) => `<option value="${k}"${BK === k ? ' selected' : ''}>${x}s (${n(k)})</option>`).join('')}</select></div></div>
    <p class="acct-muted">Everything deleted, by you or by students and parents themselves, waits here until you delete it forever. Counselling requests are never deleted.</p>
    <div class="adm-table-wrap"><table class="adm-table adm-cards adm-bin"><thead><tr><th>What</th><th>Details</th><th>Deleted</th><th><span class="sr-only">Actions</span></th></tr></thead><tbody>
    ${rows.map(b => { const k = b.kind || 'account', self = b.deletedBy !== 'admin', d = b.data || {};
      const det = k === 'account' ? [b.email, b.whatsapp ? '+91 ' + b.whatsapp : '', b.role === 'parent' ? 'Parent' : [b.cls, STREAMS[b.stream]].filter(Boolean).join(', '), b.city, b.test ? 'with test ' + (b.test.result && b.test.result.done ? 'report' : 'unlock') : ''].filter(Boolean).map(esc).join('<br>')
        : k === 'report' ? esc(b.email) + `<br>${d.done ? 'Finished ' + fmt(d.done) : 'Not finished'}${d.code ? ', code ' + esc(d.code) : ''}`
        : k === 'test' ? esc(b.email) + '<br>' + esc(VIA[(d.access || {}).via] || 'Unlocked') + (d.result ? ', with report' : '')
        : esc((d.body || '').slice(0, 120)) + ((d.body || '').length > 120 ? '…' : '');
      return `<tr><td><b>${esc(b.name || '—')}</b> <span class="adm-kind k-${k}">${KINDS[k]}</span></td><td data-l="Details">${det}</td>
        <td data-l="Deleted" class="adm-nw">${fmt(b.deletedAt, true)}<small>${self ? 'by themselves' : 'by ' + esc(b.deletedByEmail || 'staff')}</small></td>
        <td class="adm-bin-acts"><button type="button" class="btn btn-outline btn-small adm-restore" data-id="${esc(b.id)}"${k === 'account' && !uidOf(b) ? ' disabled' : ''}>Restore</button><button type="button" class="acct-link adm-purge" data-id="${esc(b.id)}">Delete forever</button>${k === 'account' && !uidOf(b) ? '<small class="adm-dim">Can’t be restored: no account ID was saved. They can sign up again.</small>' : ''}</td></tr>`; }).join('') || `<tr><td colspan="4" class="adm-empty">${S.bin.length ? 'Nothing matches.' : 'The Bin is empty.'}</td></tr>`}
    </tbody></table></div>`;
}
function wireBin() {
  const s = $('[data-keep="bq"]'); s.addEventListener('input', () => { BQ = s.value; render(); });
  $('.adm-bk').addEventListener('change', e => { BK = e.target.value; render(); });
  $$('.adm-restore').forEach(b => b.addEventListener('click', async () => {
    const it = S.bin.find(x => x.id === b.dataset.id), k = it.kind || 'account';
    if (k === 'account' && it.deletedBy !== 'admin' && !confirm(`${it.name} deleted this account themselves. Restore it only if they asked you to.\n\nRestore now?`)) return;
    b.disabled = true; b.textContent = 'Restoring…';
    try { await restore(it); render(); } catch (x) { alert(x.code ? rulesMsg(x) : x.message); b.disabled = false; b.textContent = 'Restore'; }
  }));
  $$('.adm-purge').forEach(b => b.addEventListener('click', async () => {
    const it = S.bin.find(x => x.id === b.dataset.id);
    if (!confirm(`Delete “${it.name}” (${KINDS[it.kind || 'account']}) forever?\n\nThis can’t be undone.`)) return;
    try { await fb.F.deleteDoc(fb.F.doc(fb.db, 'archive', it.id)); S.bin = S.bin.filter(x => x.id !== it.id); render(); } catch (x) { alert(rulesMsg(x)); }
  }));
}

/* ---------- counselling ---------- */
function reqs() {
  const q = low(RQ), cnt = k => S.requests.filter(r => k === 'all' || (k === 'open' ? ['requested', 'booked'].includes(r.status) : r.status === k)).length;
  const list = S.requests.filter(r => (RF === 'all' || (RF === 'open' ? ['requested', 'booked'].includes(r.status) : r.status === RF)) && (!q || low([r.studentName, r.byName, r.email, r.phone, r.topic].join(' ')).includes(q)));
  return `<div class="adm-tools"><div class="adm-tools-row">${searchBox('rq', RQ, 'Search name, email, phone or topic')}</div>
    <div class="adm-segtabs" role="group" aria-label="Show">${[['open', 'Open'], ['requested', 'Requested'], ['booked', 'Booked'], ['done', 'Completed'], ['cancelled', 'Cancelled'], ['all', 'All']].map(([k, x]) => `<button type="button" data-rf="${k}" aria-pressed="${RF === k}">${x} <i>${cnt(k)}</i></button>`).join('')}</div></div>
    <p class="acct-muted">Students see the status, time and notes on their dashboard.</p>
    <div class="adm-reqs">${list.map(r => `<form class="acct-box adm-req" data-id="${esc(r.id)}">
      <div class="adm-req-head"><div><b>${esc(r.studentName)}</b><span class="acct-pill p-${esc(r.status)}">${RSTAT[r.status] || esc(r.status)}</span>
        <p class="acct-muted">${esc(r.cls)}${r.stream ? ', ' + esc(STREAMS[r.stream] || r.stream) : ''}. Asked ${fmt(r.created, true)}${r.byName && r.byName !== r.studentName ? ` by parent ${esc(r.byName)}` : ''}</p></div>
        <div class="adm-contact">${r.phone ? `<a class="btn btn-cyan btn-small" href="https://wa.me/91${esc(r.phone)}" target="_blank" rel="noopener">WhatsApp</a><a class="btn btn-outline btn-small" href="tel:+91${esc(r.phone)}">Call</a>` : ''}<a class="btn btn-outline btn-small" href="mailto:${esc(r.email)}">Email</a>${userOf(r.uid) ? `<button type="button" class="btn btn-outline btn-small" data-open="${esc(r.uid)}">Profile</button>` : ''}</div></div>
      <blockquote>${esc(r.topic) || '<i>No topic written</i>'}<small>Best time: ${esc(r.slot || 'Any time')}</small></blockquote>
      <div class="adm-req-edit"><label>Status<select name="status">${Object.entries(RSTAT).map(([k, x]) => `<option value="${k}"${r.status === k ? ' selected' : ''}>${x}</option>`).join('')}</select></label>
        <label><span>Session time <span class="opt">(shown to the student)</span></span><input name="when" value="${esc(r.when)}" placeholder="e.g. Sat 28 Nov, 5 pm"></label>
        <label class="adm-wide"><span>Notes for the student <span class="opt">(shown on their dashboard)</span></span><textarea name="notes" rows="3" placeholder="Summary, next steps, colleges to look at…">${esc(r.notes)}</textarea></label></div>
      <div class="acct-actions"><span class="adm-saved" hidden>Saved</span><button class="btn btn-cyan btn-small" type="submit">Save</button></div></form>`).join('') || '<p class="acct-muted adm-empty">No requests here.</p>'}</div>`;
}
function wireReqs() {
  const s = $('[data-keep="rq"]'); s.addEventListener('input', () => { RQ = s.value; render(); });
  $$('[data-rf]').forEach(b => b.addEventListener('click', () => { RF = b.dataset.rf; render(); }));
  $$('.adm-req').forEach(f => f.addEventListener('submit', async e => {
    e.preventDefault(); const b = f.querySelector('button[type=submit]'); b.disabled = true;
    const up = { status: f.status.value, when: f.when.value.trim(), notes: f.notes.value.trim(), updated: fb.F.serverTimestamp() };
    try { await fb.F.updateDoc(fb.F.doc(fb.db, 'requests', f.dataset.id), up); Object.assign(S.requests.find(r => r.id === f.dataset.id), up); const s = f.querySelector('.adm-saved'); s.hidden = false; setTimeout(() => { s.hidden = true; }, 1800); }
    catch (x) { alert(rulesMsg(x)); }
    b.disabled = false;
  }));
}

/* ---------- announcements ---------- */
const on = (u, k) => (u.notify || {})[k] !== false;
function audience(a) {
  const aud = a.audience || {}, streams = aud.streams || [], classes = aud.classes || [];
  return S.users.filter(u => {
    if (aud.role && aud.role !== 'all' && u.role !== aud.role) return false;
    if (!['instant', 'reminders', 'digest'].some(k => on(u, k))) return false;
    const look = u.role === 'student' ? [u] : kidsOf(u);
    if (streams.length && !look.some(s => streams.includes(s.stream))) return false;
    if (look.length && !look.some(s => school(s).active)) return false;
    if (classes.length && !look.some(s => classes.includes(school(s).cls))) return false;
    return true;
  });
}
const ASTAT = { draft: 'Draft', approved: 'Sending', sent: 'Sent' };
function annForm(a) {
  a = a || { audience: { role: 'all' } }; const aud = a.audience || {};
  const chips = (name, obj, sel) => Object.entries(obj).map(([k, v]) => `<label><input type="checkbox" name="${name}" value="${esc(k)}"${(sel || []).includes(k) ? ' checked' : ''}><span>${esc(v)}</span></label>`).join('');
  return `<form class="acct-box acct-form adm-ann-form" data-id="${esc(a.id || '')}"><h3>${a.id ? 'Edit draft' : 'New announcement'}</h3>
    <label>Subject<input name="subject" maxlength="90" required value="${esc(a.subject)}" placeholder="e.g. Free Career Summit at your school"></label>
    <label>Message<textarea name="body" rows="6" required placeholder="Write it like a short note. Leave an empty line between paragraphs.">${esc(a.body)}</textarea></label>
    <div class="acct-grid"><label><span>Button text <span class="opt">(optional)</span></span><input name="cta_label" value="${esc(a.cta_label)}" placeholder="e.g. See the details"></label>
      <label><span>Button link <span class="opt">(optional)</span></span><input name="cta_url" type="url" value="${esc(a.cta_url)}" placeholder="https://myunimentor.in/…"></label></div>
    <fieldset class="acct-targets"><legend>Send to</legend><div class="acct-chips">${[['all', 'Everyone'], ['student', 'Students only'], ['parent', 'Parents only']].map(([k, x]) => `<label><input type="radio" name="role" value="${k}"${(aud.role || 'all') === k ? ' checked' : ''}><span>${x}</span></label>`).join('')}</div></fieldset>
    <fieldset class="acct-targets"><legend>Only these streams <span class="opt">(leave empty for all)</span></legend><div class="acct-chips">${chips('streams', STREAMS, aud.streams)}</div></fieldset>
    <fieldset class="acct-targets"><legend>Only these classes <span class="opt">(leave empty for all)</span></legend><div class="acct-chips">${chips('classes', Object.fromEntries(CLASSES.map(c => [c, c])), aud.classes)}</div></fieldset>
    <p class="adm-count"></p><div class="acct-actions adm-ann-btns"><button type="button" class="acct-link adm-ann-cancel">Cancel</button><button class="btn btn-outline btn-small" type="submit">Save draft</button></div></form>`;
}
function annTab() {
  return `<div class="adm-bar"><button type="button" class="btn btn-cyan btn-small adm-ann-new">New announcement</button>
    <p class="acct-muted">Nothing is sent until you press “Approve and send”. Emails go out within the hour. New guides on the site appear here as drafts for you to approve.</p></div>
    <div class="adm-ann-slot"></div>
    <div class="adm-anns">${S.ann.map(a => `<article class="acct-box adm-ann" data-id="${esc(a.id)}"><div class="adm-req-head"><div><b>${esc(a.subject)}</b><span class="acct-pill p-${a.status === 'sent' ? 'done' : a.status === 'approved' ? 'booked' : 'requested'}">${ASTAT[a.status] || esc(a.status)}</span>${a.auto ? '<span class="acct-pill">Auto draft</span>' : ''}
      <p class="acct-muted">${a.status === 'sent' ? `Sent to ${a.sentCount || 0} people, ${fmt(a.sentAt, true)}` : a.status === 'approved' ? `Approved, ${a.sentCount || 0} sent so far` : `Will reach about ${audience(a).length} people`}. ${audDesc(a)}</p></div></div>
      <div class="adm-ann-body">${esc(a.body).replace(/\n/g, '<br>')}${a.cta_url ? `<p><a href="${esc(a.cta_url)}" target="_blank" rel="noopener">${esc(a.cta_label || 'Find out more')}</a></p>` : ''}</div>
      ${a.status === 'draft' ? `<div class="acct-actions adm-ann-btns"><button type="button" class="acct-link adm-ann-rm">Move to Bin</button><button type="button" class="btn btn-outline btn-small adm-ann-edit">Edit</button><button type="button" class="btn btn-cyan btn-small adm-ann-go">Approve and send</button></div>` : ''}</article>`).join('') || '<p class="acct-muted">No announcements yet.</p>'}</div>`;
}
function audDesc(a) {
  const aud = a.audience || {}, parts = [aud.role === 'student' ? 'Students' : aud.role === 'parent' ? 'Parents' : 'Everyone'];
  if ((aud.streams || []).length) parts.push(aud.streams.map(s => STREAMS[s] || s).join(', '));
  if ((aud.classes || []).length) parts.push(aud.classes.join(', '));
  return esc(parts.join('; '));
}
function wireAnn() {
  const slot = $('.adm-ann-slot');
  const open = a => {
    slot.innerHTML = annForm(a); const f = slot.querySelector('form'), cnt = f.querySelector('.adm-count');
    const read = () => ({ subject: f.subject.value.trim(), body: f.body.value.trim(), cta_label: f.cta_label.value.trim(), cta_url: f.cta_url.value.trim(),
      audience: { role: f.role.value, streams: [...f.querySelectorAll('[name=streams]:checked')].map(x => x.value), classes: [...f.querySelectorAll('[name=classes]:checked')].map(x => x.value) } });
    const upd = () => { cnt.textContent = `Will reach about ${audience(read()).length} people (anyone who turned off every email is left out).`; };
    f.addEventListener('change', upd); upd();
    f.querySelector('.adm-ann-cancel').addEventListener('click', () => { slot.innerHTML = ''; });
    f.addEventListener('submit', async e => {
      e.preventDefault(); const d = read();
      if (!d.subject || !d.body) { alert('Add a subject and a message.'); return; }
      if (d.cta_url && !/^https:\/\//.test(d.cta_url)) { alert('The button link must start with https://'); return; }
      const F = fb.F;
      try {
        if (f.dataset.id) await F.updateDoc(F.doc(fb.db, 'announcements', f.dataset.id), d);
        else await F.addDoc(F.collection(fb.db, 'announcements'), Object.assign(d, { status: 'draft', created: F.serverTimestamp() }));
        await load(); render();
      } catch (x) { alert(rulesMsg(x)); }
    });
    f.subject.focus();
  };
  $('.adm-ann-new').addEventListener('click', () => open());
  $$('.adm-ann').forEach(card => {
    const a = S.ann.find(x => x.id === card.dataset.id), F = fb.F, ref = F.doc(fb.db, 'announcements', a.id);
    const ed = card.querySelector('.adm-ann-edit'), go = card.querySelector('.adm-ann-go'), rm = card.querySelector('.adm-ann-rm');
    if (ed) ed.addEventListener('click', () => { open(a); slot.scrollIntoView({ behavior: 'smooth' }); });
    if (rm) rm.addEventListener('click', async () => { if (confirm('Move this draft to the Bin?')) { try { await binAnn(a); render(); } catch (x) { alert(rulesMsg(x)); } } });
    if (go) go.addEventListener('click', async () => {
      const n = audience(a).length;
      if (!confirm(`Send “${a.subject}” to about ${n} people?\n\nIt goes out within the hour and can’t be taken back.`)) return;
      await F.updateDoc(ref, { status: 'approved', approvedAt: F.serverTimestamp() }); await load(); render();
    });
  });
}

/* ---------- psychometric test: free access, codes, results ---------- */
const VIA = { payment: 'Paid ₹99', invites: '3 friends joined', code: 'Access code', admin: 'Given by staff' };
function testRows() {
  const q = low(TQ);
  return S.access.map(a => ({ a, u: userOf(a.id) || {}, r: resultOf(a.id) || {} })).filter(({ a, u, r }) =>
    (!TF || (TF === 'done' ? r.done : TF === 'progress' ? !r.done && r.state : !r.done && !r.state)) && (!q || low([u.name, u.email, a.code, r.code].join(' ')).includes(q)))
    .sort((x, y) => (toDate(y.a.at) || 0) - (toDate(x.a.at) || 0));
}
function testTab() {
  const done = S.results.filter(r => r.done), started = S.results.filter(r => !r.done);
  const invited = count(S.users.filter(u => u.ref), u => u.ref).map(([uid, n]) => [userOf(uid) ? userOf(uid).name : uid, n]).slice(0, 8);
  const rows = testRows();
  return `<div class="adm-tiles">${tile('Unlocked', S.access.length)}${tile('Finished', done.length)}${tile('In progress', started.length)}${tile('Joined by invite', S.users.filter(u => u.ref).length)}</div>
    <div class="adm-grid2">
      <section class="acct-box"><h3>Give free access</h3><p class="acct-muted">For a student who already has an account.</p>
        <form class="adm-grant acct-form" novalidate><label>Student’s email<input type="email" name="email" placeholder="student@example.com" required></label><p class="acct-err" hidden></p><button class="btn btn-cyan btn-small" type="submit">Unlock their test</button></form></section>
      <section class="acct-box"><h3>Make an access code</h3><p class="acct-muted">For a school, an event or a seminar. Each use unlocks one student.</p>
        <form class="adm-code acct-form" novalidate><div class="acct-grid"><label>Code<input name="code" maxlength="16" value="${newCode()}" style="text-transform:uppercase"></label><label>How many uses<input name="max" type="number" min="1" max="2000" value="50"></label>
        <label class="acct-span">Note (who it is for)<input name="note" maxlength="80" placeholder="e.g. Olympus High seminar, 2 Dec"></label></div><p class="acct-err" hidden></p><button class="btn btn-cyan btn-small" type="submit">Create code</button></form></section>
    </div>
    ${S.codes.length ? `<h3 class="adm-h">Access codes</h3><div class="adm-table-wrap"><table class="adm-table adm-cards"><thead><tr><th>Code</th><th>Used of allowed</th><th>For</th><th>Made</th><th><span class="sr-only">On or off</span></th></tr></thead><tbody>
      ${S.codes.map(c => `<tr${c.active === false ? ' class="adm-row-off"' : ''}><td><b>${esc(c.id)}</b>${c.active === false ? ' <small class="adm-off">Off</small>' : ''}</td><td data-l="Used of allowed"><div class="adm-lim"><span>${c.used || 0} of</span><button type="button" class="adm-step" data-id="${esc(c.id)}" data-d="-10" aria-label="10 fewer uses for ${esc(c.id)}">−</button><input class="adm-max" type="number" min="${Math.max(1, c.used || 0)}" max="5000" value="${c.max}" data-id="${esc(c.id)}" aria-label="Uses allowed for ${esc(c.id)}"><button type="button" class="adm-step" data-id="${esc(c.id)}" data-d="10" aria-label="10 more uses for ${esc(c.id)}">+</button><button type="button" class="btn btn-cyan btn-small adm-max-save" data-id="${esc(c.id)}" hidden>Save</button></div>${(c.used || 0) >= c.max ? '<small class="adm-full">Full: no more students can use it</small>' : ''}<small class="acct-err" hidden></small></td><td data-l="For">${esc(c.note || '—')}</td><td data-l="Made" class="adm-nw">${fmt(c.created)}</td><td><button type="button" class="acct-link adm-code-tg" data-id="${esc(c.id)}" data-on="${c.active !== false}">${c.active === false ? 'Turn on' : 'Turn off'}</button></td></tr>`).join('')}</tbody></table></div>` : ''}
    ${invited.length ? `<h3 class="adm-h">Top inviters</h3>${bars(invited)}` : ''}
    <h3 class="adm-h">Students</h3>
    <div class="adm-tools"><div class="adm-tools-row">${searchBox('tq', TQ, 'Search name, email or code')}</div>
      <div class="adm-segtabs" role="group" aria-label="Show">${[['', 'All', S.access.length], ['done', 'Finished', S.access.filter(a => (resultOf(a.id) || {}).done).length], ['progress', 'In progress', S.access.filter(a => { const r = resultOf(a.id); return r && !r.done && r.state; }).length], ['none', 'Not started', S.access.filter(a => { const r = resultOf(a.id); return !r || (!r.done && !r.state); }).length]].map(([k, x, n]) => `<button type="button" data-tf="${k}" aria-pressed="${TF === k}">${x} <i>${n}</i></button>`).join('')}</div></div>
    <div class="adm-table-wrap"><table class="adm-table adm-cards"><thead><tr><th>Name</th><th>Unlocked by</th><th>Interest code</th><th>Top match</th><th>Status</th><th><span class="sr-only">Actions</span></th></tr></thead><tbody>
    ${rows.map(({ a, u, r }) => `<tr><td>${u.uid ? `<a href="#" class="adm-name" data-open="${esc(a.id)}"><b>${esc(u.name)}</b></a><small>${esc(u.email || '')}</small>` : `<b>${esc(r.name || 'No name')}</b> <small class="adm-off">Account deleted</small>`}</td><td data-l="Unlocked by">${esc(VIA[a.via] || a.via)}${a.code ? `<small>${esc(a.code)}</small>` : ''}<small>${fmt(a.at)}</small></td><td data-l="Interest code">${esc(r.code || '—')}</td><td data-l="Top match">${esc((r.topN || [])[0] || '—')}</td>
        <td data-l="Status" class="adm-nw">${r.done ? 'Finished ' + fmt(r.done) : r.state ? 'In progress' : 'Not started'}</td><td class="adm-bin-acts">${r.done ? `<a class="btn btn-small btn-outline" href="${link('test')}?u=${esc(a.id)}">View report</a><button type="button" class="acct-link adm-reset" data-id="${esc(a.id)}">Let them retake</button>` : ''}<button type="button" class="acct-link adm-lock" data-id="${esc(a.id)}">${u.uid ? 'Take back access' : 'Remove'}</button></td></tr>`).join('') || `<tr><td colspan="6" class="adm-empty">${S.access.length ? 'Nobody matches.' : 'Nobody has unlocked the test yet.'}</td></tr>`}
    </tbody></table></div>`;
}
function newCode() { const A = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; let c = 'MUM-'; for (let i = 0; i < 5; i++) c += A[Math.random() * A.length | 0]; return c; }
function wireTest() {
  const F = fb.F, me = fb.auth && fb.auth.currentUser;
  const s = $('[data-keep="tq"]'); s.addEventListener('input', () => { TQ = s.value; render(); });
  $$('[data-tf]').forEach(b => b.addEventListener('click', () => { TF = b.dataset.tf; render(); }));
  const g = $('.adm-grant'), ge = g.querySelector('.acct-err');
  g.addEventListener('submit', async e => {
    e.preventDefault(); ge.hidden = true;
    const em = g.email.value.trim().toLowerCase(), u = S.users.find(x => (x.email || '').toLowerCase() === em);
    if (!u) { ge.textContent = 'No account with this email. Ask them to sign up first.'; ge.hidden = false; return; }
    if (accessOf(u.uid)) { ge.textContent = `${u.name}’s test is already unlocked.`; ge.hidden = false; return; }
    const d = { via: 'admin', by: me ? me.uid : '', at: F.serverTimestamp() };
    try { await F.setDoc(F.doc(fb.db, 'access', u.uid), d); S.access.push(Object.assign({ id: u.uid }, d, { at: new Date() })); render(); } catch (x) { ge.textContent = rulesMsg(x); ge.hidden = false; }
  });
  const c = $('.adm-code'), ce = c.querySelector('.acct-err');
  c.addEventListener('submit', async e => {
    e.preventDefault(); ce.hidden = true;
    const code = c.code.value.trim().toUpperCase().replace(/[^A-Z0-9-]/g, ''), max = parseInt(c.max.value, 10);
    if (!/^[A-Z0-9-]{4,16}$/.test(code)) { ce.textContent = 'Use 4–16 letters, numbers or dashes.'; ce.hidden = false; return; }
    if (!(max >= 1)) { ce.textContent = 'Enter how many students can use it.'; ce.hidden = false; return; }
    if (S.codes.some(x => x.id === code)) { ce.textContent = 'That code already exists.'; ce.hidden = false; return; }
    const d = { max, used: 0, note: c.note.value.trim(), active: true, created: F.serverTimestamp() };
    await F.setDoc(F.doc(fb.db, 'codes', code), d); S.codes.unshift(Object.assign({ id: code }, d, { created: new Date() })); render();
  });
  // Change how many students a code can unlock: never below the number already used
  const limRow = id => $$('.adm-max').find(i => i.dataset.id === id).closest('td');
  $$('.adm-max').forEach(i => i.addEventListener('input', () => { limRow(i.dataset.id).querySelector('.adm-max-save').hidden = +i.value === S.codes.find(x => x.id === i.dataset.id).max; }));
  $$('.adm-step').forEach(b => b.addEventListener('click', () => {
    const i = limRow(b.dataset.id).querySelector('.adm-max'); i.value = Math.min(5000, Math.max(+i.min, (+i.value || 0) + +b.dataset.d)); i.dispatchEvent(new Event('input'));
  }));
  $$('.adm-max-save').forEach(b => b.addEventListener('click', async () => {
    const td = limRow(b.dataset.id), i = td.querySelector('.adm-max'), er = td.querySelector('.acct-err'), c = S.codes.find(x => x.id === b.dataset.id), v = parseInt(i.value, 10);
    er.hidden = true;
    if (!(v >= Math.max(1, c.used || 0)) || v > 5000) { er.textContent = `Enter a number from ${Math.max(1, c.used || 0)} (already used) to 5000.`; er.hidden = false; return; }
    b.disabled = true;
    try { await F.updateDoc(F.doc(fb.db, 'codes', c.id), { max: v }); c.max = v; render(); }
    catch (_) { b.disabled = false; er.textContent = 'Could not save. Check your connection and try again.'; er.hidden = false; }
  }));
  $$('.adm-code-tg').forEach(b => b.addEventListener('click', async () => {
    const on = b.dataset.on !== 'true'; await F.updateDoc(F.doc(fb.db, 'codes', b.dataset.id), { active: on });
    S.codes.find(x => x.id === b.dataset.id).active = on; render();
  }));
  $$('.adm-reset').forEach(b => b.addEventListener('click', async () => { if (await binReport(b.dataset.id)) render(); }));
  $$('.adm-lock').forEach(b => b.addEventListener('click', async () => { if (await binTest(b.dataset.id)) render(); }));
}

/* ---------- boot ---------- */
(async function boot() {
  await Promise.all([fetch(link('exams')).then(r => r.json()).then(x => { S.exams = x; }).catch(() => {}), fetch('/assets/data/cities.json').then(r => r.json()).then(x => { CITIES = x; }).catch(() => {})]);
  document.addEventListener('keydown', e => { if (e.key === '/' && !DR && !/INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName)) { const s = ROOT.querySelector('.adm-search input'); if (s) { e.preventDefault(); s.focus(); } } });
  if (location.hash === '#demo') return demo();
  if (!CFG.firebase || !CFG.firebase.apiKey) return gate('Not set up', 'Firebase settings are missing.');
  try { await loadFb(); } catch (e) { return gate('Could not load', 'Check your internet connection and refresh.'); }
  fb.A.onAuthStateChanged(fb.auth, async u => {
    if (!u) return gate('Log in first', 'Log in with your MyUniMentor staff email, then come back to this page.', `<a class="btn btn-cyan" href="${link('account')}">Log in</a>`);
    const t = await u.getIdTokenResult(true);
    if (t.claims.admin !== true) return gate('Staff only', `You’re logged in as ${esc(t.claims.em || u.email || '')}, which isn’t on the admin list.`);
    ME = t.claims.em || u.email || '';
    try { await load(); render(); } catch (e) { gate('Could not load data', esc(e.message) + '. Check that the latest Firestore rules are published.'); }
  });
})();

function demo() {
  const ts = n => ({ toDate: () => new Date(Date.now() - n * 864e5) });
  ME = 'om@myunimentor.in';
  S.users = [
    { uid: 'a', role: 'student', name: 'Riya Sharma', email: 'riya@example.com', whatsapp: '9876543210', cls: 'Class 12', stream: 'pcm', city: 'Dehradun', school: 'Example School', exams: ['jee-main-session-1', 'cuet-ug'], targets: ['Engineering'], parentEmails: ['anil@example.com'], parents: ['b'], created: ts(1), check: { at: Date.now() - 864e5 * 3, top: ['Software, AI and computing', 'Maths, statistics and analytics', 'Core engineering'], a: { x: 1 } } },
    { uid: 'b', role: 'parent', name: 'Anil Sharma', email: 'anil@example.com', whatsapp: '9876500000', city: 'Dehradun', created: ts(1) },
    { uid: 'c', role: 'student', name: 'Kabir Negi', email: 'kabir@example.com', whatsapp: '9811111111', cls: 'Class 11', stream: 'comm', city: 'Haridwar', exams: ['cuet-ug', 'ipmat-indore'], targets: ['Management (BBA/IPM)', 'Commerce / CA'], created: ts(4), ref: 'a' },
    { uid: 'd', role: 'student', name: 'Sara Ali', email: 'sara@example.com', whatsapp: '9822222222', cls: 'Class 12', stream: 'hum', city: 'Roorkee', exams: ['clat', 'cuet-ug'], targets: ['Law'], created: ts(9), ref: 'a' },
    { uid: 'e', role: 'student', name: 'Aarav Mehta', email: 'aarav.mehta.longemail@example.com', whatsapp: '9833333333', cls: 'Class 12', stream: 'com', city: 'saharnapur', school: 'Example Public School', created: ts(0) },
    { uid: 'f', role: 'student', name: 'Meher Kaur', email: 'meher@example.com', whatsapp: '9844444444', cls: 'Class 12', stream: 'pcb', city: 'Saharanpur', created: ts(0) },
    { uid: 'g', role: 'student', name: 'Dev Rawat', email: 'dev@example.com', whatsapp: '9855555555', cls: 'Class 10', stream: 'und', city: 'Dehradoon', created: ts(15) }];
  S.crm = { a: { stage: 'counselled', follow: ymd(0), log: [{ at: Date.now() - 864e5, by: 'om@myunimentor.in', text: 'Called. Wants B.Tech CSE in Dehradun; send the JEE plan.' }] }, c: { stage: 'contacted', follow: ymd(-2) }, d: { stage: 'joined' }, e: { follow: ymd(4) } };
  S.requests = [{ id: 'r1', uid: 'a', by: 'a', studentName: 'Riya Sharma', byName: 'Riya Sharma', email: 'riya@example.com', phone: '9876543210', cls: 'Class 12', stream: 'pcm', topic: 'B.Tech CSE or BCA, and which colleges to apply to', slot: 'Weekday evenings', status: 'requested', created: ts(0) },
    { id: 'r2', uid: 'c', by: 'c', studentName: 'Kabir Negi', byName: 'Kabir Negi', email: 'kabir@example.com', phone: '9811111111', cls: 'Class 11', stream: 'comm', topic: 'IPMAT preparation plan', slot: 'Weekends', status: 'booked', when: 'Sat 28 Nov, 5 pm', created: ts(2) }];
  S.ann = [{ id: 'n1', subject: 'New guide: Entrance exam deadlines from late November to January', body: 'Every deadline in one place.\n\nRead it free on myunimentor.in.', cta_label: 'Read the guide', cta_url: 'https://myunimentor.in/entrance-exam-deadlines-december-2026', audience: { role: 'all' }, status: 'draft', auto: true, created: ts(0) }];
  S.bin = [{ id: 'uaaaa-1', name: 'Test Student', email: 'test@example.com', role: 'student', cls: 'Class 12', stream: 'pcb', city: 'Dehradun', created: ts(5), deletedAt: ts(1), deletedBy: 'user' },
    { id: 'h-report-1', kind: 'report', uid: 'h', name: 'Old Report', email: 'old@example.com', data: { done: ts(6), code: 'SAE' }, deletedAt: ts(2), deletedBy: 'admin', deletedByEmail: 'om@myunimentor.in' }];
  S.links = [{ status: 'accepted' }]; S.sentToday = 12;
  S.access = [{ id: 'a', via: 'code', code: 'MUM-OLY26', at: ts(1) }, { id: 'c', via: 'admin', at: ts(0) }];
  S.results = [{ id: 'a', done: ts(0), code: 'ICE', topN: ['Software, AI and computing', 'Maths, statistics and analytics', 'Core engineering'] }, { id: 'c', state: {} }];
  S.codes = [{ id: 'MUM-OLY26', max: 120, used: 37, note: 'Olympus High seminar', created: ts(3), active: true }];
  const nop = async () => {}, batch = () => ({ set() {}, update() {}, delete() {}, commit: nop });
  fb = { F: { doc: () => ({}), collection: () => ({}), updateDoc: nop, setDoc: nop, addDoc: nop, deleteDoc: nop, writeBatch: batch, getDoc: async () => ({ exists: () => false }), serverTimestamp: () => null, arrayUnion: x => x } };
  TAB = new URLSearchParams(location.search).get('tab') || 'overview';
  sortAll();
  load = async () => {};
  render();
  const o = new URLSearchParams(location.search).get('open'); if (o) drawer(o, location.search.includes('edit'));
}
