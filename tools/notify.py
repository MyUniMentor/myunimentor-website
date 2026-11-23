"""MyUniMentor automatic emails (runs in GitHub Actions, see .github/workflows/notify.yml).

  python3 tools/notify.py changes     after a push: exam changes -> instant alerts; new guides -> draft announcements
  python3 tools/notify.py scheduled   every hour: queued mail, approved announcements; once a day (from 8 am IST)
                                      deadline reminders (7 days and 1 day before); Sundays the weekly summary

Secrets (GitHub -> Settings -> Secrets and variables -> Actions):
  FIREBASE_SA   the whole service-account JSON (a separate key from the one in Apps Script)
  BREVO_KEY     Brevo API key
Optional: DRY_RUN=1 prints instead of sending; TEST_TO=you@x.in sends every email to that address only.
"""
import datetime, html, json, os, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
SITE = 'https://myunimentor.in'
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
NOW = datetime.datetime.now(IST)
TODAY = NOW.date()
DRY = os.environ.get('DRY_RUN') == '1'
TEST_TO = os.environ.get('TEST_TO', '').strip().lower()
WRITE = not (DRY or TEST_TO)       # test runs change nothing in the database
DAILY_LIMIT = int(os.environ.get('DAILY_LIMIT', '230'))   # Brevo free = 300/day, shared with login codes
FROM = {'name': 'MyUniMentor', 'email': 'updates@myunimentor.in'}
REPLY_TO = {'name': 'MyUniMentor', 'email': 'info@myunimentor.in'}
STREAMS = {'pcm': 'Science (PCM)', 'pcb': 'Science (PCB)', 'pcmb': 'Science (PCMB)', 'comm': 'Commerce with Maths',
           'com': 'Commerce without Maths', 'hum': 'Humanities (Arts)', 'und': 'Not decided yet'}
STATUS = {'confirmed': 'Confirmed', 'tentative': 'Tentative', 'expected': 'Expected'}
e = lambda s: html.escape(str(s or ''), quote=True)


# ---------------------------------------------------------------- email design (matches the login-code email)
C = dict(ink='#0E2540', night='#061629', cyan='#11BDDE', teal='#087286', sky='#EEF8FC', line='#DCE7EE', paper='#F3F7FA', muted='#4A5D73', sun='#FFC94D')
FONT = "'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"

def shell(preheader, inner, why='You get this because you have a MyUniMentor account.'):
    pad = '&#8199;&#65279;&#847;' * 30
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>MyUniMentor</title></head>'
            f'<body style="margin:0;padding:0;background:{C["paper"]};-webkit-text-size-adjust:100%">'
            f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent">{e(preheader)}{pad}</div>'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{C["paper"]}"><tr><td align="center" style="padding:28px 12px">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;border-radius:20px;overflow:hidden;background:#ffffff;box-shadow:0 6px 24px rgba(14,37,64,.08)">'
            f'<tr><td style="background:{C["ink"]};background-image:linear-gradient(135deg,{C["night"]} 0%,{C["ink"]} 60%,#14406A 100%);padding:26px 32px 24px">'
            f'<a href="{SITE}" style="text-decoration:none"><img src="{SITE}/assets/img/logo-horizontal-light.png" width="196" height="53" alt="MyUniMentor" style="display:block;border:0;width:196px;height:auto"></a></td></tr>'
            f'<tr><td style="height:4px;line-height:4px;font-size:0;background:{C["cyan"]};background-image:linear-gradient(90deg,{C["cyan"]},#5FDCF2 50%,{C["sun"]})">&nbsp;</td></tr>'
            f'<tr><td style="padding:34px 32px 30px;font-family:{FONT};color:{C["ink"]}">{inner}</td></tr></table>'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px"><tr><td align="center" style="padding:22px 20px 8px;font-family:{FONT};font-size:13px;line-height:20px;color:{C["muted"]}">'
            + '&nbsp;&nbsp;·&nbsp;&nbsp;'.join(f'<a href="{u}" style="color:{C["teal"]};text-decoration:none;font-weight:600">{t}</a>' for t, u in
                                                [('Exam&nbsp;calendar', SITE + '/exam-calendar'), ('Career&nbsp;check', SITE + '/career-check'), ('Course&nbsp;guides', SITE + '/courses'), ('Instagram', 'https://instagram.com/myunimentor.in')]) +
            f'</td></tr><tr><td align="center" style="padding:6px 28px 28px;font-family:{FONT};font-size:12px;line-height:18px;color:#7A8A9C">'
            f'From confused to confident, one step at a time.<br>MyUniMentor · Dehradun, Uttarakhand<br>{e(why)} '
            f'<a href="{SITE}/account#prefs" style="color:#7A8A9C">Change which emails you get</a>.</td></tr></table>'
            f'</td></tr></table></body></html>')

def kicker(t): return f'<p style="margin:0 0 6px;font-size:13px;font-weight:700;letter-spacing:.4px;color:{C["teal"]}">{e(t).upper()}</p>'
def h1(t): return f'<h1 style="margin:0 0 10px;font-size:26px;line-height:32px;font-weight:800;color:{C["ink"]}">{e(t)}</h1>'
def para(t, size=16, color=None): return f'<p style="margin:0 0 18px;font-size:{size}px;line-height:{size + 8}px;color:{color or C["muted"]}">{t}</p>'
def button(label, url):
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 4px"><tr><td style="border-radius:12px;background:{C["cyan"]}">'
            f'<a href="{e(url)}" style="display:inline-block;padding:14px 22px;font-family:{FONT};font-size:15px;font-weight:700;color:{C["night"]};text-decoration:none;border-radius:12px">{e(label)}</a></td></tr></table>')

def mon(iso): return datetime.date.fromisoformat(iso).strftime('%b')
def days_to(iso): return (datetime.date.fromisoformat(iso) - TODAY).days
def day_text(n): return 'Today' if n == 0 else 'Tomorrow' if n == 1 else f'{n} days'

def exam_card(x, extra=''):
    has_day = (x.get('label') or '')[:1].isdigit()
    top, bot = (str(int(x['date'][8:10])), mon(x['date'])) if has_day else (mon(x['date']), x['date'][:4])
    n = days_to(x['date'])
    count = f'<div style="font-size:22px;line-height:24px;font-weight:800;color:{"#B45309" if n <= 30 else C["ink"]}">{n}</div><div style="font-size:12px;color:{C["muted"]}">days</div>' if n > 1 else \
            f'<div style="font-size:15px;font-weight:800;color:#B45309">{day_text(n) if n >= 0 else "Done"}</div>'
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 10px;border:1px solid {C["line"]};border-radius:14px"><tr>'
            f'<td width="64" valign="top" style="padding:14px 0 14px 14px;width:64px"><div style="width:52px;border-radius:12px;background:{C["sky"]};text-align:center;padding:8px 0">'
            f'<div style="font-size:{20 if has_day else 15}px;line-height:22px;font-weight:800;color:{C["ink"]}">{e(top)}</div><div style="font-size:11px;font-weight:700;color:{C["teal"]}">{e(bot)}</div></div></td>'
            f'<td valign="top" style="padding:14px 10px;font-family:{FONT}"><div style="font-size:15px;line-height:20px;font-weight:700;color:{C["ink"]}">{e(x["exam"])}</div>'
            f'<div style="font-size:13px;line-height:19px;color:{C["muted"]};margin-top:3px">{e(STATUS.get(x.get("status"), ""))} · {e(x.get("label"))}</div>{extra}'
            f'<div style="font-size:13px;margin-top:6px"><a href="{e(x.get("site"))}" style="color:{C["teal"]};font-weight:700">Official site</a></div></td>'
            f'<td width="64" valign="top" align="right" style="padding:14px 14px 14px 0;font-family:{FONT};width:64px">{count}</td></tr></table>')

def deadline_line(x):
    if not x.get('deadline'): return ''
    n = days_to(x['deadline'])
    if n < 0: return ''
    return f'<div style="font-size:13px;line-height:19px;color:#9A3412;font-weight:700;margin-top:3px">{e(x.get("deadline_label"))} · {day_text(n)} left</div>'


# ---------------------------------------------------------------- data
def load_exams(ref=None):
    if ref is None:
        return json.load(open(os.path.join(ROOT, 'data/exams.json')))
    try:
        return json.loads(subprocess.run(['git', 'show', f'{ref}:data/exams.json'], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    except Exception:
        return None

def load_posts():
    import importlib
    return [{'slug': p['slug'], 'title': p['h1'], 'desc': p['desc']} for p in importlib.import_module('content_blog').POSTS]


class FirestoreDB:
    def __init__(self):
        import firebase_admin
        from firebase_admin import credentials, firestore
        firebase_admin.initialize_app(credentials.Certificate(json.loads(os.environ['FIREBASE_SA'])))
        self.fs, self.db = firestore, firestore.client()
    def users(self): return [dict(d.to_dict(), uid=d.id) for d in self.db.collection('users').stream()]
    def get(self, col, id_):
        d = self.db.collection(col).document(id_).get(); return d.to_dict() if d.exists else None
    def set(self, col, id_, data, merge=True): self.db.collection(col).document(id_).set(data, merge=merge)
    def add(self, col, data): self.db.collection(col).add(data)
    def query(self, col, field, value): return [dict(d.to_dict(), id=d.id) for d in self.db.collection(col).where(field, '==', value).stream()]
    def delete(self, col, id_): self.db.collection(col).document(id_).delete()
    def ordered(self, col, limit): return [dict(d.to_dict(), id=d.id) for d in self.db.collection(col).order_by('created').limit(limit).stream()]
    def now(self): return self.fs.SERVER_TIMESTAMP


# ---------------------------------------------------------------- sending with a daily limit; overflow waits in mailqueue
class Mailer:
    def __init__(self, db):
        self.db, self.day = db, TODAY.isoformat()
        self.count = (db.get('stats', 'mail-' + self.day) or {}).get('sent', 0)
        self.sent = self.queued = 0
        self.blocked = False
    def room(self): return not self.blocked and self.count < DAILY_LIMIT
    def send(self, to, subject, html_, text, tag, queue_ok=True):
        queue_ok = queue_ok and WRITE
        if not self.room():
            if queue_ok:
                self.db.add('mailqueue', {'to': to, 'subject': subject, 'html': html_, 'text': text, 'tag': tag, 'created': self.db.now()}); self.queued += 1
            return False
        dest = TEST_TO or to
        if DRY:
            print(f'  [dry] {tag:<12} -> {dest}: {subject}')
        else:
            body = {'sender': FROM, 'replyTo': REPLY_TO, 'to': [{'email': dest}], 'subject': subject, 'htmlContent': html_, 'textContent': text,
                    'tags': [tag], 'headers': {'List-Unsubscribe': f'<{SITE}/account#prefs>'}}
            req = urllib.request.Request('https://api.brevo.com/v3/smtp/email', data=json.dumps(body).encode(), method='POST',
                                         headers={'api-key': os.environ['BREVO_KEY'], 'content-type': 'application/json', 'accept': 'application/json'})
            try:
                urllib.request.urlopen(req, timeout=30).read()
            except Exception as x:
                detail = x.read().decode(errors='replace')[:300] if hasattr(x, 'read') else ''
                print(f'  ! Brevo refused {tag} to {to}: {x} {detail}')
                if queue_ok: self.db.add('mailqueue', {'to': to, 'subject': subject, 'html': html_, 'text': text, 'tag': tag, 'created': self.db.now()}); self.queued += 1
                self.blocked = True             # stop this run; the rest waits for the next one
                return False
        self.count += 1; self.sent += 1
        return True
    def close(self):
        if WRITE: self.db.set('stats', 'mail-' + self.day, {'sent': self.count, 'day': self.day})
        print(f'sent {self.sent}, queued {self.queued}, total today {self.count}/{DAILY_LIMIT}')


# ---------------------------------------------------------------- who gets what
def on(u, pref): return (u.get('notify') or {}).get(pref, True) is not False

def recipients(users, exam_ids, pref):
    """{email: {'name', 'child' (None for students), 'exams': set}} for students following the exams, plus their linked parents."""
    by_uid = {u['uid']: u for u in users}
    out = {}
    for s in users:
        if s.get('role') != 'student': continue
        hit = set(s.get('exams') or []) & set(exam_ids)
        if not hit: continue
        if on(s, pref) and s.get('email'):
            out.setdefault(s['email'], {'name': s.get('name', ''), 'child': None, 'exams': set()})['exams'] |= hit
        for pid in s.get('parents') or []:
            p = by_uid.get(pid)
            if p and on(p, pref) and p.get('email'):
                out.setdefault(p['email'], {'name': p.get('name', ''), 'child': s.get('name', ''), 'exams': set()})['exams'] |= hit
    return out

def first(name): return (name or '').split(' ')[0] or 'there'


# ---------------------------------------------------------------- 1. exam changes (instant)
FIELDS = [('date', 'Date'), ('label', 'Date'), ('status', 'Status'), ('deadline_label', 'Registration deadline')]

def diff_exams(old, new):
    o = {x.get('id'): x for x in old or [] if x.get('id')}
    changes = {}
    for x in new:
        y = o.get(x.get('id'))
        if not y: continue
        rows, seen = [], set()
        for f, label in FIELDS:
            a, b = y.get(f), x.get(f)
            if a == b or label in seen: continue
            if f == 'date' and y.get('label') != x.get('label'): continue     # the label row says it better
            if f == 'status': a, b = STATUS.get(a, a), STATUS.get(b, b)
            rows.append((label, a or '—', b or '—')); seen.add(label)
        if rows: changes[x['id']] = (x, rows)
    return changes

def send_changes(db, mailer, users, changes):
    if not changes: print('no exam changes'); return
    for email, r in recipients(users, list(changes), 'instant').items():
        items = [changes[i] for i in changes if i in r['exams']]
        title = items[0][0]['exam'] if len(items) == 1 else f'{len(items)} of your exams'
        who = f'{r["child"]}’s' if r['child'] else 'your'
        inner = kicker('Exam update') + h1(f'{title} changed') + para(f'Hi {e(first(r["name"]))}, there’s an update to {e(who)} exam plan. Here’s what changed:')
        for x, rows in items:
            tbl = ''.join(f'<tr><td style="padding:6px 0;font-size:13px;color:{C["muted"]};width:38%">{e(l)}</td><td style="padding:6px 0;font-size:14px;color:{C["ink"]}">'
                          f'<span style="text-decoration:line-through;color:#8A99AA">{e(a)}</span><br><b>{e(b)}</b></td></tr>' for l, a, b in rows)
            inner += exam_card(x, deadline_line(x) + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;border-top:1px solid {C["line"]}">{tbl}</table>')
        inner += para('Always check the official site before you apply.', 13) + button('See all your exams', SITE + '/account')
        subj = f'Update: {title} has changed' if len(items) == 1 else f'Updates to {len(items)} of your exams'
        text = f'Hi {first(r["name"])}, ' + '; '.join(f'{x["exam"]}: ' + ', '.join(f'{l} {a} -> {b}' for l, a, b in rows) for x, rows in items) + f'. See {SITE}/account'
        pre = '; '.join(f'{x["exam"]}: ' + ', '.join(f'{l.lower()} now {b}' for l, a, b in rows) for x, rows in items)
        mailer.send(email, subj, shell(pre, inner), text, 'exam-change')


# ---------------------------------------------------------------- 2. deadline reminders (7 days and 1 day before)
def send_reminders(db, mailer, users, exams):
    due = {x['id']: x for x in exams if x.get('id') and x.get('deadline') and days_to(x['deadline']) in (7, 1)}
    if not due: print('no deadlines 7 or 1 day away'); return
    for email, r in recipients(users, list(due), 'reminders').items():
        items = sorted((due[i] for i in r['exams']), key=lambda x: x['deadline'])
        n = min(days_to(x['deadline']) for x in items)
        when = 'tomorrow' if n == 1 else 'in 7 days'
        name = items[0]['exam'] if len(items) == 1 else f'{len(items)} exams'
        who = f'{e(r["child"])} has' if r['child'] else 'You have'
        inner = kicker('Deadline reminder') + h1(f'Registration closes {when}') + para(f'Hi {e(first(r["name"]))}, {who} {"a deadline" if len(items) == 1 else "deadlines"} coming up. Apply on the official site before it closes.')
        inner += ''.join(exam_card(x, deadline_line(x)) for x in items) + button('See all your exams', SITE + '/account')
        subj = f'{name}: registration closes {when}'
        text = f'Hi {first(r["name"])}, ' + '; '.join(f'{x["exam"]}: {x.get("deadline_label")}' for x in items) + f'. Official sites and your exams: {SITE}/account'
        pre = ' · '.join(f'{x["exam"]}: {x.get("deadline_label")}' for x in items)
        mailer.send(email, subj, shell(pre, inner), text, 'reminder')


# ---------------------------------------------------------------- 3. Sunday summary
def send_digest(db, mailer, users, exams, new_guides):
    by_id = {x['id']: x for x in exams if x.get('id')}
    by_uid = {u['uid']: u for u in users}
    for u in users:
        if not u.get('email') or not on(u, 'digest'): continue
        subject = u
        if u.get('role') == 'parent':
            kids = [s for s in users if s.get('role') == 'student' and u['uid'] in (s.get('parents') or [])]
            if not kids: continue
            subject = kids[0]
        ex = sorted((by_id[i] for i in subject.get('exams') or [] if i in by_id and days_to(by_id[i]['date']) >= 0), key=lambda x: x['date'])
        if not ex and not new_guides: continue
        whose = 'your' if subject is u else f'{e(first(subject.get("name")))}’s'
        inner = kicker('Your Sunday summary') + h1(f'Hi {first(u.get("name"))}, here’s {whose} week ahead' if subject is u else f'Hi {first(u.get("name"))}, here’s {first(subject.get("name"))}’s week ahead')
        soon = [x for x in ex if x.get('deadline') and 0 <= days_to(x['deadline']) <= 21]
        if soon:
            inner += para(f'<b style="color:#9A3412">Deadlines in the next 3 weeks:</b> ' + ', '.join(f'{e(x["exam"])} ({e(x["deadline_label"])})' for x in soon), 15, C['ink'])
        if ex:
            inner += f'<p style="margin:6px 0 10px;font-size:15px;font-weight:700;color:{C["ink"]}">Countdown</p>' + ''.join(exam_card(x, deadline_line(x)) for x in ex[:6])
        if new_guides:
            inner += f'<p style="margin:22px 0 10px;font-size:15px;font-weight:700;color:{C["ink"]}">New on MyUniMentor this week</p>' + ''.join(
                f'<p style="margin:0 0 12px;font-size:14px;line-height:20px"><a href="{SITE}/{e(g["slug"])}" style="color:{C["teal"]};font-weight:700">{e(g["title"])}</a><br><span style="color:{C["muted"]}">{e(g["desc"])}</span></p>' for g in new_guides[:4])
        inner += button('Open your dashboard', SITE + '/account')
        subj = f'Your week ahead: {ex[0]["exam"]} in {day_text(days_to(ex[0]["date"]))}' if ex else 'New guides on MyUniMentor this week'
        text = 'Countdown: ' + '; '.join(f'{x["exam"]} {x.get("label")}' for x in ex[:6]) + f'. {SITE}/account'
        bits = [f'{len(soon)} deadline{"s" if len(soon) != 1 else ""} in the next 3 weeks' if soon else 'No deadlines in the next 3 weeks', f'{len(ex)} exam{"s" if len(ex) != 1 else ""} on the countdown' if ex else '']
        if new_guides: bits.append(f'{len(new_guides)} new guide{"s" if len(new_guides) != 1 else ""}')
        mailer.send(u['email'], subj, shell(' · '.join(b for b in bits if b), inner), text, 'digest')


# ---------------------------------------------------------------- 4. announcements (written or approved by an admin in /admin)
def audience(users, a):
    aud = a.get('audience') or {}
    role, streams, classes = aud.get('role', 'all'), set(aud.get('streams') or []), set(aud.get('classes') or [])
    by_parent = {}
    for s in users:
        if s.get('role') == 'student':
            for pid in s.get('parents') or []: by_parent.setdefault(pid, []).append(s)
    out = []
    for u in users:
        if not u.get('email') or u.get('role') not in ('student', 'parent'): continue
        if role != 'all' and u['role'] != role: continue
        if not any(on(u, k) for k in ('instant', 'reminders', 'digest')): continue     # turned every email off
        look = [u] if u['role'] == 'student' else by_parent.get(u['uid'], [])
        if streams and not any(s.get('stream') in streams for s in look): continue
        if classes and not any(s.get('cls') in classes for s in look): continue
        out.append(u)
    return out

def send_announcements(db, mailer, users):
    for a in db.query('announcements', 'status', 'approved'):
        people = audience(users, a)
        done = set(a.get('sentTo') or [])
        paras = ''.join(para(e(p).replace('\n', '<br>'), 16) for p in (a.get('body') or '').split('\n\n') if p.strip())
        for u in people:
            if u['email'] in done: continue
            inner = kicker('From MyUniMentor') + h1(a.get('subject', '')) + para(f'Hi {e(first(u.get("name")))},') + paras
            if a.get('cta_url'): inner += button(a.get('cta_label') or 'Find out more', a['cta_url'])
            pre = (a.get('body') or '').split('\n')[0][:140]
            if not mailer.send(u['email'], a['subject'], shell(pre, inner), (a.get('body') or '') + ' ' + (a.get('cta_url') or ''), 'announcement', queue_ok=False):
                break                                    # out of room today: carry on next run
            done.add(u['email'])
        finished = all(u['email'] in done for u in people)
        if not WRITE: continue
        db.set('announcements', a['id'], {'sentTo': sorted(done), 'sentCount': len(done), 'status': 'sent' if finished else 'approved',
                                          **({'sentAt': db.now()} if finished else {})})
        print(f'announcement {a["id"]}: {len(done)}/{len(people)}')


# ---------------------------------------------------------------- new guides -> draft announcement for an admin to approve
def track_guides(db):
    posts, meta = load_posts(), db.get('meta', 'guides') or {}
    seen = meta.get('seen') or {}
    fresh = [p for p in posts if p['slug'] not in seen]
    if fresh and WRITE:
        for p in fresh: seen[p['slug']] = TODAY.isoformat()
        db.set('meta', 'guides', {'seen': seen})
        if meta:   # the very first run only records what exists
            for p in fresh:
                db.add('announcements', {'subject': f'New guide: {p["title"]}', 'body': p['desc'] + '\n\nRead it free on myunimentor.in.',
                                         'cta_label': 'Read the guide', 'cta_url': f'{SITE}/{p["slug"]}', 'audience': {'role': 'all'},
                                         'status': 'draft', 'auto': True, 'created': db.now()})
                print('draft announcement for new guide', p['slug'])
    week = (TODAY - datetime.timedelta(days=7)).isoformat()
    return [p for p in posts if seen.get(p['slug'], '') > week]


def drain_queue(db, mailer):
    for m in db.ordered('mailqueue', 200):
        if not mailer.room(): break
        if mailer.send(m['to'], m['subject'], m['html'], m.get('text', ''), m.get('tag', 'queued'), queue_ok=False):
            if WRITE: db.delete('mailqueue', m['id'])


def main(mode, db=None):
    db = db or FirestoreDB()
    mailer, users, exams = Mailer(db), db.users(), load_exams()
    print(f'{mode} · {NOW:%Y-%m-%d %H:%M} IST · {len(users)} accounts{" · DRY RUN" if DRY else ""}{" · test to " + TEST_TO if TEST_TO else ""}')
    try:
        if mode == 'changes':
            before = os.environ.get('BEFORE', '')
            old = load_exams(before if before and set(before) != {'0'} else 'HEAD~1')
            send_changes(db, mailer, users, diff_exams(old, exams))
            track_guides(db)
        else:
            drain_queue(db, mailer)
            send_announcements(db, mailer, users)
            jobs = db.get('stats', 'jobs-' + TODAY.isoformat()) or {}
            if (NOW.hour >= 8 and not jobs.get('daily')) or not WRITE:
                new_guides = track_guides(db)
                send_reminders(db, mailer, users, exams)
                if TODAY.weekday() == 6 or not WRITE: send_digest(db, mailer, users, exams, new_guides)
                if WRITE: db.set('stats', 'jobs-' + TODAY.isoformat(), {'daily': True})
    finally:
        mailer.close()


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'scheduled')
