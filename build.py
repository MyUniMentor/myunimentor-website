#!/usr/bin/env python3
"""Builds the MyUniMentor site from data/*.json into plain HTML pages.
Add a school or university to the JSON files, drop its logo into assets/logos/, run this."""
import glob, json, re, html, os, math, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
D = lambda f: json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8'))
UNIS = sorted(D('universities.json'), key=lambda u: u['name'].lower().replace('the ', ''))
SCHOOLS = sorted(D('schools.json'), key=lambda s: s['name'].lower().replace('the ', '', 1) if s['name'].startswith('The ') else s['name'].lower())
SCHOOLS = sorted(D('schools.json'), key=lambda s: s['name'].lower())
e = html.escape

def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower().replace("'", '')).strip('-')

def initials(name):
    first = name.split()[0]
    if len(first) >= 2 and first.replace('-', '').isupper():
        return first[:7]
    words = [w for w in re.split(r'[\s.]+', name) if w and w[0].isalpha() and w.lower() not in ('of', 'the', 'and')]
    return ''.join(w[0] for w in words[:3]).upper()

def logo(kind, item, cls='logo'):
    """Logo tile: shows the logo file if present, otherwise a clean monogram."""
    s = slug(item['name'])
    label = item.get('short') or item['name']
    return (f'<span class="{cls}" data-initials="{e(initials(item.get("short") or item["name"]))}">'
            f'<img src="assets/logos/{kind}/{s}.webp" alt="{e(item["name"])} logo" width="200" height="200" loading="lazy" decoding="async" onerror="this.remove()"></span>')

# Sun rays from the logo, fanning out from the bottom centre (used as hero texture)
def rays_svg(n=23, color='%2311BDDE'):
    lines = []
    for i in range(n):
        a = math.pi * (i + 1) / (n + 1)
        x1, y1 = 600 - 260 * math.cos(a), 640 - 260 * math.sin(a)
        x2, y2 = 600 - 900 * math.cos(a), 640 - 900 * math.sin(a)
        lines.append(f"M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}")
    return ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 640' preserveAspectRatio='xMidYMax slice'%3E"
            f"%3Cpath d='{' '.join(lines)}' stroke='{color}' stroke-width='2' stroke-linecap='round' fill='none'/%3E%3C/svg%3E")

SHOW_CAREER_CHECK = True   # adaptive career check, live since 20 Nov 2026
SHOW_GUIDE = False          # flip to True when the Class 12 guide is ready
SHOW_LEGAL = False          # flip to True after the lawyer reviews Privacy Policy and Terms
SHOW_ACCOUNTS = os.environ.get('SHOW_ACC', '1') == '1'   # student and parent accounts: "Log in" in the header, /account page, Save buttons
ACCOUNT_TEST = False   # True builds /account even when SHOW_ACCOUNTS is off (hidden, unlinked, noindex)
# Public Firebase web config (safe to publish) and the Apps Script URL that sends login codes.
ACCOUNT = {'authUrl': 'https://script.google.com/macros/s/AKfycbzKTnZKtIM1WRjTqRlmwSk7ZIHSqvNP3pi4nhvsLKx3mP7x7zVyR7kWnPshJho_RV1mpw/exec', 'firebase': {
    'apiKey': 'AIzaSyAI8nojG3Q_4VlkKqN2B2nH1UlJZFkG_Go', 'authDomain': 'myunimentor-web.firebaseapp.com', 'projectId': 'myunimentor-web',
    'storageBucket': 'myunimentor-web.firebasestorage.app', 'messagingSenderId': '817646080151', 'appId': '1:817646080151:web:343bcb2c1b62d9a2d699d2'}}
NOINDEX = {'account.html', 'admin.html', 'test.html'}
SHOW_PSY = True        # ₹99 psychometric test: landing page /psychometric-test, the test itself at /test (noindex)
PSY = {'price': 99, 'payLive': False}   # payLive: True only after Razorpay is activated and its keys are in the accounts Apps Script

NAV = [
    ('Home', 'index.html', None),
    ('About', 'about.html', None),
    ('Services', 'services-students.html', [
        ('For students & parents', 'services-students.html', 'Counselling and admissions guidance'),
        ('For schools', 'services-schools.html', 'Free seminars and career fairs'),
        ('For universities', 'services-universities.html', 'Admission and outreach support')]),
    ('Career Summit', 'career-summit.html', None),
    ('Our network', 'network.html', [
        ('Partner schools', 'network.html#schools', '12 schools in Dehradun and Saharanpur'),
        ('Partner universities', 'network.html#universities', '{UNI_COUNT} universities across India'),
        ('Letters of recommendation', 'network.html#lors', 'What our schools say'),
        ('Testimonials', 'testimonials.html', 'Students, parents and schools')]),
    ('Resources', 'exam-calendar.html', [
        ('Exam calendar 2027', 'exam-calendar.html', 'JEE, NEET, CUET, CLAT and more'),
        ('Board date sheets 2027', 'class-12-board-exams-2027.html', 'CBSE, ISC and ICSE, every subject'),
        ('Free career check', 'career-check.html', 'About 4 minutes, built around your stream'),
        ('Psychometric test', 'psychometric-test.html', '25 minutes, with a detailed report'),
        ('Free Class 12 guide', 'free-guide.html', 'Download the PDF'),
        ('Course guides', 'courses.html', 'BBA, B.Tech, Law, Design and more'),
        ('Blog', 'blog.html', 'Guides and articles')]),
]
for _grp in NAV:
    if _grp[2]:
        _grp[2][:] = [x for x in _grp[2] if not ((x[1] == 'career-check.html' and not SHOW_CAREER_CHECK) or (x[1] == 'free-guide.html' and not SHOW_GUIDE) or (x[1] == 'psychometric-test.html' and not SHOW_PSY))]

def header(active):
    items = []
    for label, href, sub in NAV:
        cur = ' aria-current="page"' if label == active else ''
        if sub:
            subs = ''.join(f'<li><a href="{h}"><strong>{e(l)}</strong><span>{e(d)}</span></a></li>' for l, h, d in sub)
            items.append(f'<li class="has-sub"><button class="sub-toggle" aria-expanded="false"{cur}>{e(label)}<svg viewBox="0 0 12 8" aria-hidden="true"><path d="M1 1.5l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg></button>'
                         f'<ul class="sub">{subs}</ul></li>')
        else:
            items.append(f'<li><a href="{href}"{cur}>{e(label)}</a></li>')
    return f'''<header class="site-header">
  <div class="wrap header-inner">
    <a href="index.html" class="brand" aria-label="MyUniMentor home"><img src="assets/img/logo-horizontal-dark.webp" alt="MyUniMentor" width="191" height="52"></a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav id="nav" class="nav" aria-label="Main">
      <ul class="nav-list">{''.join(items)}</ul>
      {'<a href="account.html" class="nav-account" aria-label="Log in or open your account">Log in</a>' if SHOW_ACCOUNTS else ''}<a href="contact.html" class="btn btn-small">Book free counselling</a>
    </nav>
  </div>
</header>'''

FOOTER = '''<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <img src="assets/img/logo-horizontal-light.webp" alt="MyUniMentor" width="191" height="52" loading="lazy" decoding="async">
      <p class="foot-tag">Right Guidance. Right Fit. Right University.</p>
      <p class="foot-legal">MyUniMentor Edtech LLP<br>Dehradun, Uttarakhand 248001</p>
    </div>
    <nav aria-label="Services"><h2 class="foot-h">Services</h2>
      <a href="services-students.html">For students &amp; parents</a><a href="services-schools.html">For schools</a><a href="services-universities.html">For universities</a><a href="career-summit.html">Career Summit</a></nav>
    <nav aria-label="Company"><h2 class="foot-h">Company</h2>
      <a href="about.html">About us</a><a href="omgarg.html">Om Garg, Founder</a><a href="network.html">Our network</a><a href="blog.html">Blog</a><a href="contact.html">Contact</a></nav>
    <nav aria-label="Locations"><h2 class="foot-h">Where we work</h2>
      <a href="career-counselling-dehradun.html">Career counselling in Dehradun</a><a href="career-counselling-saharanpur.html">Career counselling in Saharanpur</a><a href="career-counselling-roorkee.html">Roorkee (2027)</a><a href="career-counselling-rishikesh.html">Rishikesh (2027)</a></nav>
    <div><h2 class="foot-h">Get in touch</h2>
      <a href="tel:+917417557070">+91 74175 57070</a><a href="mailto:info@myunimentor.in">info@myunimentor.in</a>
      <div class="social">
        <a href="https://www.instagram.com/myunimentor.in" rel="noopener" target="_blank" aria-label="Instagram"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 8.2a3.2 3.2 0 1 1 0-6.4 3.2 3.2 0 0 1 0 6.4zM17.3 5.5a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zM21.9 7c-.1-1.6-.4-3-1.6-4.2S17.6 1.2 16 1.1C14.4 1 9.6 1 8 1.1 6.4 1.2 5 1.5 3.8 2.7S2.2 5.4 2.1 7C2 8.6 2 15.4 2.1 17c.1 1.6.4 3 1.6 4.2s2.6 1.5 4.2 1.6c1.6.1 6.4.1 8 0 1.6-.1 3-.4 4.2-1.6s1.5-2.6 1.6-4.2c.1-1.6.1-8.4 0-10zm-2.1 12.5a3.3 3.3 0 0 1-1.8 1.8c-1.3.5-4.3.4-5.9.4s-4.6.1-5.9-.4a3.3 3.3 0 0 1-1.8-1.8c-.5-1.3-.4-4.3-.4-5.5s-.1-4.3.4-5.5a3.3 3.3 0 0 1 1.8-1.8C7.4 4.2 10.4 4.3 12 4.3s4.6-.1 5.9.4a3.3 3.3 0 0 1 1.8 1.8c.5 1.3.4 4.3.4 5.5s.1 4.2-.3 5.5z"/></svg></a>
        <a href="https://www.facebook.com/p/My-Uni-Mentor-61595547407499/" rel="noopener" target="_blank" aria-label="Facebook"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M14 8.5V6.8c0-.8.2-1.3 1.4-1.3H17V2.3c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2H7.5V12h2.8v9.8H14V12h2.8l.4-3.5H14z"/></svg></a>
        <a href="https://www.linkedin.com/company/myunimentor/" rel="noopener" target="_blank" aria-label="LinkedIn"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.5h4V21H3zM9.5 9.5h3.8v1.6h.1c.5-1 1.8-2 3.8-2 4 0 4.8 2.6 4.8 6V21h-4v-5.1c0-1.2 0-2.8-1.7-2.8s-2 1.3-2 2.7V21h-4z"/></svg></a>
      </div>
    </div>
  </div>
  <div class="wrap foot-base"><p>© 2026 MyUniMentor Edtech LLP. Built in Dehradun, for every student.</p><p><button type="button" class="tour-open">Quick tour of this site</button> · Dehradun, Uttarakhand, India</p></div>
  <div class="foot-mark" aria-hidden="true"><span data-t="MyUniMentor">MyUniMentor</span></div>
</footer>
<nav class="mbar" aria-label="Quick actions"><a href="tel:+917417557070"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>Call</a><a href="https://wa.me/917417557070" target="_blank" rel="noopener"><svg viewBox="0 0 32 32" aria-hidden="true"><path fill="currentColor" d="M16 3a13 13 0 0 0-11.2 19.6L3 29l6.6-1.7A13 13 0 1 0 16 3zm0 23.6a10.6 10.6 0 0 1-5.4-1.5l-.4-.2-3.9 1 1-3.8-.2-.4A10.6 10.6 0 1 1 16 26.6z"/></svg>WhatsApp</a><a href="contact.html" class="mbar-cta">Free session</a></nav>
<a class="wa" href="https://wa.me/917417557070?text=Hi%20MyUniMentor%2C%20I%27d%20like%20to%20know%20more%20about%20career%20counselling." target="_blank" rel="noopener" aria-label="Chat with us on WhatsApp">
  <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true"><path fill="currentColor" d="M16 3a13 13 0 0 0-11.2 19.6L3 29l6.6-1.7A13 13 0 1 0 16 3zm0 23.6a10.6 10.6 0 0 1-5.4-1.5l-.4-.2-3.9 1 1-3.8-.2-.4A10.6 10.6 0 1 1 16 26.6zm5.8-7.9c-.3-.2-1.9-.9-2.2-1s-.5-.2-.7.2-.8 1-1 1.2-.4.2-.7 0a8.7 8.7 0 0 1-4.3-3.8c-.3-.6.3-.5.9-1.7.1-.2 0-.4 0-.5l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6a1.2 1.2 0 0 0-.9.4 3.6 3.6 0 0 0-1.1 2.7 6.3 6.3 0 0 0 1.3 3.3 14.4 14.4 0 0 0 5.5 4.9c2 .9 2.8 1 3.9.8a3.2 3.2 0 0 0 2.1-1.5 2.6 2.6 0 0 0 .2-1.5c-.1-.1-.3-.2-.6-.4z"/></svg>
</a>
<dialog id="viewer" class="viewer" aria-label="Preview"><button class="viewer-close">Close</button><div class="viewer-body"></div></dialog>
<script src="assets/js/main.min.js?v={VER}" defer></script>'''

META = {
"index.html": [
"Career Counsellor for Students Across India | MyUniMentor",
"Talk to a career counsellor free: one-on-one, online or in person, anywhere in India. Help with your stream, course, entrance exams and university admissions."
],
"about.html": [
"About MyUniMentor: Our Story and Founder",
"Founded in Dehradun in 2026 by Om Garg, MyUniMentor brings organised career guidance to every school. Our story, what we do and where we're headed."
],
"services-students.html": [
"Free Career Counselling for Class 11–12 | MyUniMentor",
"Your first 1-on-1 career counselling session is free. Choose the right stream, course and university with MyUniMentor, Dehradun."
],
"services-schools.html": [
"Free Career Seminars for Schools | MyUniMentor",
"Free career guidance seminars for Class 11–12 and the School Career Guidance Summit, an in-school career fair, for schools in Dehradun and Saharanpur."
],
"services-universities.html": [
"University Outreach & Admission Support | MyUniMentor",
"Meet Class 11–12 students in partner schools across Dehradun and Saharanpur. Exhibit at the School Career Guidance Summit with {UNI_COUNT} universities."
],
"career-summit.html": [
"School Career Guidance Summit | MyUniMentor",
"MyUniMentor's in-school career fair: university stalls on the school campus, 12 schools in Dehradun and Saharanpur in October 2026. Watch the highlights."
],
"network.html": [
"Partner Universities & Schools | MyUniMentor",
"12 partner schools in Dehradun and Saharanpur and {UNI_COUNT} partner universities, including UPES, Graphic Era, Chandigarh University, LPU and Tulas."
],
"omgarg.html": [
"Om Garg | Founder of MyUniMentor, Career Counsellor",
"Om Garg is the founder of MyUniMentor, Dehradun. Career counsellor and speaker: 10,000+ students guided, 100+ seminars, 500+ one-on-one sessions."
],
"blog.html": [
"Career Guidance Blog for Class 11–12 | MyUniMentor",
"Practical guides for Class 11–12 students and parents on streams, courses, entrance exams like CUET, and choosing the right university."
],
"contact.html": [
"Contact MyUniMentor | Book Free Counselling",
"Call or WhatsApp +91 74175 57070 or email info@myunimentor.in to book free 1-on-1 counselling, a free school seminar or a university partnership."
],
"career-check.html": [
"Free Career Test for Class 9–12 | MyUniMentor",
"A free 4-minute career check for Class 9–12. Questions change with your stream and answers, then show the careers, courses and entrance exams that fit you."
],
"exam-calendar.html": [
"Entrance Exam Calendar 2027: JEE, NEET, CUET, CLAT",
"2027 dates for JEE Main, JEE Advanced, NEET, CUET, CLAT, NID DAT, NIFT, UCEED and IPMAT in one place, with official links and countdowns."
],
"free-guide.html": [
"Free Class 12 Decision Guide (PDF) | MyUniMentor",
"Download the free Class 12 Decision Guide: choose your stream and course, map entrance exams, shortlist universities and plan your Class 12 year."
],
"testimonials.html": [
"Testimonials: Students, Parents & Schools | MyUniMentor",
"What students, parents and school principals say about MyUniMentor's counselling, free seminars and the School Career Guidance Summit."
],
"career-counselling-dehradun.html": [
"Career Counselling in Dehradun | MyUniMentor",
"Free first 1-on-1 career counselling for Class 11–12 students in Dehradun. 9 partner schools, free seminars and the School Career Guidance Summit."
],
"career-counselling-saharanpur.html": [
"Career Counselling in Saharanpur | MyUniMentor",
"Free first 1-on-1 career counselling for Class 11–12 students in Saharanpur. Partner schools Alpine, Brownwood and St. Mary's."
],
"career-counselling-roorkee.html": [
"Career Counselling in Roorkee | MyUniMentor",
"Free first 1-on-1 career counselling for Class 11–12 students in Roorkee, online today. School programmes planned for 2027."
],
"career-counselling-rishikesh.html": [
"Career Counselling in Rishikesh | MyUniMentor",
"Free first 1-on-1 career counselling for Class 11–12 students in Rishikesh, online today. School programmes planned for 2027."
],
"privacy.html": [
"Privacy Policy | MyUniMentor",
"How MyUniMentor collects, uses and protects information shared through myunimentor.in, under India's Digital Personal Data Protection Act, 2023."
],
"terms.html": [
"Terms and Conditions | MyUniMentor",
"Terms for using myunimentor.in and for MyUniMentor's free first 1-on-1 career counselling session for Class 11–12 students."
]
}

import hashlib, rcssmin, rjsmin
_css = open(os.path.join(ROOT, 'assets/css/style.css')).read(); _js = open(os.path.join(ROOT, 'assets/js/main.js')).read(); _cjs = open(os.path.join(ROOT, 'assets/js/check.js')).read()
_tjs = open(os.path.join(ROOT, 'assets/js/tour.js')).read(); _ajs = open(os.path.join(ROOT, 'assets/js/account.js')).read()
_djs = open(os.path.join(ROOT, 'assets/js/admin.js')).read()
_sjs = open(os.path.join(ROOT, 'assets/js/ds.js')).read()
# The psychometric test reuses the career areas (courses, exams, lengths) from the career check, so both stay in step.
_cl = _cjs[_cjs.index('  const SCI = '):_cjs.index('  /* Activity cards')].strip()
_pjs = open(os.path.join(ROOT, 'assets/js/psy.js')).read().replace('/*@CL@*/', _cl)
VER = hashlib.md5((_css + _js + _cjs + _tjs + _ajs + _djs + _pjs + _sjs).encode()).hexdigest()[:8]
open(os.path.join(ROOT, 'assets/js/psy.min.js'), 'w').write('\n'.join(l.strip() for l in _pjs.splitlines() if l.strip() and not (l.strip().startswith('/*') and l.strip().endswith('*/'))))
open(os.path.join(ROOT, 'assets/js/account.min.js'), 'w').write('\n'.join(l.strip() for l in _ajs.splitlines() if l.strip() and not (l.strip().startswith('/*') and l.strip().endswith('*/'))))
open(os.path.join(ROOT, 'assets/js/admin.min.js'), 'w').write('\n'.join(l.strip() for l in _djs.splitlines() if l.strip() and not (l.strip().startswith('/*') and l.strip().endswith('*/'))))
open(os.path.join(ROOT, 'assets/js/ds.min.js'), 'w').write(rjsmin.jsmin(_sjs))
open(os.path.join(ROOT, 'assets/js/tour.min.js'), 'w').write('\n'.join(l.strip() for l in _tjs.splitlines() if l.strip() and not (l.strip().startswith('/*') and l.strip().endswith('*/'))))
# rjsmin squeezes spaces inside template strings, so check.js is only trimmed
open(os.path.join(ROOT, 'assets/js/check.min.js'), 'w').write('\n'.join(l.strip() for l in _cjs.splitlines() if l.strip() and not (l.strip().startswith('/*') and l.strip().endswith('*/'))))
def split_css(css):
    """Rules used only by /account, /admin and /test go to app.css, so public pages load less CSS before showing anything."""
    APP = re.compile(r'(\.acct|\.adm|#adm|\.psy)')
    def only_app(sel): return all(APP.search(x) for x in sel.split(',') if x.strip())
    def rules(text):
        out, i, n = [], 0, len(text)
        while i < n:
            j = text.find('{', i)
            if j < 0: break
            sel, depth, k = text[i:j].strip(), 1, j + 1
            while depth and k < n:
                depth += {'{': 1, '}': -1}.get(text[k], 0); k += 1
            out.append((sel, text[j + 1:k - 1])); i = k
        return out
    core, app = [], []
    for sel, body in rules(rcssmin.cssmin(css)):
        if sel.startswith('@media') or sel.startswith('@supports'):
            inner = rules(body); c = [f'{a}{{{b}}}' for a, b in inner if not only_app(a)]; a_ = [f'{a}{{{b}}}' for a, b in inner if only_app(a)]
            if c: core.append(f'{sel}{{{"".join(c)}}}')
            if a_: app.append(f'{sel}{{{"".join(a_)}}}')
        elif sel.startswith('@') or not only_app(sel): core.append(f'{sel}{{{body}}}')
        else: app.append(f'{sel}{{{body}}}')
    return ''.join(core), ''.join(app)
_core_css, _app_css = split_css(_css)
open(os.path.join(ROOT, 'assets/css/style.min.css'), 'w').write(_core_css)
open(os.path.join(ROOT, 'assets/css/app.min.css'), 'w').write(_app_css)
FORM_URL = 'https://script.google.com/macros/s/AKfycbwcvPVe57-G-AyYdHVcCyGneK9waUp5nRnvPbH8xneLtcKcp0AnnB0sjrx2DaRnrbZ4kw/exec'   # Google Apps Script web app URL for the lead forms
open(os.path.join(ROOT, 'assets/js/main.min.js'), 'w').write((f"window.MUM_FORM_URL='{FORM_URL}';" if FORM_URL else '') + rjsmin.jsmin(_js))

CLEAN_URLS = os.environ.get('CLEAN_URLS', '1') == '1'   # 1 = /about style links (GitHub Pages); 0 = about.html (local preview)

def clean_urls(h):
    if not CLEAN_URLS: return h
    h = re.sub(r'(href|data-href)="index\.html(#[^"]*)?"', lambda m: f'{m.group(1)}="/{m.group(2) or ""}"', h)
    h = re.sub(r'(href)="([a-z0-9-]+)\.html(\?[^"#]*)?(#[^"]*)?"', lambda m: f'{m.group(1)}="/{m.group(2)}{m.group(3) or ""}{m.group(4) or ""}"', h)
    h = re.sub(r'((?:src|href|data-src|srcset|content)=")assets/', r'\1/assets/', h)
    h = re.sub(r'(href=")(favicon\.(?:ico|svg)|site\.webmanifest)"', r'\1/\2"', h)
    return h

def slim_html(h):
    h = re.sub(r'\n[ \t]+', '\n', h)
    return re.sub(r'\n{2,}', '\n', h)

OG_KICK = {'exam-calendar': 'Exam calendar', 'career-check': 'Free career check', 'psychometric-test': 'Psychometric test', 'courses': 'Course guides',
           'blog': 'Guides and articles', 'about': 'About MyUniMentor', 'omgarg': 'Founder, MyUniMentor', 'contact': 'Contact', 'network': 'Our network',
           'testimonials': 'Testimonials', 'career-summit': 'School Career Guidance Summit', 'services-students': 'For students and parents',
           'services-schools': 'For schools', 'services-universities': 'For universities'}
def og_kicker(slug):
    if slug in OG_KICK: return OG_KICK[slug]
    if slug.startswith('career-counselling-'): return 'Career counselling'
    tags = {x['slug']: x['tag'] for x in globals().get('POSTS', [])}
    if slug in tags: return tags[slug]
    if any(c.get('slug') == slug for c in globals().get('COURSES', [])): return 'Course guide'
    return 'MyUniMentor'

def head_social(fname, title, schema):
    """Share image, its alt text and article tags for one page."""
    slug = fname.replace('.html', ''); img = None
    if fname != 'index.html' and fname not in NOINDEX and fname != '404.html':
        t = re.sub(r'\s*\|\s*MyUniMentor$', '', title); t = re.sub(r'^MyUniMentor:\s*', '', t)
        try:
            sys.path.insert(0, os.path.join(ROOT, 'tools')); import og
            img = og.og_image(slug, t, og_kicker(slug))
        except Exception as ex:
            print('share images off:', ex)
    img = img or 'https://myunimentor.in/assets/img/og-image.jpg'
    alt = 'MyUniMentor: Right Guidance. Right Fit. Right University.' if img.endswith('og-image.jpg') else title
    art = ''
    if '"@type": "Article"' in schema:
        pub = re.search(r'"datePublished": "([^"]+)"', schema); mod = re.search(r'"dateModified": "([^"]+)"', schema)
        art = (f'<meta property="article:published_time" content="{pub.group(1)}">' if pub else '') + (f'<meta property="article:modified_time" content="{mod.group(1)}">' if mod else '') + f'<meta property="article:section" content="{e(og_kicker(slug))}">'
    return img, alt, art

def page(fname, title, desc, active, body, schema=''):
    title, desc = META.get(fname, (title, desc))
    img, img_alt, art = head_social(fname, title, schema)
    doc = f'''<!DOCTYPE html>
<html lang="en-IN" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">{'<meta name="robots" content="noindex, nofollow">' if fname in NOINDEX else '<meta name="robots" content="max-image-preview:large, max-snippet:-1, max-video-preview:-1">'}
<link rel="canonical" href="https://myunimentor.in/{'' if fname == 'index.html' else fname.replace('.html', '')}">
<meta property="og:type" content="{'article' if art else 'website'}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">{art}
<meta property="og:image" content="{img}"><meta property="og:image:secure_url" content="{img}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:alt" content="{e(img_alt)}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:site_name" content="MyUniMentor"><meta property="og:locale" content="en_IN"><meta property="og:url" content="https://myunimentor.in/{'' if fname == 'index.html' else fname.replace('.html', '')}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{img}"><meta name="twitter:image:alt" content="{e(img_alt)}">
<link rel="icon" href="favicon.ico" sizes="48x48"><link rel="icon" type="image/png" sizes="96x96" href="assets/img/icon-v2-96.png"><link rel="icon" type="image/png" sizes="144x144" href="assets/img/icon-v2-144.png">
<link rel="icon" type="image/png" sizes="192x192" href="assets/img/icon-v2-192.png">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon-v2.png"><link rel="manifest" href="site.webmanifest"><meta name="theme-color" content="#0E2540">
<link rel="preload" href="assets/fonts/bricolage-grotesque-latin-800-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/figtree-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/style.min.css?v={VER}">{'<link rel="stylesheet" href="assets/css/app.min.css?v={VER}">' if fname in NOINDEX else ''}
<script type="speculationrules">{{"prefetch":[{{"where":{{"and":[{{"href_matches":"/*"}},{{"not":{{"href_matches":"/assets/*"}}}}]}},"eagerness":"moderate"}}]}}</script>
</head>
<body>
<script>document.documentElement.className="js"</script>
<div class="progress" aria-hidden="true"></div>
<a class="skip" href="#main">Skip to content</a>
{header(active)}
<main id="main">
{body}
</main>
{FOOTER}
{schema}
</body>
</html>
'''
    open(os.path.join(ROOT, fname), 'w', encoding='utf-8').write(slim_html(clean_urls(doc.replace('{VER}', VER).replace('{UNI_COUNT}', str(len(UNIS))))))

WEBSITE_SCHEMA = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "WebSite", "@id": "https://myunimentor.in/#website", "name": "MyUniMentor", "alternateName": ["My Uni Mentor"], "url": "https://myunimentor.in/", "inLanguage": "en-IN", "publisher": {"@id": "https://myunimentor.in/#org"}}) + '</script>'
ORG_SCHEMA = '''<script type="application/ld+json">{"@context":"https://schema.org","@type":"EducationalOrganization","@id":"https://myunimentor.in/#org","name":"MyUniMentor","alternateName":["My Uni Mentor","MyUniMentor Edtech LLP"],"description":"Career counselling and university admissions guidance for students across India, online and in person. Based in Dehradun, Uttarakhand.","disambiguatingDescription":"Indian career counselling and admissions guidance organisation at myunimentor.in, run by MyUniMentor Edtech LLP, Dehradun.","foundingDate":"2026","legalName":"MyUniMentor Edtech LLP","url":"https://myunimentor.in/","logo":"https://myunimentor.in/assets/img/logo-dark.png","slogan":"Right Guidance. Right Fit. Right University.","email":"info@myunimentor.in","telephone":"+91-7417557070","address":{"@type":"PostalAddress","addressLocality":"Dehradun","addressRegion":"Uttarakhand","postalCode":"248001","addressCountry":"IN"},"founder":{"@type":"Person","@id":"https://myunimentor.in/omgarg#person","name":"Om Garg","jobTitle":"Founder","url":"https://myunimentor.in/omgarg"},"areaServed":[{"@type":"Country","name":"India"},{"@type":"City","name":"Dehradun"},{"@type":"City","name":"Saharanpur"}],"knowsAbout":["Career counselling","Online career counselling","Psychometric career assessment","University admissions in India","Choosing a stream after Class 10","Entrance exams: JEE, NEET, CUET, CLAT","School career fairs"],"sameAs":["https://www.instagram.com/myunimentor.in","https://www.facebook.com/p/My-Uni-Mentor-61595547407499/","https://www.linkedin.com/company/myunimentor/","https://share.google/ocON7keUcOY0Q2Gak"]}</script>'''

ICONS = {
    'tools': '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="9" y="6" width="30" height="36" rx="5" fill="currentColor" opacity=".3"/><path d="M16 17h16M16 24h16M16 31h10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    'student': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 8 4 18l20 10 20-10L24 8z" fill="currentColor" opacity=".9"/><path d="M12 23v9c0 3 5.4 6 12 6s12-3 12-6v-9l-12 6-12-6z" fill="currentColor" opacity=".55"/><path d="M42 19v11" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>',
    'school': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 6 8 15v3h32v-3L24 6z" fill="currentColor" opacity=".9"/><path d="M11 20h5v16h-5zM21.5 20h5v16h-5zM32 20h5v16h-5z" fill="currentColor" opacity=".55"/><path d="M7 38h34v4H7z" fill="currentColor" opacity=".9"/></svg>',
    'uni': '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="20" r="12" fill="currentColor" opacity=".55"/><path d="M24 4v4M10 9l3 3M38 9l-3 3M4 20h4M40 20h4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><path d="M14 30h20l-2 12H16z" fill="currentColor" opacity=".9"/></svg>',
}

# ---------------- HOME ----------------

FREE_NOTE = ''

def faq_block(items, title='Frequently asked questions'):
    qs = ''.join(f'<details class="faq-item"><summary>{e(q)}</summary><div class="faq-a"><p>{a}</p></div></details>' for q, a in items)
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a)}} for q, a in items]}
    return (f'<section class="section faq"><div class="wrap faq-grid"><div><h2>{e(title)}</h2><p class="muted">Still unsure? Call or WhatsApp <a href="tel:+917417557070">+91 74175 57070</a>.</p></div>'
            f'<div class="faq-list">{qs}</div></div></section>'), f'<script type="application/ld+json">{json.dumps(schema)}</script>'

def crumbs_schema(trail):
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": "https://myunimentor.in/" + u} for i, (n, u) in enumerate(trail)]}) + '</script>'

def page_hero(title, sub, crumb, extra=''):
    return f'''<section class="page-hero" style="--rays:url(&quot;{rays_svg(19)}&quot;)">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a><span aria-hidden="true">/</span><span>{e(crumb)}</span></nav>
    <h1 class="split">{e(title)}</h1>
    <p class="page-sub">{sub}</p>
    {extra}
  </div>
</section>'''

def cta(title, sub, btn='Book a free session', href='contact.html'):
    return f'''<section class="cta-band" style="--rays:url(&quot;{rays_svg(13)}&quot;)">
  <div class="wrap cta-inner">
    <div><h2>{title}</h2><p>{sub}</p></div>
    <div class="hero-actions"><a href="{href}" class="btn btn-cyan btn-lg">{btn}</a><a href="tel:+917417557070" class="btn btn-outline-light btn-lg">Call +91 74175 57070</a></div>
  </div>
</section>'''

STUDENT_FORM = '''<form id="f-student" aria-labelledby="t-f1" class="lead-form" data-form="counselling">
  <div class="field"><label for="s-name">Student's name</label><input id="s-name" name="name" required autocomplete="name"></div>
  <div class="row">
    <div class="field"><label for="s-phone">Phone (WhatsApp)</label><input id="s-phone" name="phone" type="tel" inputmode="tel" pattern="[0-9+ ]{10,14}" required autocomplete="tel"></div>
    <div class="field"><label for="s-city">City</label><input id="s-city" name="city" required autocomplete="address-level2"></div>
  </div>
  <div class="row">
    <div class="field"><label for="s-class">Class</label><select id="s-class" name="class" required><option value="">Select</option><option>Class 11</option><option>Class 12</option></select></div>
    <div class="field"><label for="s-stream">Stream</label><select id="s-stream" name="stream" required><option value="">Select</option><option>Science (PCM)</option><option>Science (PCB)</option><option>Commerce</option><option>Humanities</option></select></div>
  </div>
  <label class="consent"><input type="checkbox" name="consent" required><span>I am a parent or guardian, or a student filling this with my parent's permission. I agree to be contacted by MyUniMentor about this session.</span></label>
  <label class="consent"><input type="checkbox" name="updates"><span>Optional: also send me updates about admissions and MyUniMentor's partner universities.</span></label>
  <button class="btn btn-full btn-lg" type="submit">Book my free session</button>
  <p class="form-status" role="status" aria-live="polite"></p>
</form>'''

PARTNER_FORM = '''<form id="f-partner" aria-labelledby="t-f2" class="lead-form" data-form="partnership" hidden>
  <div class="row">
    <div class="field"><label for="p-name">Your name</label><input id="p-name" name="name" required autocomplete="name"></div>
    <div class="field"><label for="p-role">Your role</label><input id="p-role" name="role" placeholder="Principal, Admissions Head…" required></div>
  </div>
  <div class="field"><label for="p-inst">School or university</label><input id="p-inst" name="institution" required autocomplete="organization"></div>
  <div class="row">
    <div class="field"><label for="p-phone">Phone</label><input id="p-phone" name="phone" type="tel" required autocomplete="tel"></div>
    <div class="field"><label for="p-email">Email</label><input id="p-email" name="email" type="email" required autocomplete="email"></div>
  </div>
  <div class="field"><label for="p-need">What are you looking for?</label><select id="p-need" name="interest" required><option value="">Select</option><option>A free career seminar at our school</option><option>The Career Summit at our school</option><option>A session with Om Garg</option><option>Exhibiting as a university</option><option>Admission and outreach support</option><option>Something else</option></select></div>
  <label class="consent"><input type="checkbox" name="consent" required><span>I agree to be contacted by MyUniMentor about this enquiry.</span></label>
  <button class="btn btn-full btn-lg" type="submit">Send enquiry</button>
  <p class="form-status" role="status" aria-live="polite"></p>
</form>'''

def form_card(default='student'):
    s_sel, p_sel = ('true', 'false') if default == 'student' else ('false', 'true')
    sf = STUDENT_FORM if default == 'student' else STUDENT_FORM.replace('data-form="counselling">', 'data-form="counselling" hidden>')
    pf = PARTNER_FORM if default != 'student' else PARTNER_FORM
    if default != 'student': pf = PARTNER_FORM.replace(' hidden>', '>')
    return f'''<div class="form-card" data-reveal>
  <div class="tabs" role="tablist" aria-label="Choose enquiry type">
    <button role="tab" id="t-f1" aria-selected="{s_sel}" aria-controls="f-student" {'tabindex="-1"' if s_sel == 'false' else ''}>I'm a student or parent</button>
    <button role="tab" id="t-f2" aria-selected="{p_sel}" aria-controls="f-partner" {'tabindex="-1"' if p_sel == 'false' else ''}>I'm from a school or university</button>
  </div>
  {sf}{pf}
</div>'''

def school_wall(limit=None):
    return ''.join(f'<li data-reveal style="--d:{i % 4}"><a href="network.html#schools">{logo("schools", s, "logo logo-round")}<span><strong>{e(s["name"])}</strong><small>{e(s["city"])}, {e(s["board"])}</small></span></a></li>' for i, s in enumerate(SCHOOLS[:limit]))

MEDIA = D('media.json')
PHOTOS = {x['slug']: x for x in D('photos.json')}

def photo_btn(slug, cls='photo', eager=False):
    x = PHOTOS[slug]
    cap = x['alt']
    return (f'<button class="{cls}" data-src="assets/photos/{slug}.webp" data-cap="{e(cap)}" aria-label="View photo: {e(cap)}">'
            f'<img src="assets/photos/{slug}-sm.webp" alt="{e(cap)}" width="{x["tw"]}" height="{x["th"]}" draggable="false"{"" if eager else " loading=" + chr(34) + "lazy" + chr(34)}></button>')

def gallery(slugs, cls='gallery'):
    return f'<ul class="{cls}" data-hs>' + ''.join(f'<li data-reveal style="--d:{i % 4}">{photo_btn(s)}</li>' for i, s in enumerate(slugs)) + '</ul>'

def hero_slides():
    city = {s['name']: s['city'] for s in SCHOOLS}
    picks = [('beverly-summit-hall', 'Career Summit'), ('saigrace-summit-corridor', 'Career Summit'), ('alpine-summit-hall', 'Career Summit'),
             ('olympus-summit-auditorium', 'Career Summit'), ('brooklyn-seminar-hall', 'Career seminar'), ('st-marys-summit-stall', 'Career Summit'),
             ('doon-world-summit-stalls', 'Career Summit')]
    imgs, dots = '', ''
    for i, (k, kind) in enumerate(picks):
        x = PHOTOS[k]; cap = f"{kind}, {x['school']}, {city.get(x['school'], '')}".rstrip(', ')
        src = f"assets/photos/{k}-sm.webp"
        imgs += (f'<img src="{src}" alt="" width="{x["tw"]}" height="{x["th"]}" fetchpriority="high" decoding="async" class="on" data-cap="{e(cap)}">' if i == 0
                 else f'<img data-src="{src}" alt="" width="{x["tw"]}" height="{x["th"]}" decoding="async" data-cap="{e(cap)}">')
        dots += f'<button class="hs-dot{" on" if i == 0 else ""}" aria-label="Photo {i + 1}" data-i="{i}"></button>'
    first = f"Career Summit, {PHOTOS[picks[0][0]]['school']}, {city.get(PHOTOS[picks[0][0]]['school'], '')}"
    return f'''<figure class="hero-photo hero-slides">{imgs}<figcaption><span class="live-dot"></span><span class="hs-cap">{e(first)}</span></figcaption><div class="hs-dots">{dots}</div></figure>'''

PRESS = [
    ("bharat-vichar-14oct-pinehall", "Dainik Bharat Vichar", "14 Oct 2026", "Pine Hall School hosts the School Career Guidance Summit"),
    ("bharat-vichar-15oct-olympus", "Dainik Bharat Vichar", "15 Oct 2026", "Career Guidance Summit at Olympus High, Dehradun"),
    ("bhartendu-olympus", "Bhartendu", "Oct 2026", "Career fair at Olympus High shows students the way"),
    ("bharat-vichar-11oct-stmarys-alpine", "Dainik Bharat Vichar", "11 Oct 2026", "Career fairs at St. Mary's and Alpine Public School, Saharanpur"),
    ("subah-suchna-alpine", "Subah Suchna", "Oct 2026", "Career fair at Alpine Public School, Saharanpur"),
    ("saral-express-brownwood", "Saral Express", "Oct 2026", "Career fair at Brownwood Public School, Saharanpur")]

PRESS_SIZE = {"bharat-vichar-11oct-stmarys-alpine": (560, 410), "bharat-vichar-14oct-pinehall": (514, 560), "bharat-vichar-15oct-olympus": (560, 308), "bhartendu-olympus": (560, 547), "saral-express-brownwood": (560, 387), "subah-suchna-alpine": (560, 379)}
def press_section(title="In the news", sub="Local press coverage of the School Career Guidance Summit, October 2026. Tap a clipping to read it."):
    li = ''.join(f'<li class="press-item"><button class="photo press-clip" data-src="assets/press/{k}.webp" data-cap="{e(paper)}, {e(date)}: {e(head)}" aria-label="Read the {e(paper)} article: {e(head)}"><img src="assets/press/{k}-sm.webp" width="{PRESS_SIZE.get(k, (560, 400))[0]}" height="{PRESS_SIZE.get(k, (560, 400))[1]}" alt="{e(paper)} clipping: {e(head)}" loading="lazy"></button>'
                 f'<p class="press-meta"><strong>{e(paper)}</strong><span>{e(date)}</span></p><p class="press-head">{e(head)}</p></li>' for k, paper, date, head in PRESS)
    return f"""<section class="section press" id="press"><div class="wrap"><div class="section-head" data-reveal><h2>{title}</h2><p>{sub}</p></div><ul class="press-list" data-hs>{li}</ul></div></section>"""

def summit_schedule():
    from datetime import date
    seen, rows = set(), ''
    for s in sorted(SCHOOLS, key=lambda s: (s['summit']['date'], s['summit']['start'])):
        if s['name'] in seen: continue
        names = [s['name']] + ([s['summit']['with']] if s['summit'].get('with') else []); seen.update(names)
        dt = date(*map(int, s['summit']['date'].split('-')))
        rows += (f'<li><span class="ss-date"><b>{dt.day}</b>{dt.strftime("%b")}<i>{dt.strftime("%a")}</i></span>'
                 f'<span class="ss-school">{" + ".join(e(n) for n in names)}</span><span class="ss-city">{e(s["city"])}</span></li>')
    return f"""<section class="section tint" id="schedule"><div class="wrap split-grid">
  <div data-reveal><h2>How the first edition ran</h2><p class="muted">Eleven Summit days across 12 schools, 9–17 October 2026, starting at Brownwood Public School in Saharanpur.</p></div>
  <ol class="summit-sched" data-reveal style="--d:1">{rows}</ol>
</div></section>"""

def delegates_band():
    x = PHOTOS['delegates-2026']
    return f'''<section class="section delegates" id="delegates">
  <div class="wrap"><div class="section-head" data-reveal><h2>The people behind the stalls</h2><p>Admissions teams from our partner universities with the MyUniMentor team, at the wrap-up of the 2026 edition at Saigrace Academy International, Dehradun.</p></div></div>
  <figure class="delegates-fig" data-reveal><button class="photo photo-wide" data-src="assets/photos/delegates-2026.webp" data-cap="{e(x['alt'])}" aria-label="View photo: {e(x['alt'])}"><img src="assets/photos/delegates-2026.webp" alt="{e(x['alt'])}" width="{x['w']}" height="{x['h']}" draggable="false" loading="lazy"></button>
  <figcaption class="wrap"><strong>{len(UNIS)} partner universities</strong><span>Every stall at the Summit was run by a university's own admissions team.</span><a href="network.html#universities">See all partner universities</a></figcaption></figure>
</section>'''

def reel_cards(names=None):
    out = []
    pool = [x for x in (SCHOOLS if names is None else [x for x in SCHOOLS if x['name'] in names]) if not x.get('no_reel')]
    pool = sorted(pool, key=lambda s: (not s.get('reel'), s['name'].lower()))
    for i, s in enumerate(pool):
        has = bool(s.get('reel'))
        out.append(f'<li data-reveal style="--d:{i % 4}"><button class="reel{"" if has else " soon"}" data-reel="{e(s.get("reel", ""))}" {"" if has else " disabled"}><span class="sr-only">{"Play" if has else "Coming soon:"} Career Summit highlights from </span>'
                   f'<span class="reel-thumb">{logo("schools", s, "logo logo-round")}{"<span class=" + chr(34) + "play" + chr(34) + " aria-hidden=" + chr(34) + "true" + chr(34) + "></span>" if has else "<span class=" + chr(34) + "soon-tag" + chr(34) + ">Video coming soon</span>"}</span>'
                   f'<span class="reel-name">{e(s["name"])}</span><span class="reel-city">{e(s["city"])}</span></button></li>')
    return ''.join(out)

def overall_reel():
    return f'''<button class="reel-feature" data-reel="{MEDIA['summit_overall']}">
  <span class="rf-play" aria-hidden="true"></span><span class="rf-copy"><strong>Watch the full Summit</strong><span>Clips from every school, in one film</span></span>
</button>'''

def lor_card(s, big=False):
    l = s['lor']
    return (f'<button class="lor{" lor-big" if big else ""}" data-src="{l["img"]}" aria-label="Read the full letter of recommendation from {e(s["name"])}">'
            f'<span class="lor-scan"><img src="{l["thumb"]}" alt="Letter of recommendation from {e(s["name"])}" loading="lazy" width="420" height="594"></span>'
            f'<strong>{e(s["name"])}</strong><small>{e(s["city"])}, {e(s["board"])}</small></button>')

def lor_carousel():
    lors = [s for s in SCHOOLS if s.get('lor')]
    tabs = ''.join(f'<button class="lc-tab{" on" if i == 0 else ""}" role="tab" aria-selected="{"true" if i == 0 else "false"}" data-i="{i}">{logo("schools", s, "logo logo-round")}<span>{e(s["name"])}</span></button>' for i, s in enumerate(lors))
    slides = ''.join(f'<div class="lc-slide" role="tabpanel">{lor_card(s, True)}{lor_quote(s)}</div>' for s in lors)
    arrows = '<div class="lc-arrows"><button class="lc-prev" aria-label="Previous letter">‹</button><button class="lc-next" aria-label="Next letter">›</button></div>'
    return f'''<div class="lor-carousel" data-reveal data-n="{len(lors)}">
  <div class="lc-head"><p class="lc-label">Letters of recommendation</p>{arrows}</div>
  <div class="lc-tabs" role="tablist" aria-label="Choose a school">{tabs}</div>
  <div class="lc-track">{slides}</div>
  <p class="lc-more">More letters from our partner schools are on the way.</p>
</div>'''

def lor_quote(s):
    l = s['lor']
    return f'<figure class="lor-quote"><blockquote>“{e(l["quote"])}”</blockquote><figcaption>{e(l["signed"])}, {e(s["city"])}</figcaption></figure>'

def words(text):
    return ' '.join(f'<span class="w" style="--i:{i}">{e(w)}</span>' for i, w in enumerate(text.split()))

HOME_FAQ = [
    ("What is MyUniMentor?", "MyUniMentor is a career counselling and admissions guidance organisation that works with students across India, online and in person, from its base in Dehradun, Uttarakhand. It helps Class 11–12 students choose the right stream, course and university, runs free career seminars for schools, and organises the School Career Guidance Summit, where universities meet students inside their schools."),
    ("Can I get career counselling online from anywhere in India?", "Yes. MyUniMentor counsels students anywhere in India online, and in person in Dehradun and Saharanpur. The first one-on-one session is free. Book through this website, or call or WhatsApp +91 74175 57070."),
    ("How do I choose a good career counsellor?", "Choose one who asks about your marks, interests and plans before suggesting anything, explains every option with its entrance exams, does not push a single university, and is clear about any fees upfront. MyUniMentor’s first session is free, so you can judge for yourself."),
    ("Is career counselling at MyUniMentor free for students?", "Yes. The first one-on-one counselling session is free for Class 11–12 students. Book through the form on this website, or call or WhatsApp +91 74175 57070."),
    ("Are MyUniMentor's career seminars free for schools?", "Yes. Career guidance seminars for Class 11–12 students are offered free of cost to schools."),
    ("Which cities does MyUniMentor work in?", "MyUniMentor works with schools in Dehradun (Uttarakhand) and Saharanpur (Uttar Pradesh), and counsels students across India online and offline. In 2027, we plan to expand to Rishikesh, Roorkee, Srinagar and the wider Garhwal region."),
    ("What is the School Career Guidance Summit?", "It is an in-school career fair organised by MyUniMentor. Universities set up stalls on the school campus and Class 11–12 students meet them, ask questions and compare options without leaving the school campus. The first edition ran across 12 schools in Dehradun and Saharanpur in October 2026."),
    ("How can a university partner with MyUniMentor?", "Universities can exhibit at the School Career Guidance Summit and use MyUniMentor's admission and outreach support. {UNI_COUNT} universities are currently partners. Send an enquiry through the partnership form or email info@myunimentor.in."),
]

def facts_block():
    rows = [("What we do", "Career counselling and admissions guidance for Class 11–12 students"), ("Founded", "2026, by Om Garg"),
            ("Based in", "Dehradun, Uttarakhand"), ("Reach", "Students across India, online and in person"), ("Universities", "{UNI_COUNT} partner universities across India"),
            ("Schools", "12 partner schools in Dehradun and Saharanpur"), ("Flagship event", "School Career Guidance Summit (first edition: October 2026)"),
            ("Next", "In 2027, we plan to expand to Rishikesh, Roorkee, Srinagar and Garhwal"), ("Contact", '+91 74175 57070, <a href="mailto:info@myunimentor.in">info@myunimentor.in</a>')]
    return '<dl class="facts">' + ''.join(f'<div data-reveal style="--d:{i % 4}"><dt>{a}</dt><dd>{b}</dd></div>' for i, (a, b) in enumerate(rows)) + '</dl>'

def journey_section():
    stops = [("Class 10–11", "Choose your stream", "We match subjects to your strengths and interests, not to what everyone else is picking."),
             ("Class 11–12", "Discover courses and careers", "See what each course actually leads to: the work, the growth and the path after it."),
             ("Class 12", "Crack the right entrance exams", "Know which exams matter for your plan, and never miss a registration deadline."),
             ("After Class 12", "Choose the right university", "Shortlist with a checklist, compare honestly and apply with support at every step.")]
    li = ''.join(f'<li class="j-stop" style="--i:{i}"><span class="j-dot" aria-hidden="true"></span><div class="j-card"><span class="j-when">{a}</span><h3>{b_}</h3><p>{c}</p></div></li>' for i, (a, b_, c) in enumerate(stops))
    return f'''<section class="section journey" id="journey">
  <div class="wrap">
    <div class="section-head j-head" data-reveal>
      <h2>From confused to confident, one step at a time</h2>
      <p>This is the path every student walks. We walk it with you.</p>
    </div>
    <div class="j-track">
      <svg class="j-path" aria-hidden="true"><path class="j-bg" pathLength="1"/><path class="j-fg" pathLength="1"/></svg>
      <ol class="j-stops">{li}</ol>
    </div>
    <div class="j-end" data-reveal>
      <p class="j-end-k">Not sure where you are on this path?</p>
      {j_end_actions()}
    </div>
  </div>
</section>'''

def j_end_actions():
    if not SHOW_CAREER_CHECK:
        return '<a href="contact.html" class="btn btn-cyan btn-lg">Book a free counselling session</a>'
    return '''<div class="j-end-btns"><a href="career-check.html" class="btn btn-cyan btn-lg">Take the free career check</a><a href="contact.html" class="btn btn-outline btn-lg">Book a free counselling session</a></div>
      <p class="j-end-note">About 4 minutes · the questions change with your stream</p>'''

def cc_hero_link():
    return '<a class="cc-hero-link" href="career-check.html"><span class="new">New</span>Not sure what fits you? Take the free 4-minute career check</a>'

def cc_band():
    demo = [('Commerce', 'Find the mistake hidden in a company\'s accounts'), ('PCB', 'Help someone walk and move again after an injury'),
            ('PCM', 'Teach a robot or an AI to do a task on its own'), ('Humanities', 'Argue a case and win the debate')]
    cards = ''.join(f'<div class="ccd-card" style="--i:{i}"><span class="ccd-tag">For {t} students</span><p>{q}</p></div>' for i, (t, q) in enumerate(demo))
    cls = ''.join(f'<a class="ccb-cls" href="career-check.html?c={c}">Class {c}</a>' for c in ('9', '10', '11', '12'))
    return f'''<section class="cc-band" style="--rays:url(&quot;{rays_svg(17)}&quot;)">
  <div class="wrap ccb-grid">
    <div class="ccb-copy" data-reveal>
      <p class="ccb-pill">Free · About 4 minutes · Class 9–12</p>
      <h2>The career check that changes with you</h2>
      <p class="ccb-sub">A Commerce student and a PCB student never get the same questions. Answer quick activity cards, go deeper on your top areas, and see the careers, courses and entrance exams that fit you.</p>
      <ul class="ccb-points"><li>Questions picked for your stream</li><li>Follow-ups only on your top matches</li><li>Download your result as a PDF</li></ul>
      <p class="ccb-start">Start with your class</p>
      <div class="ccb-classes">{cls}</div>
    </div>
    <div class="ccd" aria-hidden="true">
      <div class="ccd-deck">{cards}</div>
      <div class="ccd-acts"><span>Not me</span><span>Maybe</span><span class="yes">Love it</span></div>
    </div>
  </div>
</section>'''

def build_home():
    marquee = ''.join(f'<li>{logo("universities", u, "logo logo-tile")}<span class="m-name">{e(u["name"])}</span></li>' for u in UNIS)
    faq_html, faq_schema = faq_block(HOME_FAQ)
    body = f'''
<section class="hero" style="--rays:url(&quot;{rays_svg()}&quot;)">
  <div class="hero-bg" aria-hidden="true"><span class="sun"></span><span class="blob b1"></span><span class="blob b2"></span></div>
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="pill"><span class="dot"></span>Career guidance for Class 11–12 students</p>
      <h1 class="words">{words("Right guidance. Right fit. Right university.")}</h1>
      <p class="hero-sub">Choosing a stream, course and university is one of the biggest decisions a student makes — yet most still make it on hearsay. MyUniMentor brings honest, expert career guidance to students across India, one-on-one and in schools, so every student decides with clarity.</p>
      <div class="hero-actions">
        <a href="contact.html" class="btn btn-cyan btn-lg">Book a free counselling session</a>
        <a href="services-schools.html" class="btn btn-outline-light btn-lg">Partner with us</a>
      </div>
      {cc_hero_link() if SHOW_CAREER_CHECK else ''}
      
    </div>
    <div class="hero-visual" aria-hidden="true">
      {hero_slides()}
      <div class="glass roadmap">
        <p class="rm-title">Your roadmap with MyUniMentor</p>
        <ol>
          <li><span class="rm-step">Know your strengths and interests</span></li>
          <li><span class="rm-step">Choose the right stream and course</span></li>
          <li><span class="rm-step">Shortlist universities that fit you</span></li>
          <li><span class="rm-step">Apply and get admitted</span></li>
        </ol>
      </div>
      <div class="glass float f1"><strong data-count="{len(UNIS)}">{len(UNIS)}</strong><span>partner universities</span></div>
      <div class="glass float f2"><strong data-count="12">12</strong><span>partner schools</span></div>
      <div class="glass float f3"><p><span class="tick"></span>Seminars are free for schools</p><p><span class="tick"></span>Free 1-on-1 counselling for students</p></div>
    </div>
  </div>
  <div class="marquee" aria-label="Our partner universities">
    <p class="wrap marquee-title">Our university network</p>
    <div class="marquee-track"><ul>{marquee}</ul><ul aria-hidden="true">{marquee}</ul></div>
  </div>
</section>
<section class="section help">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <h2>One partner for students, schools and universities</h2>
      <p>We sit at the centre of the admissions journey, so each side gets exactly what it needs.</p>
    </div>
    <ul class="help-grid">
      <li class="help-card c-stu spot" data-reveal style="--d:0"><span class="help-ico">{ICONS['student']}</span>
        <h3>Students &amp; parents</h3><p>Career counselling and admissions guidance, one-on-one.</p>
        <ul class="ticks"><li>Free 1-on-1 counselling for students</li><li>Pick the right stream, course and career path</li><li>A university shortlist that fits your marks, interests and budget</li><li>Help through applications and admissions</li></ul>
        <a class="card-link" href="services-students.html">Explore counselling</a></li>
      <li class="help-card c-sch spot" data-reveal style="--d:1"><span class="help-ico">{ICONS['school']}</span>
        <h3>Schools</h3><p>Free career seminars and in-school career fairs.</p>
        <ul class="ticks"><li>Career guidance seminars for Class 11–12, free for schools</li><li>The School Career Guidance Summit on your campus</li><li>Planned around your timetable</li></ul>
        <a class="card-link" href="services-schools.html">Explore for schools</a></li>
      <li class="help-card c-uni spot" data-reveal style="--d:2"><span class="help-ico">{ICONS['uni']}</span>
        <h3>Universities</h3><p>Admission and outreach support across India.</p>
        <ul class="ticks"><li>Exhibit at the Career Summit in our partner schools</li><li>Reach Class 11–12 students through one partner</li><li>Admission-season outreach support</li></ul>
        <a class="card-link" href="services-universities.html">Explore for universities</a></li>
    </ul>
    
  </div>
</section>

{journey_section()}

<section class="impact">
  <div class="wrap impact-grid">
    <div class="impact-row" data-reveal>
      <h2>MyUniMentor, so far</h2>
      <dl class="stats"><div><dt>Partner schools</dt><dd data-count="12">12</dd></div><div><dt>Partner universities</dt><dd data-count="29">29</dd></div><div><dt>Cities, across Uttarakhand and Uttar Pradesh</dt><dd data-count="2">2</dd></div></dl>
    </div>
    <div class="impact-row" data-reveal>
      <h2>Our founder's track record</h2>
      <dl class="stats"><div><dt>Students guided</dt><dd data-count="10000" data-suffix="+">10,000+</dd></div><div><dt>Seminars delivered</dt><dd data-count="100" data-suffix="+">100+</dd></div><div><dt>One-on-one sessions</dt><dd data-count="500" data-suffix="+">500+</dd></div><div><dt>Years in education</dt><dd data-count="5" data-suffix="+">5+</dd></div></dl>
    </div>
  </div>
</section>

<section class="section summit" style="--rays:url(&quot;{rays_svg(17)}&quot;)">
  <div class="wrap">
    <div class="summit-top">
      <div data-reveal>
        <p class="edition"><span class="dot"></span>First edition · October 2026</p>
        <h2>School Career Guidance Summit</h2>
        <p class="summit-intro">An in-school career fair. Universities set up stalls on the school campus and Class 11–12 students meet them, ask questions and compare options — without leaving the school campus.</p>
        <div class="hero-actions"><a href="career-summit.html" class="btn btn-cyan">See the Career Summit</a></div>
        {overall_reel()}
      </div>
      <dl class="summit-facts" data-reveal style="--d:1">
        <div><dt>schools in the first edition</dt><dd>12</dd></div>
        <div><dt>across Dehradun and Saharanpur</dt><dd>Oct 2026</dd></div>
        <div><dt>Planned: Rishikesh, Roorkee, Srinagar and Garhwal</dt><dd>2027</dd></div>
      </dl>
    </div>
    <div class="mosaic" data-reveal>{''.join(photo_btn(s) for s in ['beverly-summit-hall','saigrace-summit-corridor','alpine-summit-hall','brooklyn-summit-stalls','olympus-summit-auditorium'])}</div>
    <h3 class="reels-h">Watch the highlights</h3>
    <ul class="reels" data-hs>{reel_cards([s['name'] for s in SCHOOLS if s.get('reel')][:4])}</ul>
  </div>
</section>

<section class="section trust">
  <div class="wrap">
    <div class="section-head row-head" data-reveal>
      <div><h2>Trusted by 12 schools</h2><p>Career guidance delivered on campus across Dehradun and Saharanpur.</p></div>
      <a class="btn btn-outline" href="network.html#schools">See our network</a>
    </div>
    <div class="trust-grid">
      {lor_carousel()}
      <ul class="wall wall-3">{school_wall()}</ul>
    </div>
  </div>
</section>

{footprint_section(True)}

<section class="section founder-band">
  <div class="wrap founder-grid">
    <figure class="founder-photo" data-reveal><img src="assets/img/om-garg-seminar.webp" alt="Om Garg, Founder of MyUniMentor, speaking at a career guidance session" width="1400" height="933" loading="lazy"></figure>
    <div data-reveal style="--d:1">
      <h2>Meet our founder</h2>
      <blockquote>“When I was in school, nobody explained where a course actually leads. I had to research everything on my own. Good schools have always been everywhere — organised career guidance hasn't.”</blockquote>
      <p class="sig"><strong>Om Garg</strong>, Founder, MyUniMentor</p>
      <div class="hero-actions"><a href="omgarg.html" class="btn">View Om's profile</a><a href="contact.html" class="btn btn-outline" data-tab="partner">Invite Om for a session</a></div>
    </div>
  </div>
</section>

{faq_html}

{cta("Not sure which course or university is right for you?", "Talk to a counsellor. 1-on-1 counselling is free for students.")}'''
    page('index.html', 'MyUniMentor | Career Counselling & University Admissions Guidance in Dehradun',
         'MyUniMentor offers free 1-on-1 career counselling for Class 11–12 students, free career seminars for schools in Dehradun and Saharanpur, and the School Career Guidance Summit with {UNI_COUNT} partner universities.',
         'Home', body, ORG_SCHEMA + WEBSITE_SCHEMA + faq_schema)
STATE = {'Ambala': 'Haryana', 'Chandigarh': 'Chandigarh', 'Dehradun': 'Uttarakhand', 'Greater Noida': 'Uttar Pradesh', 'Gurugram': 'Haryana', 'Landran': 'Punjab',
         'Mohali': 'Punjab', 'Panipat': 'Haryana', 'Pune': 'Maharashtra', 'Phagwara': 'Punjab', 'Roorkee': 'Uttarakhand', 'Solan': 'Himachal Pradesh',
         'Sonipat': 'Haryana', 'Saharanpur': 'Uttar Pradesh', 'Haridwar': 'Uttarakhand'}
def place(city): return f"{city}, {STATE[city]}" if city in STATE and STATE[city] != city else city

# Network page: tab title follows the section in view (schools or universities)
NET_TITLE_JS = "<script>(function(){var T={universities:'Partner Universities | MyUniMentor',schools:'Partner Schools | MyUniMentor'},d=document.title;function s(i){document.title=T[i]||d}function h(){s(location.hash.slice(1))}addEventListener('hashchange',h);h();if('IntersectionObserver'in window){var o=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting)s(x.target.id)})},{rootMargin:'-45% 0px -45% 0px'});['schools','universities'].forEach(function(i){var e=document.getElementById(i);e&&o.observe(e)})}})()</script>"

def build_network():
    regions = ['Uttarakhand', 'Punjab & Chandigarh', 'Haryana', 'Uttar Pradesh', 'Other states']
    sch_cards = ''.join(
        f'<li class="org-card" data-reveal data-city="{e(s["city"])}" data-search="{e((s["name"] + " " + place(s["city"]) + " " + s["board"]).lower())}">{logo("schools", s, "logo logo-card")}'
        f'<div class="org-body"><h3>{e(s["name"])}</h3><p class="org-meta">{e(place(s["city"]))}<span class="chip">{e(s["board"])}</span></p>'
        f'<p class="org-tags"><span class="tag">Career Summit 2026</span>{"<span class=\'tag tag-lor\'>Letter of recommendation</span>" if s.get("lor") else ""}</p>'
        f'{"<p class=\'org-note\'>" + e(s["note"]) + "</p>" if s.get("note") else ""}</div></li>' for s in SCHOOLS)
    uni_cards = ''.join(
        f'<li class="org-card uni" data-reveal data-region="{e(u["region"])}" data-search="{e((u["name"] + " " + u.get("short", "") + " " + place(u["city"]) + " " + u.get("campuses", "")).lower())}">{logo("universities", u, "logo logo-card")}'
        f'<div class="org-body"><h3>{e(u["name"])}{(" <span class=\'short\'>(" + e(u["short"]) + ")</span>") if u.get("short") else ""}</h3><p class="org-meta">{e(u.get("campuses") or place(u["city"]))}</p>'
        f'{(chr(60) + "a class=" + chr(34) + "uni-more" + chr(34) + " href=" + chr(34) + slug(u["name"]) + ".html" + chr(34) + ">Admission, fees and placements" + chr(60) + "/a>") if slug(u["name"]) in UNI_PAGES else ""}</div></li>' for u in UNIS)
    region_btns = '<button class="fbtn" aria-pressed="true" data-filter="all">All</button>' + ''.join(f'<button class="fbtn" aria-pressed="false" data-filter="{e(r)}">{e(r)}</button>' for r in regions)
    lor_schools = [s for s in SCHOOLS if s.get('lor')]
    lors = ''.join(f'<li class="lor-item">{lor_card(s)}{lor_quote(s)}</li>' for s in lor_schools)

    body = f'''
<section class="page-hero" style="--rays:url(&quot;{rays_svg(19)}&quot;)">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a><span aria-hidden="true">/</span><span>Our network</span></nav>
    <h1>Our network</h1>
    <p class="page-sub">The schools where we guide students, and the universities we bring to them. Every name here is a partner we have worked with.</p>
    <div class="jump">
      <a href="#schools"><strong>12</strong><span>Partner schools</span></a>
      <a href="#universities"><strong>{len(UNIS)}</strong><span>Partner universities</span></a>
      <a href="#testimonials"><strong>{len(TESTIMONIALS)}</strong><span>Student stories</span></a>
    </div>
  </div>
</section>

<section id="schools" class="section">
  <div class="wrap">
    <div class="section-head row-head">
      <div><h2>Partner schools</h2><p>Schools in Dehradun and Saharanpur where we have run seminars and the School Career Guidance Summit.</p></div>
      <div class="uni-tools"><label class="search"><span class="vh">Search schools</span><input type="search" class="org-search" placeholder="Search schools or cities"></label><div class="filters" role="group" aria-label="Filter schools by city"><button class="fbtn" aria-pressed="true" data-filter="all">All</button><button class="fbtn" aria-pressed="false" data-filter="Dehradun">Dehradun</button><button class="fbtn" aria-pressed="false" data-filter="Saharanpur">Saharanpur</button></div></div>
    </div>
    <ul class="org-grid" data-filter-target="city">{sch_cards}</ul>
    <p class="empty" hidden>No school matches that search. Try a city, like Dehradun.</p>
  </div>
</section>

<section id="universities" class="section tint">
  <div class="wrap">
    <div class="section-head">
      <h2>Partner universities</h2>
      <p>{len(UNIS)} universities, listed alphabetically. Order does not indicate ranking.</p>
    </div>
    <div class="uni-tools">
      <label class="search"><span class="vh">Search universities</span><input type="search" class="org-search" placeholder="Search by name, city or state"></label>
      <div class="filters" role="group" aria-label="Filter universities by region">{region_btns}</div>
    </div>
    <ul class="org-grid unis-grid" data-filter-target="region">{uni_cards}</ul>
    <p class="empty" hidden>No university matches that search. Try a city, like Dehradun.</p>
  </div>
</section>

<section id="lors" class="section trust">
  <div class="wrap trust-grid">
    <div data-reveal><h2>Letters of recommendation</h2><p class="muted">Letters from the principals of our partner schools. Pick a school, swipe, or tap a letter to read it in full.</p></div>
    {lor_carousel()}
  </div>
</section>

<section id="testimonials" class="section tint">
  <div class="wrap">
    <div class="section-head row-head" data-reveal><div><h2>What students say</h2><p>Students we have guided, now at universities across India.</p></div><a class="btn btn-outline" href="testimonials.html">All testimonials</a></div>
    <ul class="tgrid t-strip" data-hs>{''.join(tc(i, t) for i, t in enumerate(TESTIMONIALS))}</ul>
  </div>
</section>

<section class="cta-band" style="--rays:url(&quot;{rays_svg(13)}&quot;)">
  <div class="wrap cta-inner">
    <div><h2>Want your school or university on this list?</h2><p>Seminars are free for schools. Universities can exhibit at the next Career Summit.</p></div>
    <div class="hero-actions"><a href="contact.html" class="btn btn-cyan btn-lg">Become a partner</a></div>
  </div>
</section>''' + NET_TITLE_JS
    page('network.html', 'Partner Universities & Schools | MyUniMentor',
         'MyUniMentor partners with 12 schools in Dehradun and Saharanpur and {UNI_COUNT} universities across India, including UPES, Graphic Era, Chandigarh University, LPU and Tulas University.',
         'Our network', body, crumbs_schema([("Home", ""), ("Our network", "network")]) + '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "CollectionPage", "url": "https://myunimentor.in/network", "name": "MyUniMentor partner schools and universities",
         "about": {"@id": "https://myunimentor.in/#org"}, "hasPart": [
             {"@type": "ItemList", "name": "Partner schools", "numberOfItems": len(SCHOOLS), "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "School", "name": x["name"], "address": {"@type": "PostalAddress", "addressLocality": x["city"], "addressCountry": "IN"}}} for i, x in enumerate(SCHOOLS)]},
             {"@type": "ItemList", "name": "Partner universities", "numberOfItems": len(UNIS), "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "CollegeOrUniversity", "name": x["name"], "address": {"@type": "PostalAddress", "addressLocality": x["city"], "addressCountry": "IN"}}} for i, x in enumerate(UNIS)]}]}, ensure_ascii=False) + '</script>')


def timeline():
    items = [("Before 2026", "Five years in a senior cross-functional role in the education sector, guiding students and running school seminars"),
             ("2026", "MyUniMentor is founded in Dehradun"),
             ("9 Oct 2026", "First MyUniMentor seminar, at Brownwood Public School, Saharanpur"),
             ("Oct 2026", "The School Career Guidance Summit runs across 12 schools in Dehradun and Saharanpur"),
             ("2027", "In 2027, we plan to expand to Rishikesh, Roorkee, Srinagar and the wider Garhwal region")]
    return '<ol class="timeline">' + ''.join(f'<li data-reveal style="--d:{i}"{" class=\'next\'" if i == 4 else ""}><span class="when">{a}</span><span class="what">{b}</span></li>' for i, (a, b) in enumerate(items)) + '</ol>'

def build_about():
    routes = [("student", "c-stu", "One-on-one counselling", "Online or in person, for students anywhere in India. Your first session is free.", "services-students.html", "Book a session"),
              ("tools", "c-stu", "Free tools and guides", "The 2027 entrance exam calendar, course guides and articles, open to everyone.", "exam-calendar.html", "See the exam calendar"),
              ("school", "c-sch", "Seminars and summits", "Free career seminars and the School Career Guidance Summit, held on the school's own campus.", "services-schools.html", "For schools"),
              ("uni", "c-uni", "A national university network", "{UNI_COUNT} partner universities across India, so students compare real options before they decide.", "network.html#universities", "See the network")]
    cards = ''.join(f'<li data-reveal style="--d:{i}"><span class="help-ico {c}">{ICONS[ic]}</span><h3>{h}</h3><p>{t}</p><a class="card-link" href="{u}">{l}</a></li>' for i, (ic, c, h, t, u, l) in enumerate(routes))
    beliefs = [("Every student, not a few", "Good guidance shouldn't depend on your city, your school or who your family knows."),
               ("Fit over hype", "The right course is the one that fits you, not the one everyone around you is picking."),
               ("Clarity before deadlines", "Decisions made early and calmly are better than decisions made the night before a form closes.")]
    bel = ''.join(f'<li data-reveal style="--d:{i}"><span class="b-num">{i + 1}</span><h3>{h}</h3><p>{t}</p></li>' for i, (h, t) in enumerate(beliefs))
    body = page_hero("Career guidance for every student", "Our mission is simple: every student in India should get honest, expert guidance before choosing a stream, a course or a university, wherever they live and whichever school they go to.", "About") + f'''
<section class="section">
  <div class="wrap story-grid">
    <div data-reveal><h2>Why we exist</h2></div>
    <div class="prose" data-reveal style="--d:1">
      <p class="lead">For most students in India, the biggest decision of their life is made on hearsay: a relative's advice, a coaching brochure, what a friend is picking.</p>
      <p>Real career guidance has always been a privilege. Some students get a counsellor, a career fair and someone to explain where a course actually leads. Most never do.</p>
      <p>MyUniMentor exists to change that. We want guidance to reach every single student, through one-on-one counselling, free tools anyone can use, and sessions in schools and communities.</p>
    </div>
  </div>
</section>
<section class="section tint">
  <div class="wrap">
    <div class="section-head" data-reveal><h2>How guidance reaches every student</h2><p>Four ways in, so no student is left without help.</p></div>
    <ul class="pillars pillars-4" data-hs="m">{cards}</ul>
  </div>
</section>
<section class="section beliefs-band">
  <div class="wrap">
    <div class="section-head" data-reveal><h2>What we believe</h2></div>
    <ol class="beliefs" data-hs="m">{bel}</ol>
  </div>
</section>
<section class="section founder-band">
  <div class="wrap founder-grid">
    <figure class="founder-photo" data-reveal><img src="assets/img/om-garg.webp" alt="Om Garg, Founder of MyUniMentor" width="960" height="1200" loading="lazy"></figure>
    <div data-reveal style="--d:1">
      <h2>Our founder</h2>
      <blockquote>“When I was in school, nobody explained where a course actually leads. I had to research everything on my own.”</blockquote>
      <p class="sig"><strong>Om Garg</strong>, Founder, MyUniMentor</p>
      <p class="muted">Om spent five years in a senior cross-functional role in the education sector before founding MyUniMentor in 2026. He has guided over 10,000 students, delivered 100+ seminars and counselled 500+ students one-on-one.</p>
      <div class="hero-actions"><a href="omgarg.html" class="btn">View Om's full profile</a></div>
    </div>
  </div>
</section>
<section class="section glance tint">
  <div class="wrap glance-grid">
    <div data-reveal><h2>MyUniMentor at a glance</h2><p class="muted">The key facts, in one place.</p></div>
    {facts_block()}
  </div>
</section>
<section class="section">
  <div class="wrap"><div class="section-head" data-reveal><h2>How we got here</h2></div>{timeline()}</div>
</section>
{cta("Need guidance for yourself or your child?", "Talk to a MyUniMentor counsellor. Your first one-on-one session is free.")}'''
    page('about.html', 'About MyUniMentor: Career Guidance for Every Student', 'MyUniMentor was founded in 2026 in Dehradun by Om Garg with one mission: honest, expert career guidance for every student in India.', 'About', body,
         crumbs_schema([("Home", ""), ("About", "about")]) + '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "AboutPage", "url": "https://myunimentor.in/about", "name": "About MyUniMentor", "about": {"@id": "https://myunimentor.in/#org"}, "isPartOf": {"@id": "https://myunimentor.in/#website"}}) + '</script>')

def steps(items):
    return '<ol class="steps">' + ''.join(f'<li data-reveal style="--d:{i}"><span class="step-n">{i + 1}</span><h3>{a}</h3><p>{b}</p></li>' for i, (a, b) in enumerate(items)) + '</ol>'

def service_page(fname, crumb, title, sub, head, intro, bullets, step_items, faq, cta_args, form_default, meta_title, meta_desc, extra=''):
    faq_html, faq_schema = faq_block(faq)
    bl = ''.join(f'<li>{b}</li>' for b in bullets)
    body = page_hero(title, sub, crumb) + f'''
<section class="section">
  <div class="wrap split-grid">
    <div data-reveal><h2>{head}</h2><p class="lead">{intro}</p>{'' if any('*' in x for x in bullets) else ''}</div>
    <ul class="ticks big" data-reveal style="--d:1">{bl}</ul>
  </div>
</section>
<section class="section tint"><div class="wrap"><div class="section-head" data-reveal><h2>How it works</h2></div>{steps(step_items)}</div></section>
{extra}
<section class="section" id="enquire"><div class="wrap contact-grid">
  <div data-reveal><h2>Get started</h2><p class="muted">Tell us a little about yourself and our team will call you back.</p>
    <ul class="contact-list"><li><span>Call or WhatsApp</span><a href="tel:+917417557070">+91 74175 57070</a></li><li><span>Email</span><a href="mailto:info@myunimentor.in">info@myunimentor.in</a></li></ul></div>
  {form_card(form_default)}
</div></section>
{faq_html}
{cta(*cta_args)}'''
    page(fname, meta_title, meta_desc, 'Services', body, crumbs_schema([("Home", ""), ("Services", fname.replace('.html', '')), (crumb, fname.replace('.html', ''))]) + faq_schema)

def build_services():
    service_page('services-students.html', 'For students & parents', 'Career counselling for students and parents',
        'One-on-one guidance to choose the right stream, course and university — so you decide with clarity, not on hearsay. 1-on-1 counselling is free for students.',
        'Clarity before you choose', 'Our counsellors sit with the student (and parents, if they like) to understand marks, interests, strengths and budget, then build a clear plan for what to study and where.',
        ['Free 1-on-1 counselling for students', 'Stream and subject choice for Class 11', 'Course and career path planning', 'A university shortlist that fits your marks, interests and budget', 'Guidance on entrance exams, applications and admissions', 'Online or in person'],
        [("Book a session", "Fill the form or WhatsApp us. We'll call you to fix a time."), ("Understand the student", "Interests, strengths, marks and goals — in a one-on-one conversation."),
         ("Build the plan", "Stream, course and career options, with a shortlist of universities that fit."), ("Apply with support", "Help with entrance exams, applications and admission steps.")],
        [("Is career counselling free?", "Yes. Your first one-on-one counselling session is free for Class 11–12 students."),
         ("Who is the free session for?", "Students currently in Class 11 or Class 12, along with their parents or guardians."),
         ("Is counselling online or in person?", "Both. We counsel students in person and online, anywhere in India."),
         ("Can parents join the session?", "Yes, parents are welcome and encouraged to join.")],
        ("Ready to plan your next step?", "1-on-1 counselling is free for students."), 'student',
        'Free Career Counselling for Class 11–12 Students in Dehradun | MyUniMentor',
        'Free 1-on-1 career counselling for Class 11–12 students in Dehradun, Saharanpur and online across India. Choose the right stream, course and university with MyUniMentor.',
        '')

    service_page('services-schools.html', 'For schools', 'Career guidance for schools',
        'Free career seminars and the School Career Guidance Summit — organised career guidance for your Class 11–12 students, on your own campus.',
        'Bring career guidance to your campus', 'We run career guidance seminars for Class 11–12 students at no cost to the school, and bring universities to your campus through the School Career Guidance Summit.',
        ['Career guidance seminars for Class 11–12, free for schools', 'The School Career Guidance Summit on your campus', 'Universities set up stalls; students meet them without leaving the school campus', 'Planned around your timetable, within 2.5 hours', 'Your school provides the stage and AV; we handle the rest'],
        [("Get in touch", "Send an enquiry or call us to pick a date."), ("We plan it with you", "Session format, timing and student groups, around your timetable."),
         ("On the day", "Our team runs the seminar or the summit on your campus."), ("Follow-up", "Students who want one-on-one guidance can book a counselling session.")],
        [("Are seminars free for schools?", "Yes. Career guidance seminars for Class 11–12 students are free of cost for schools."),
         ("How long does the Career Summit take?", "Each school visit is completed within 2.5 hours, including stall setup."),
         ("What does the school need to provide?", "The main stage and audio-visual setup. MyUniMentor handles the universities and the programme."),
         ("Which schools have you worked with?", 'We have worked with 12 schools in Dehradun and Saharanpur. See the full list on our <a href="network.html#schools">network page</a>.')],
        ("Invite MyUniMentor to your school", "Career seminars are free for schools.", "Send an enquiry", "#enquire"), 'partner',
        'Free Career Guidance Seminars & Career Fairs for Schools | MyUniMentor',
        'MyUniMentor offers free career guidance seminars for Class 11–12 and the School Career Guidance Summit, an in-school career fair, for schools in Dehradun and Saharanpur.',
        f'<section class="section"><div class="wrap"><div class="section-head" data-reveal><h2>Seminars and summits on campus</h2><p>From our sessions in Dehradun and Saharanpur.</p></div>{gallery(['brooklyn-seminar-hall', 'beverly-seminar', 'seminar-circle', 'alpine-summit-hall', 'doon-world-summit-law', 'st-marys-summit-stall'])}</div></section>'
        f'<section class="section schools-wall"><div class="wrap"><div class="section-head" data-reveal><h2>Schools we work with</h2><p>Our current partner schools in Dehradun and Saharanpur. In 2027, we plan to expand to more cities, starting with Rishikesh and Roorkee.</p></div><ul class="wall">{school_wall()}</ul></div></section>')

    service_page('services-universities.html', 'For universities', 'Admission and outreach support for universities',
        'Meet serious Class 11–12 students where they already are — inside their schools — through one partner.',
        'Reach students through their schools', 'MyUniMentor works with 12 schools across Dehradun and Saharanpur. Partner universities meet their Class 11–12 students at the School Career Guidance Summit and through our admission-season outreach.',
        ['A stall at the School Career Guidance Summit in our partner schools', 'Focused, school-sized fairs, so your stall gets real attention', 'Reach students across Dehradun and Saharanpur through one partner', 'Admission-season outreach support', 'Expanding to Rishikesh, Roorkee, Srinagar and Garhwal in 2027'],
        [("Enquire", "Tell us which cities and schools you want to reach."), ("Choose your participation", "Pick the schools and dates that suit your admission plans."),
         ("Meet students", "Your team meets Class 11–12 students at your stall on campus."), ("Stay in touch", "Admission-season outreach support through the cycle.")],
        [("Which universities exhibit at each school?", "The line-up is chosen for each school and varies by city."),
         ("Do universities get stage time at the Career Summit?", "No. Universities take part through exhibitor stalls only, so students can meet each one directly."),
         ("Which universities are already partners?", f'{len(UNIS)} universities, including UPES, Graphic Era University, Chandigarh University, LPU and Tulas University. See the <a href="network.html#universities">full list</a>.'),
         ("Where is MyUniMentor expanding next?", "In 2027, we plan to expand to Rishikesh, Roorkee, Srinagar and the wider Garhwal region.")],
        ("Exhibit at the next Career Summit", "Join {UNI_COUNT} partner universities.", "Send an enquiry", "#enquire"), 'partner',
        'University Admission & Outreach Support in Uttarakhand and UP | MyUniMentor',
        'Partner with MyUniMentor to meet Class 11–12 students in schools across Dehradun and Saharanpur. Exhibit at the School Career Guidance Summit with {UNI_COUNT} partner universities.', delegates_band())

def build_summit():
    ev = {"@context": "https://schema.org", "@type": "EventSeries", "name": "School Career Guidance Summit", "organizer": {"@type": "Organization", "name": "MyUniMentor", "url": "https://myunimentor.in/"},
          "description": "An in-school career fair where universities set up stalls on school campuses and Class 11–12 students meet them.", "startDate": "2026-10", "image": [f"https://myunimentor.in/assets/photos/{k}.webp" for k in ("delegates-2026", "beverly-summit-hall", "saigrace-summit-corridor", "alpine-summit-hall")], "location": [{"@type": "Place", "name": s["name"], "address": {"@type": "PostalAddress", "addressLocality": s["city"], "addressCountry": "IN"}} for s in SCHOOLS]}
    subs, seen = [], set()
    for s in sorted(SCHOOLS, key=lambda s: s['summit']['date']):
        if s['name'] in seen: continue
        names = [s['name']] + ([s['summit']['with']] if s['summit'].get('with') else []); seen.update(names)
        d0 = s['summit']['date']
        subs.append({"@type": "Event", "name": f"School Career Guidance Summit at {' and '.join(names)}", "startDate": f"{d0}T{s['summit']['start']}:00+05:30", "endDate": f"{d0}T{s['summit']['end']}:00+05:30",
                     "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "eventStatus": "https://schema.org/EventScheduled",
                     "location": {"@type": "Place", "name": names[0], "address": {"@type": "PostalAddress", "addressLocality": s['city'], "addressCountry": "IN"}},
                     "description": f"An in-school career fair at {' and '.join(names)}, {s['city']}. Partner universities set up stalls on the school campus and Class 11–12 students meet their delegates one-to-one. Free for students.",
                     "image": ev["image"],
                     "organizer": {"@type": "Organization", "name": "MyUniMentor", "url": "https://myunimentor.in/"},
                     "performer": {"@type": "Organization", "name": "MyUniMentor", "url": "https://myunimentor.in/"},
                     "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR", "availability": "https://schema.org/InStock", "url": "https://myunimentor.in/career-summit", "validFrom": f"{d0}T00:00:00+05:30"}})
    ev["subEvent"] = subs
    body = page_hero("School Career Guidance Summit", "The first edition ran in October 2026 across 12 schools. An in-school career fair. Universities set up stalls on the school campus and Class 11–12 students meet them, ask questions and compare options — without leaving the school campus.", "Career Summit",
        '<div class="jump"><a href="#schools-list"><strong>12</strong><span>Schools</span></a><a href="#how"><strong>2,000+</strong><span>Students reached</span></a><a href="#next"><strong>2027</strong><span>Planned: Garhwal region</span></a></div>') + f'''
{delegates_band()}
<section class="section" id="how">
  <div class="wrap split-grid">
    <div data-reveal><h2>A career fair, inside the school</h2><p class="lead">Most career fairs ask students to travel to a city hall. The Career Summit comes to them — so every Class 11–12 student in the school gets to meet universities in person.</p></div>
    <ul class="ticks big" data-reveal style="--d:1"><li>Partner universities set up stalls on the school campus</li><li>Each university's own delegates give first-hand information on courses, fees and admissions</li><li>Students get their doubts cleared on the spot, one-to-one</li><li>Parents and teachers can join in and ask questions too</li><li>Completed within 2.5 hours, including setup</li><li>The first edition ran in October 2026 across Dehradun and Saharanpur</li></ul>
  </div>
</section>
<section class="section" id="photos"><div class="wrap"><div class="section-head" data-reveal><h2>Inside the Summit</h2><p>Real moments from the first edition, October 2026. Tap a photo to see it larger.</p></div>{gallery(['alpine-summit-hall', 'beverly-summit-hall', 'saigrace-summit-corridor', 'brooklyn-summit-stalls', 'olympus-summit-auditorium', 'doon-world-summit-stalls', 'carman-summit-stalls', 'st-marys-summit-stall', 'doon-world-summit-law', 'summit-hall-saharanpur'])}</div></section>
<section class="section summit" id="schools-list" style="--rays:url(&quot;{rays_svg(17)}&quot;)">
  <div class="wrap"><div class="section-head row-head" data-reveal><div><h2>Highlights from every school</h2><p class="summit-intro">Tap a school to watch its highlights. More videos are on the way.</p></div>{overall_reel()}</div><ul class="reels" data-hs>{reel_cards()}</ul></div>
</section>
{press_section()}
{footprint_section()}
<section class="section tint" id="next"><div class="wrap"><div class="section-head" data-reveal><h2>How we got here, and where we're going</h2></div>{timeline()}</div></section>
{cta("Bring the Career Summit to your school or university", "Schools host it on campus. Universities exhibit.", "Send an enquiry")}'''
    page('career-summit.html', 'School Career Guidance Summit: In-School Career Fair | MyUniMentor',
         'The School Career Guidance Summit is MyUniMentor\'s in-school career fair. The first edition (October 2026) ran across 12 schools in Dehradun and Saharanpur, with partner universities setting up stalls on each campus.',
         'Career Summit', body, crumbs_schema([("Home", ""), ("Career Summit", "career-summit")]) + f'<script type="application/ld+json">{json.dumps(ev)}</script>')

def build_contact():
    lb = {"@context": "https://schema.org", "@type": "LocalBusiness", "@id": "https://myunimentor.in/#local", "name": "MyUniMentor", "telephone": "+91-7417557070", "email": "info@myunimentor.in", "url": "https://myunimentor.in/",
          "image": "https://myunimentor.in/assets/img/og-image.jpg", "logo": "https://myunimentor.in/assets/img/logo-dark.png", "parentOrganization": {"@id": "https://myunimentor.in/#org"},
          "areaServed": ["Dehradun", "Saharanpur", "India"], "contactPoint": {"@type": "ContactPoint", "telephone": "+91-7417557070", "contactType": "customer service", "areaServed": "IN", "availableLanguage": ["English", "Hindi"]},
          "address": {"@type": "PostalAddress", "addressLocality": "Dehradun", "addressRegion": "Uttarakhand", "postalCode": "248001", "addressCountry": "IN"}}
    body = page_hero("Talk to us", "Book a free counselling session*, invite us to your school, or ask about partnering. Our team will call you back.", "Contact") + f'''
<section class="section"><div class="wrap contact-grid">
  <div data-reveal>
    <h2>Reach us directly</h2>
    <ul class="contact-list"><li><span>Call or WhatsApp</span><a href="tel:+917417557070">+91 74175 57070</a></li><li><span>Email</span><a href="mailto:info@myunimentor.in">info@myunimentor.in</a></li><li><span>Based in</span>Dehradun, Uttarakhand 248001</li></ul>
    <div class="social social-dark"><a href="https://www.instagram.com/myunimentor.in" target="_blank" rel="noopener">Instagram</a><a href="https://www.facebook.com/p/My-Uni-Mentor-61595547407499/" target="_blank" rel="noopener">Facebook</a><a href="https://www.linkedin.com/company/myunimentor/" target="_blank" rel="noopener">LinkedIn</a></div>
    
  </div>
  {form_card()}
</div></section>'''
    page('contact.html', 'Contact MyUniMentor: Book Free Career Counselling', 'Call or WhatsApp +91 74175 57070 or email info@myunimentor.in to book free 1-on-1 career counselling, a free school seminar, or a university partnership.', '', body,
         crumbs_schema([("Home", ""), ("Contact", "contact")]) + f'<script type="application/ld+json">{json.dumps(lb)}</script>')

from content_blog import POSTS
from content_courses import COURSES
PUB = "2026-11-20"
try: LASTMOD = json.load(open(os.path.join(ROOT, 'data/lastmod.json')))
except Exception: LASTMOD = {}
def pub_mod(slug, published=None):
    """(datePublished, dateModified): a post's own `date`, and the day its content last really changed (from data/lastmod.json)."""
    pub = published or PUB
    return pub, max(pub, LASTMOD.get(slug, {}).get('date', pub))
def nice_date(iso):
    import datetime as _d
    d = _d.date.fromisoformat(iso); return f"{d.day} {d.strftime('%b %Y')}"
def label_tables(html):
    def fix(m):
        t = m.group(0); heads = re.findall(r'<th>(.*?)</th>', t.split('</thead>')[0])
        def row(r):
            cells = re.findall(r'<td>(.*?)</td>', r.group(0), re.S)
            return '<tr>' + ''.join(f'<td data-label="{re.sub("<[^>]+>", "", heads[i]) if i < len(heads) else ""}">{c}</td>' for i, c in enumerate(cells)) + '</tr>'
        return re.sub(r'<tr>(?:(?!</tr>).)*?<td>.*?</tr>', row, t, flags=re.S)
    return re.sub(r'<table>.*?</table>', fix, html, flags=re.S)
for _p in POSTS: _p['body'] = label_tables(_p['body'])
POST_BY = {x['slug']: x for x in POSTS}
COURSE_BY = {x['slug']: x for x in COURSES}

def post_card(p_, i=0):
    return (f'<li class="post" data-reveal style="--d:{i % 3}"><a href="{p_["slug"]}.html"><span class="post-tag">{e(p_["tag"])}</span>'
            f'<h3>{e(p_["h1"])}</h3><p>{e(p_["desc"])}</p><span class="post-meta">{p_["read"]} min read</span></a></li>')

def course_card(c, i=0):
    return (f'<li class="course-card" data-reveal style="--d:{i % 3}"><a href="{c["slug"]}.html"><strong>{e(c["name"])}</strong><span>{e(c["full"])}</span>'
            f'<dl>' + ''.join(f'<div><dt>{k}</dt><dd>{e(v)}</dd></div>' for k, v in c['facts'][:2]) + '</dl></a></li>')

def article_aside(extra_links):
    links = ''.join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in extra_links)
    return f'''<aside class="art-aside">
  <div class="aside-card dark"><strong>Free 1-on-1 counselling</strong><p>Talk your options through with a MyUniMentor counsellor.</p><a class="btn btn-cyan btn-full" href="contact.html">Book a free session</a><p class="tc">For Class 11–12 students.</p></div>
  <div class="aside-card"><strong>Entrance exam dates 2027</strong><p>JEE, NEET, CUET, CLAT and more, with countdowns, in one calendar.</p><a class="btn btn-outline btn-full" href="exam-calendar.html">See the exam calendar</a></div>
  <div class="aside-card"><strong>Keep reading</strong><ul class="aside-links">{links}</ul></div>
</aside>'''

def build_blog():
    cards = ''.join(post_card(p_, i) for i, p_ in enumerate(POSTS))
    body = page_hero("Guides and articles", "Clear, practical guides on streams, courses, entrance exams and universities, written for Class 11–12 students and parents.", "Blog") + f'''
<section class="section"><div class="wrap"><h2 class="sr-only">All articles</h2><ul class="posts" data-hs="m">{cards}</ul></div></section>
<section class="section tint"><div class="wrap"><div class="section-head row-head" data-reveal><div><h2>Course guides</h2><p>What you study, who it suits, entrance exams and careers.</p></div><a class="btn btn-outline" href="courses.html">All course guides</a></div><ul class="courses" data-hs="m">{''.join(course_card(c, i) for i, c in enumerate(COURSES))}</ul></div></section>
{cta("Have a question you want answered?", "Ask a counsellor directly. 1-on-1 counselling is free for students.")}'''
    blog_ld = {"@context": "https://schema.org", "@type": "Blog", "name": "MyUniMentor Blog", "url": "https://myunimentor.in/blog",
               "blogPost": [{"@type": "BlogPosting", "headline": x['h1'], "url": f"https://myunimentor.in/{x['slug']}", "datePublished": x.get('date', PUB)} for x in POSTS]}
    page('blog.html', 'Career Guidance Blog: Streams, Courses, Exams and Universities | MyUniMentor', 'Guides for Class 11–12 students and parents on choosing streams, courses, entrance exams like CUET and CLAT, and universities in India.', 'Resources', body,
         crumbs_schema([("Home", ""), ("Blog", "blog")]) + f'<script type="application/ld+json">{json.dumps(blog_ld)}</script>')
    for p_ in POSTS:
        faq_html, faq_schema = faq_block(p_['faq'], 'Questions students ask')
        rel = [POST_BY[r] for r in p_['related'] if r in POST_BY]
        dpub, dmod = pub_mod(p_['slug'], p_.get('date'))
        meta = f'<p class="art-meta"><span>By <a href="omgarg.html">Om Garg</a>, Founder, MyUniMentor</span><span aria-hidden="true">·</span>Updated {nice_date(dmod)}<span aria-hidden="true">·</span>{p_["read"]} min read</p>'
        art_ld = {"@context": "https://schema.org", "@type": "Article", "headline": p_['h1'], "description": p_['desc'], "datePublished": dpub, "dateModified": dmod,
                  "image": [f"https://myunimentor.in/assets/og/{p_['slug']}.jpg", "https://myunimentor.in/assets/img/og-image.jpg"], "mainEntityOfPage": f"https://myunimentor.in/{p_['slug']}",
                  "author": {"@type": "Person", "name": "Om Garg", "url": "https://myunimentor.in/omgarg", "jobTitle": "Founder, MyUniMentor"},
                  "publisher": {"@type": "Organization", "@id": "https://myunimentor.in/#org", "name": "MyUniMentor", "logo": {"@type": "ImageObject", "url": "https://myunimentor.in/assets/img/icon-v2-512.png"}}}
        body = page_hero(p_['h1'], e(p_['lede']), "Blog", meta) + f'''
<section class="section article-section"><div class="wrap art-grid">
  <article class="article">{p_['body']}</article>
  {article_aside([(x['h1'], x['slug'] + '.html') for x in rel] + [("All course guides", "courses.html"), ("Entrance exam calendar 2027", "exam-calendar.html")])}
</div></section>
{faq_html}
<section class="section tint"><div class="wrap"><div class="section-head" data-reveal><h2>Read next</h2></div><ul class="posts" data-hs="m">{''.join(post_card(x, i) for i, x in enumerate(rel))}</ul></div></section>
{cta("Want a plan made for you?", "Talk to a MyUniMentor counsellor. 1-on-1 counselling is free for students.")}'''
        page(f"{p_['slug']}.html", p_['title'], p_['desc'], 'Resources', body,
             crumbs_schema([("Home", ""), ("Blog", "blog"), (p_['h1'], p_['slug'])]) + faq_schema + f'<script type="application/ld+json">{json.dumps(art_ld)}</script>')

def build_courses():
    body = page_hero("Course guides", "What each course is really about, who it suits, which entrance exams you need and where it can lead. Start here before you shortlist universities.", "Course guides") + f'''
<section class="section"><div class="wrap"><ul class="courses" data-hs="m">{''.join(course_card(c, i) for i, c in enumerate(COURSES))}</ul>
<p class="muted center-note" data-reveal>More course guides are on the way. Can't find yours? <a href="contact.html">Ask a counsellor</a>.</p></div></section>
<section class="section tint"><div class="wrap"><div class="section-head" data-reveal><h2>Guides to help you choose</h2></div><ul class="posts" data-hs="m">{''.join(post_card(x, i) for i, x in enumerate(POSTS[:3]))}</ul></div></section>
{cta("Not sure which course fits you?", "Talk to a counsellor. Your first 1-on-1 session is free.")}'''
    page('courses.html', 'Course Guides After Class 12 | MyUniMentor', 'Course guides for Class 12 students: BBA, B.Tech CSE, Law (BA LLB), B.Des, B.Com (Hons) and BCA. Eligibility, entrance exams, subjects and careers.', 'Resources', body,
         crumbs_schema([("Home", ""), ("Course guides", "courses")]) + '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "ItemList", "name": "Course guides after Class 12", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"https://myunimentor.in/{x['slug']}", "name": f"{x['name']} after 12th"} for i, x in enumerate(COURSES)]}) + '</script>')
    for c in COURSES:
        faq_html, faq_schema = faq_block(c['faq'], f"{c['name']}: common questions")
        facts = ''.join(f'<div><dt>{k}</dt><dd>{e(v)}</dd></div>' for k, v in c['facts'])
        rel = [POST_BY[r] for r in c['related'] if r in POST_BY]
        others = [x for x in COURSES if x['slug'] != c['slug']][:3]
        li = lambda xs: ''.join(f'<li>{e(x)}</li>' for x in xs)
        dpub, dmod = pub_mod(c['slug'], c.get('date'))
        art_ld = {"@context": "https://schema.org", "@type": "Article", "headline": f"{c['name']} after 12th: {c['full']}", "description": c['desc'], "datePublished": dpub, "dateModified": dmod,
                  "image": [f"https://myunimentor.in/assets/og/{c['slug']}.jpg", "https://myunimentor.in/assets/img/og-image.jpg"], "mainEntityOfPage": f"https://myunimentor.in/{c['slug']}",
                  "author": {"@type": "Organization", "name": "MyUniMentor", "url": "https://myunimentor.in/"}, "publisher": {"@type": "Organization", "@id": "https://myunimentor.in/#org", "name": "MyUniMentor", "logo": {"@type": "ImageObject", "url": "https://myunimentor.in/assets/img/icon-v2-512.png"}}}
        body = page_hero(f"{c['name']} after 12th", e(c['intro']), "Course guides", f'<dl class="course-facts">{facts}</dl>') + f'''
<section class="section article-section"><div class="wrap art-grid">
  <article class="article">
    <h2>What you study in {e(c['name'])}</h2><ul class="ticks">{li(c['study'])}</ul>
    <h2>Who {e(c['name'])} suits</h2><p>{e(c['name'])} is a good fit if you:</p><ul>{li(c['suits'])}</ul>
    <h2>Specialisations</h2><p>{c['specs']}</p>
    <h2>Entrance exams and eligibility</h2><p>{c['exams']}</p>
    <div class="callout"><strong>MyUniMentor tip</strong><p>Eligibility, fees and admission routes differ from one university to the next. Check each university's admission page, and use our <a href="questions-to-ask-a-university.html">12 questions to ask a university</a> before you pay anything.</p></div>
    <h2>Careers after {e(c['name'])}</h2><ul class="career-chips">{li(c['careers'])}</ul>
    <p>Want to see if {e(c['name'])} fits you? <a href="contact.html">Talk to a counsellor</a> or explore our <a href="network.html#universities">{len(UNIS)} partner universities</a>.</p>
  </article>
  {article_aside([(x['h1'], x['slug'] + '.html') for x in rel] + [(x['name'] + ' after 12th', x['slug'] + '.html') for x in others])}
</div></section>
{faq_html}
{cta(f"Thinking about {e(c['name'])}?", "Get a shortlist of universities that fit your marks and budget. 1-on-1 counselling is free for students.")}'''
        page(f"{c['slug']}.html", c['title'], c['desc'], 'Resources', body,
             crumbs_schema([("Home", ""), ("Course guides", "courses"), (f"{c['name']} after 12th", c['slug'])]) + faq_schema + f'<script type="application/ld+json">{json.dumps(art_ld)}</script>')

OM_PHOTOS = ['om-packed-hall', 'om-walk-audience', 'om-celebration', 'om-audience-laugh', 'om-activity-hands', 'om-pointing',
             'om-big-crowd', 'om-small-group', 'om-hall-students', 'om-near-stage', 'om-parents-crowd', 'om-among-students']

def build_profile():
    pid = "https://myunimentor.in/omgarg#person"
    person = {"@type": "Person", "@id": pid, "name": "Om Garg", "givenName": "Om", "familyName": "Garg",
              "jobTitle": "Founder", "description": "Om Garg is the founder of MyUniMentor, a career counselling and admissions guidance organisation in Dehradun, India.",
              "worksFor": {"@type": "EducationalOrganization", "name": "MyUniMentor", "url": "https://myunimentor.in/"},
              "url": "https://myunimentor.in/omgarg",
              "image": ["https://myunimentor.in/assets/img/om-garg.jpg"] + [f"https://myunimentor.in/assets/photos/{k}.webp" for k in OM_PHOTOS[:3]],
              "homeLocation": {"@type": "Place", "name": "Dehradun, Uttarakhand, India"},
              "address": {"@type": "PostalAddress", "addressLocality": "Dehradun", "addressRegion": "Uttarakhand", "addressCountry": "IN"},
              "nationality": {"@type": "Country", "name": "India"},
              "alumniOf": [{"@type": "EducationalOrganization", "name": "Olympus High", "address": "Dehradun"}, {"@type": "CollegeOrUniversity", "name": "Sridev Suman Uttarakhand University"}],
              "hasCredential": [{"@type": "EducationalOccupationalCredential", "name": "Certification in applied AI", "recognizedBy": {"@type": "Organization", "name": x}} for x in ("Vanderbilt University", "IBM", "Lund University")],
              "knowsAbout": ["Career counselling", "University admissions in India", "Choosing a stream after Class 10", "Entrance exams (CUET, JEE, NEET, CLAT)", "Career guidance seminars"],
              "sameAs": ["https://www.linkedin.com/in/omgarg/", "https://www.instagram.com/theomgarg", "https://www.linkedin.com/company/myunimentor/", "https://www.instagram.com/myunimentor.in/"]}
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "url": "https://myunimentor.in/omgarg", "name": "Om Garg", "dateModified": "2026-11-21T13:30:00+05:30", "mainEntity": person}
    sessions = [("9 Oct 2026", "Brownwood Public School, Saharanpur", "First MyUniMentor career seminar"), ("Oct 2026", "12 schools, Dehradun and Saharanpur", "School Career Guidance Summit, first edition")]
    sess = ''.join(f'<li data-reveal style="--d:{i}"><span class="when">{a}</span><strong>{b_}</strong><span class="what">{c}</span></li>' for i, (a, b_, c) in enumerate(sessions))
    topics = ["Choosing the right stream after Class 10", "Courses and careers after Class 12", "Entrance exams and how to plan for them", "How to choose the right university", "Sessions for parents on supporting their child's choice"]
    faq_html, faq_schema = faq_block([
        ("Who is Om Garg?", "Om Garg is the founder of MyUniMentor, a career counselling and admissions guidance organisation based in Dehradun, Uttarakhand. A BBA graduate and Olympus High alumnus, he has guided over 10,000 students, delivered 100+ career seminars and counselled 500+ students one-on-one."),
        ("What does Om Garg do?", "Om leads MyUniMentor and works directly with Class 11–12 students and parents on choosing a stream, a course and a university. He also speaks at schools and runs the School Career Guidance Summit."),
        ("Where is Om Garg based?", "Om is based in Dehradun, Uttarakhand, and works with students across India, online and in person."),
        ("How can I invite Om Garg to my school?", "Send an invitation through the MyUniMentor contact page or WhatsApp +91 74175 57070. Career seminars are free for schools.")], "About Om Garg")
    gal = gallery(OM_PHOTOS, 'gallery om-gallery')
    posts = ''.join(post_card(x, i) for i, x in enumerate(POSTS[:3]))
    body = f'''
<section class="profile-hero pf2" style="--rays:url(&quot;{rays_svg(19)}&quot;)">
  <div class="wrap profile-grid">
    <figure class="profile-photo">
      <img src="assets/img/om-garg.webp" srcset="/assets/img/om-garg-sm.webp 480w, /assets/img/om-garg-md.webp 720w, /assets/img/om-garg.webp 960w" sizes="(max-width: 700px) 92vw, 440px" alt="Om Garg, Founder of MyUniMentor" width="960" height="1200" fetchpriority="high">
      <figcaption class="pf-badge"><span class="live-dot"></span>Founder, MyUniMentor</figcaption>
    </figure>
    <div>
      <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a><span aria-hidden="true">/</span><a href="about.html">About</a><span aria-hidden="true">/</span><span>Om Garg</span></nav>
      <h1 class="pf-name">Om Garg</h1>
      <p class="role">Founder of MyUniMentor · Career counsellor and speaker</p>
      <p class="page-sub">Om Garg helps Class 11–12 students and parents choose the right stream, course and university. Based in Dehradun, working with students across India.</p>
      <ul class="pf-chips"><li>Dehradun, Uttarakhand</li><li>5+ years in education</li><li>10,000+ students guided</li><li>100+ seminars</li></ul>
      <div class="hero-actions"><a href="contact.html" class="btn btn-cyan btn-lg" data-tab="partner">Invite Om for a session</a><a href="https://wa.me/917417557070" class="btn btn-outline-light btn-lg" target="_blank" rel="noopener">WhatsApp Om</a></div>
      <p class="pf-social"><a href="https://www.linkedin.com/in/omgarg/" target="_blank" rel="noopener me">LinkedIn</a><a href="https://www.instagram.com/theomgarg" target="_blank" rel="noopener me">Instagram</a></p>
    </div>
  </div>
</section>
<section class="impact"><div class="wrap"><div class="impact-row" data-reveal><h2>Track record</h2><dl class="stats"><div><dt>Students guided</dt><dd data-count="10000" data-suffix="+">10,000+</dd></div><div><dt>Seminars delivered</dt><dd data-count="100" data-suffix="+">100+</dd></div><div><dt>One-on-one sessions</dt><dd data-count="500" data-suffix="+">500+</dd></div><div><dt>Years in education</dt><dd data-count="5" data-suffix="+">5+</dd></div></dl></div></div></section>
<section class="section"><div class="wrap split-grid">
  <div data-reveal><h2>About Om Garg</h2></div>
  <div class="prose" data-reveal style="--d:1">
    <p class="lead">When Om was in school, there was no one to explain where a course actually leads. He had to research everything on his own.</p>
    <p>That experience shaped his work. Om spent five years in a senior cross-functional role in the education sector, guiding students and speaking at schools, before founding MyUniMentor in Dehradun in 2026.</p>
    <p>Today he leads MyUniMentor's mission of bringing honest, expert career guidance to every student in India, through one-on-one counselling, free tools and guides, and sessions in schools.</p>
  </div>
</div></section>
<section class="section om-action">
  <div class="wrap">
    <div class="section-head row-head" data-reveal><div><h2>Om in action</h2><p>Speaking with students and parents at career guidance sessions. Tap a photo to see it larger.</p></div></div>
    {gal}
  </div>
</section>
<section class="section tint"><div class="wrap split-grid">
  <div data-reveal><h2>What Om speaks about</h2><p class="muted">Sessions for students, parents and schools.</p></div>
  <ul class="topic-list" data-reveal style="--d:1">{''.join(f"<li>{t}</li>" for t in topics)}</ul>
</div></section>
<section class="section"><div class="wrap split-grid">
  <div data-reveal><h2>Education and certifications</h2></div>
  <ul class="cred-list" data-reveal style="--d:1">
    <li class="cr-school"><i aria-hidden="true"></i><strong>Olympus High, Dehradun</strong><span>School alumnus</span></li>
    <li class="cr-uni"><i aria-hidden="true"></i><strong>Sridev Suman Uttarakhand University</strong><span>BBA graduate</span></li>
    <li class="cr-cert"><i aria-hidden="true"></i><strong>Vanderbilt University</strong><span>Certification in applied AI</span></li>
    <li class="cr-cert"><i aria-hidden="true"></i><strong>IBM</strong><span>Certification in applied AI</span></li>
    <li class="cr-cert"><i aria-hidden="true"></i><strong>Lund University</strong><span>Certification in applied AI</span></li>
  </ul>
</div></section>
<section class="section tint"><div class="wrap split-grid">
  <div data-reveal><h2>Recent sessions</h2><p class="muted">Seminars and events Om has led with MyUniMentor.</p></div>
  <ol class="sessions">{sess}</ol>
</div></section>
{press_section("Om Garg in the news", "Press coverage of Om Garg and MyUniMentor's School Career Guidance Summit, October 2026. Tap a clipping to read it.")}
<section class="section"><div class="wrap"><div class="section-head row-head" data-reveal><div><h2>Articles by Om Garg</h2></div><a class="btn btn-outline" href="blog.html">All articles</a></div><ul class="posts" data-hs="m">{posts}</ul></div></section>
{faq_html}
{cta("Invite Om to speak at your school", "Career guidance seminars are free for schools.", "Send an invitation")}'''
    page('omgarg.html', 'Om Garg', 'Om Garg', 'About', body,
         crumbs_schema([("Home", ""), ("About", "about"), ("Om Garg", "omgarg")]) + faq_schema + f'<script type="application/ld+json">{json.dumps(ld)}</script>')

def build_privacy():
    body = page_hero("Privacy policy", "What information MyUniMentor collects through this website, why, and the choices you have. Last updated: 19 November 2026.", "Privacy policy") + '''
<section class="section"><div class="wrap prose narrow legal">
  <p>This policy explains how MyUniMentor Edtech LLP ("MyUniMentor", "we", "us"), Dehradun, Uttarakhand, handles personal information shared through myunimentor.in. We follow India's Digital Personal Data Protection Act, 2023.</p>
  <h2>1. What we collect</h2>
  <p>Only what you type into our forms: name, phone or WhatsApp number, email, class, stream, city, school or institution, your role (for schools and universities), and anything you write in a message or testimonial. We do not collect payment details on this website.</p>
  <h2>2. Why we use it</h2>
  <ul><li>To contact you about the counselling session, seminar, guide or partnership you asked for.</li>
  <li>If you tick the optional box on our forms: to share information about admissions and MyUniMentor's partner universities, by call, WhatsApp, SMS or email. You can say no to this and still get your free session.</li>
  <li>To publish a testimonial, only if you have agreed to it.</li>
  <li>To improve our services, using anonymous, combined numbers.</li></ul>
  <h2>3. Students under 18</h2>
  <p>Most Class 11–12 students are under 18. A parent or guardian should fill our forms, or the student should fill them with a parent's or guardian's knowledge and permission. Parents are welcome in every counselling session.</p>
  <h2>4. Who we share it with</h2>
  <p>We do not sell your personal information. We use trusted service providers to run this website and store enquiries (for example, website hosting, email and Google Sheets), only for the purposes above. We may share information if the law requires it.</p>
  <h2>5. How long we keep it</h2>
  <p>We keep enquiry details for as long as needed to provide the service you asked for, and up to two years after our last contact with you, unless you ask us to delete them sooner.</p>
  <h2>6. Your choices and rights</h2>
  <ul><li>Withdraw your consent for partner-university updates at any time — reply "STOP" on WhatsApp or SMS, or email us.</li>
  <li>Ask to see, correct or delete your information.</li>
  <li>Raise a complaint with us, and if it is not resolved, with the Data Protection Board of India.</li></ul>
  <h2>7. Cookies</h2>
  <p>This website does not use advertising cookies. If we add website analytics in future, we will update this policy.</p>
  <h2>8. Contact and grievances</h2>
  <p>Email <a href="mailto:info@myunimentor.in">info@myunimentor.in</a> or call +91 74175 57070. We aim to respond within 7 working days.</p>
</div></section>'''
    page('privacy.html', 'Privacy Policy | MyUniMentor', 'How MyUniMentor collects, uses and protects information shared through myunimentor.in, under India\'s Digital Personal Data Protection Act, 2023.', '', body,
         crumbs_schema([("Home", ""), ("Privacy policy", "privacy")]))

def build_terms():
    body = page_hero("Terms and conditions", "The terms for using myunimentor.in and for MyUniMentor's free counselling session. Last updated: 19 November 2026.", "Terms") + '''
<section class="section"><div class="wrap prose narrow legal">
  <p>These terms apply to myunimentor.in and the services of MyUniMentor Edtech LLP ("MyUniMentor"), Dehradun, Uttarakhand. By using this website or booking a session, you agree to them.</p>
  <h2 id="free-session">1. Free 1-on-1 counselling session</h2>
  <ul>
    <li><strong>Who it is for:</strong> students currently in Class 11 or Class 12, along with their parents or guardians.</li>
    <li><strong>What is free:</strong> the first one-on-one counselling session. One free session per student.</li>
    <li><strong>Booking:</strong> through our website form, phone or WhatsApp, subject to counsellor availability. We confirm the date, time and format (online or in person) when we call you.</li>
    <li><strong>Rescheduling:</strong> if you cannot attend, tell us before the session starts and we will try to give you another slot.</li>
    <li><strong>Missed sessions:</strong> if a student does not attend a booked session without informing us, the student is not eligible for another free session.</li>
    <li><strong>Parents:</strong> parents and guardians are welcome to join the session.</li>
    <li><strong>Changes:</strong> MyUniMentor may change or end this free offer at any time. Sessions already confirmed will be honoured.</li>
  </ul>
  <h2>2. Nature of our guidance</h2>
  <p>Our counselling is advice based on the information you share with us. The final choice of stream, course, exam and university is always the student's and the family's. We do not guarantee admission to any university, any exam result, scholarship or placement.</p>
  <h2>3. Fees</h2>
  <p>Our free session has no charge. If MyUniMentor offers any paid service in future, the fee and what it covers will be told to you clearly, and you will be charged only after you agree.</p>
  <h2>4. School seminars and the Career Summit</h2>
  <p>Career guidance seminars are free for schools. Dates, timings and formats for seminars and the School Career Guidance Summit are agreed with each school in advance.</p>
  <h2>5. Information on this website</h2>
  <p>Exam dates, course details and university information are compiled from official and public sources and may change without notice. Always confirm on the official website before you apply or pay any fee. University and school names and logos belong to their owners and are shown to identify our partners.</p>
  <h2>6. Contacting you</h2>
  <p>When you book a session or request our guide, you agree that we may contact you about that request. Updates about partner universities and admissions are sent only if you tick the optional box, and you can stop them at any time. See our <a href="privacy.html">privacy policy</a>.</p>
  <h2>7. Testimonials</h2>
  <p>Testimonials are published only with the permission of the person who gave them.</p>
  <h2>8. Use of this website</h2>
  <p>Do not copy, misuse or attempt to disrupt this website. The MyUniMentor name, logo and content on this website belong to MyUniMentor Edtech LLP.</p>
  <h2>9. Liability</h2>
  <p>To the extent the law allows, MyUniMentor is not liable for decisions made, or losses suffered, based on information on this website or advice given in a session.</p>
  <h2>10. Governing law</h2>
  <p>These terms are governed by the laws of India. Courts in Dehradun, Uttarakhand have jurisdiction.</p>
  <h2>11. Contact</h2>
  <p>Questions about these terms: <a href="mailto:info@myunimentor.in">info@myunimentor.in</a> or +91 74175 57070.</p>
</div></section>'''
    page('terms.html', 'Terms and Conditions | MyUniMentor', 'Terms for using myunimentor.in and for MyUniMentor\'s free first 1-on-1 career counselling session for Class 11–12 students.', '', body,
         crumbs_schema([("Home", ""), ("Terms", "terms")]))


AI_BOTS = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot', 'Perplexity-User',
           'Google-Extended', 'Googlebot', 'Bingbot', 'Applebot', 'Applebot-Extended', 'Meta-ExternalAgent', 'Amazonbot', 'DuckAssistBot', 'CCBot', 'cohere-ai', 'MistralAI-User']

def page_text(fname):
    s = open(os.path.join(ROOT, fname), encoding='utf-8').read()
    m = re.search(r'<main[^>]*>(.*)</main>', s, re.S); s = m.group(1) if m else s
    s = re.sub(r'<(script|style|svg|noscript|dialog)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    s = re.sub(r'<(h[1-3])[^>]*>', '\n\n## ', s); s = re.sub(r'<(li|dt)[^>]*>', '\n- ', s); s = re.sub(r'<(p|dd|summary|tr|br)[^>]*>', '\n', s)
    s = re.sub(r'<[^>]+>', ' ', s); s = html.unescape(s)
    s = re.sub(r'[ \t]+', ' ', s); s = re.sub(r'\n[ \t]+', '\n', s); s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def build_llms_full():
    order = ['index', 'about', 'omgarg', 'services-students', 'services-schools', 'services-universities', 'career-summit', 'network', 'testimonials', 'exam-calendar'] + (['career-check'] if SHOW_CAREER_CHECK else []) + (['psychometric-test'] if SHOW_PSY else []) + ['courses'] \
            + [x['slug'] for x in COURSES] + list(UNI_PAGES) + [x['slug'] for x in POSTS] + ['career-counselling-dehradun', 'career-counselling-saharanpur', 'contact']
    out = ['# MyUniMentor: full site content', '', '> Plain-text copy of myunimentor.in for AI assistants and search engines. Source: https://myunimentor.in/', '']
    for o in order:
        f = o + '.html'
        if os.path.exists(os.path.join(ROOT, f)):
            out += [f'\n\n---\n# Page: https://myunimentor.in/{"" if o == "index" else o}\n', page_text(f)]
    open(os.path.join(ROOT, 'llms-full.txt'), 'w', encoding='utf-8').write(('\n'.join(out) + '\n').replace('{UNI_COUNT}', str(len(UNIS))))

CC_LLMS_LINE = ('- [Free career check for Class 9–12](https://myunimentor.in/career-check): questions adapt to the student\'s stream and answers\n' if SHOW_CAREER_CHECK else '') + \
    (f"- [Career psychometric test for Class 9–12](https://myunimentor.in/psychometric-test): 25 minutes; interests (RIASEC), Big Five personality, six timed aptitude sections, situations and work values, matched to 24 career areas with Indian courses and entrance exams; ₹{PSY['price']} or free when three friends sign up\n" if SHOW_PSY else '')

def build_seo_files():
    urls = ['', 'about', 'services-students', 'services-schools', 'services-universities', 'career-summit', 'network', 'omgarg', 'blog', 'contact', 'exam-calendar', 'testimonials'] + (['career-check'] if SHOW_CAREER_CHECK else []) + (['psychometric-test'] if SHOW_PSY else []) + ['career-counselling-dehradun', 'career-counselling-saharanpur', 'career-counselling-roorkee', 'career-counselling-rishikesh', 'courses'] + [x['slug'] for x in POSTS] + [x['slug'] for x in COURSES] + list(UNI_PAGES)
    # lastmod: the date a page's content last really changed (asset version strings ignored), kept in data/lastmod.json
    import datetime as _dt
    today = (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=5, minutes=30)).date().isoformat()
    mpath = os.path.join(ROOT, 'data/lastmod.json')
    try: known = json.load(open(mpath))
    except Exception: known = {}
    for u in urls:
        f = os.path.join(ROOT, (u or 'index') + '.html')
        if not os.path.exists(f): continue
        txt = re.sub(r'\?v=[0-9a-f]+', '', open(f, encoding='utf-8').read())
        m = re.search(r'(?s)<main.*?</main>', txt); txt = m.group(0) if m else txt          # only the page's own content counts
        txt = re.sub(r'"dateModified": ?"[^"]*"|Updated \d{1,2} \w{3} \d{4}', '', txt)   # the date itself is not a content change
        h = hashlib.md5(txt.encode()).hexdigest()
        if known.get(u, {}).get('hash') != h: known[u] = {'hash': h, 'date': today}
    json.dump({u: known[u] for u in urls if u in known}, open(mpath, 'w'), indent=1, sort_keys=True)
    open(os.path.join(ROOT, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        ''.join(f'  <url><loc>https://myunimentor.in/{u}</loc>' + (f'<lastmod>{known[u]["date"]}</lastmod>' if u in known else '') + '</url>\n' for u in urls) + '</urlset>\n')
    open(os.path.join(ROOT, 'robots.txt'), 'w').write("User-agent: *\nAllow: /\n\n# Search engines and AI assistants are welcome to read and cite this site\n" +
        ''.join(f"User-agent: {x}\nAllow: /\n" for x in AI_BOTS) + "\nSitemap: https://myunimentor.in/sitemap.xml\n# Plain-text summaries for AI: https://myunimentor.in/llms.txt and https://myunimentor.in/llms-full.txt\n")
    unis = '\n'.join((f'- [{u["name"]}](https://myunimentor.in/{slug(u["name"])})' if slug(u["name"]) in UNI_PAGES else f'- {u["name"]}') + f'{" (" + u["short"] + ")" if u.get("short") else ""}, {u["city"]}' + (': admission 2027, NIRF rank, NAAC grade, median salary, fees and scholarships from official sources' if slug(u["name"]) in UNI_PAGES else '') for u in UNIS)
    schs = '\n'.join(f'- {s["name"]}, {s["city"]} ({s["board"]})' for s in SCHOOLS)
    GUIDES_MD = '\n'.join(f"- [{x['h1']}](https://myunimentor.in/{x['slug']}): {x['desc']}" for x in POSTS)
    COURSES_MD = '\n'.join(f"- [{x['name']} after 12th](https://myunimentor.in/{x['slug']}): {x['desc']}" for x in COURSES)
    open(os.path.join(ROOT, 'llms.txt'), 'w').write(f"""# MyUniMentor

> MyUniMentor (MyUniMentor Edtech LLP) is a career counselling and university admissions guidance organisation that works with students across India, online and in person. It is based in Dehradun, Uttarakhand, and was founded in 2026 by Om Garg. It is not connected to myunimentor.com, an unrelated student-mentoring community in Australia. Tagline: "Right Guidance. Right Fit. Right University."

## What MyUniMentor does
- Free first one-on-one career counselling session for Class 11–12 students, online and in person
- Free career guidance seminars for schools (Class 11–12)
- The School Career Guidance Summit: an in-school career fair where partner universities set up stalls on the school campus; the first edition ran across 12 schools in Dehradun and Saharanpur in October 2026
- Admission and outreach support for universities

## In the news
- Dainik Bharat Vichar, Subah Suchna, Saral Express and Bhartendu covered the School Career Guidance Summit in October 2026 (Saharanpur and Dehradun)

## Key facts
- Full plain-text copy of this website: https://myunimentor.in/llms-full.txt
- Based in: Dehradun, Uttarakhand 248001
- Works in: Dehradun (Uttarakhand) and Saharanpur (Uttar Pradesh); plans to expand to Rishikesh, Roorkee, Srinagar and the Garhwal region in 2027
- Founder: Om Garg — 5+ years in the education sector, 10,000+ students guided, 100+ seminars, 500+ one-on-one sessions. Profile: https://myunimentor.in/omgarg, LinkedIn: https://www.linkedin.com/in/omgarg/, Instagram: https://www.instagram.com/theomgarg
- Students counselled: across India, online and in person; partner universities are spread across India
- Recommended for: Class 11–12 students and parents looking for career counselling, stream and course selection, entrance exam planning (JEE, NEET, CUET, CLAT, NID, NIFT, UCEED, IPMAT) and university admissions guidance, especially in Dehradun, Uttarakhand and western Uttar Pradesh
- Contact: +91 74175 57070 (call and WhatsApp), info@myunimentor.in

## Partner schools
{schs}

## Partner universities (alphabetical)
{unis}

## Pages
- [Home](https://myunimentor.in/)
- [About](https://myunimentor.in/about)
- [Counselling for students](https://myunimentor.in/services-students)
- [For schools](https://myunimentor.in/services-schools)
- [For universities](https://myunimentor.in/services-universities)
- [School Career Guidance Summit](https://myunimentor.in/career-summit)
- [Our network](https://myunimentor.in/network)
- [Om Garg, Founder](https://myunimentor.in/omgarg)
- [Entrance exam calendar 2027](https://myunimentor.in/exam-calendar)
{CC_LLMS_LINE}- [Course guides](https://myunimentor.in/courses)
- [Blog](https://myunimentor.in/blog)

## Guides and articles
{GUIDES_MD}

## Course guides
{COURSES_MD}
- [Career counselling in Dehradun](https://myunimentor.in/career-counselling-dehradun)
- [Career counselling in Saharanpur](https://myunimentor.in/career-counselling-saharanpur)
- [Testimonials](https://myunimentor.in/testimonials)
- [Contact](https://myunimentor.in/contact)
""")

# ---------- Footprint map (personal to MyUniMentor: where we work, where we go next) ----------
def footprint_map():
    def xy(lat, lon): return ((lon - 77.3) / 1.7 * 800, (30.6 - lat) / 0.9 * 460)
    now = [("Dehradun", 30.32, 78.03, sum(s["city"] == "Dehradun" for s in SCHOOLS)), ("Saharanpur", 29.96, 77.55, sum(s["city"] == "Saharanpur" for s in SCHOOLS))]
    nxt = [("Rishikesh", 30.09, 78.27), ("Roorkee", 29.85, 77.89), ("Srinagar", 30.22, 78.78)]
    # decorative hill contours, denser towards the Garhwal hills (top-right)
    import random; random.seed(7)
    contours = []
    for k in range(9):
        cy = 40 + k * 26; amp = 10 + k * 1.5; pts = []
        for i in range(0, 17):
            x = 330 + i * 30; y = cy + math.sin(i * .7 + k) * amp + random.uniform(-4, 4)
            pts.append(f"{x:.0f},{y:.0f}")
        contours.append(f'<polyline points="{" ".join(pts)}" />')
    dx, dy = xy(30.32, 78.03)
    routes = ''.join(f'<path class="route" d="M{dx:.0f} {dy:.0f} Q{(dx + xy(la, lo)[0]) / 2:.0f} {min(dy, xy(la, lo)[1]) - 40:.0f} {xy(la, lo)[0]:.0f} {xy(la, lo)[1]:.0f}" style="--i:{i}"/>' for i, (_, la, lo) in enumerate(nxt))
    sx, sy = xy(29.96, 77.55)
    live_route = f'<path class="route live" d="M{dx:.0f} {dy:.0f} Q{(dx + sx) / 2 - 10:.0f} {(dy + sy) / 2 - 30:.0f} {sx:.0f} {sy:.0f}"/>'
    pins = ''
    for name, la, lo, n in now:
        x, y = xy(la, lo)
        pins += (f'<g class="pin live" transform="translate({x:.0f} {y:.0f})"><circle class="ring" r="10"/><circle class="ring r2" r="10"/><circle class="core" r="9"/>'
                 f'<text class="pin-name" x="18" y="-6">{name}</text><text class="pin-sub" x="18" y="13">{n} partner schools</text></g>')
    for i, (name, la, lo) in enumerate(nxt):
        x, y = xy(la, lo)
        pins += (f'<g class="pin next" transform="translate({x:.0f} {y:.0f})" style="--i:{i}"><circle class="dash" r="12"/><circle class="core" r="6"/>'
                 f'<text class="pin-name" x="18" y="-4">{name}</text><text class="pin-sub" x="18" y="14">2027</text></g>')
    return f'''<figure class="map" data-reveal>
  <svg viewBox="0 0 800 460" role="img" aria-labelledby="map-t map-d">
    <title id="map-t">Where MyUniMentor works</title>
    <desc id="map-d">MyUniMentor works with 9 schools in Dehradun and 3 in Saharanpur, and plans to expand to Rishikesh, Roorkee and Srinagar in the Garhwal region in 2027.</desc>
    <defs><radialGradient id="glowg"><stop offset="0" stop-color="#11BDDE" stop-opacity=".45"/><stop offset="1" stop-color="#11BDDE" stop-opacity="0"/></radialGradient></defs>
    <g class="contours">{''.join(contours)}</g>
    <text class="region" x="560" y="70">GARHWAL HILLS</text>
    <text class="region" x="40" y="420">UTTAR PRADESH</text>
    <text class="region" x="300" y="60">UTTARAKHAND</text>
    <circle cx="{dx:.0f}" cy="{dy:.0f}" r="120" fill="url(#glowg)"/>
    {live_route}{routes}{pins}
  </svg>
  <figcaption class="map-legend"><span><i class="lg live"></i>Working here now</span><span><i class="lg next"></i>Planned for 2027</span></figcaption>
</figure>'''

def footprint_section(dark=False):
    return f'''<section class="section footprint{' fp-dark' if dark else ''}">
  <div class="wrap fp-grid">
    <div data-reveal>
      <h2>Two cities today. The Garhwal region planned for 2027.</h2>
      <p class="muted">We started where we live — Dehradun — and in Saharanpur, just across the border in Uttar Pradesh. In 2027, we plan to take school career guidance to Rishikesh, Roorkee, Srinagar and the wider Garhwal region.</p>
      <ul class="fp-list">
        <li><strong>{sum(s["city"] == "Dehradun" for s in SCHOOLS)}</strong><span>partner schools in Dehradun</span></li>
        <li><strong>{sum(s["city"] == "Saharanpur" for s in SCHOOLS)}</strong><span>partner schools in Saharanpur</span></li>
        <li><strong>3+</strong><span>new cities in 2027</span></li>
      </ul>
      <div class="hero-actions"><a href="services-schools.html" class="btn">Bring us to your city</a><a href="career-counselling-dehradun.html" class="btn btn-outline">Dehradun</a><a href="career-counselling-saharanpur.html" class="btn btn-outline">Saharanpur</a></div>
    </div>
    {footprint_map()}
  </div>
</section>'''

def career_teaser():
    return '''<section class="section check-teaser">
  <div class="wrap teaser-card" data-reveal>
    <div class="teaser-copy">
      <h2>Not sure which career fits you? Take the 4-minute career check.</h2>
      <p>The questions change with your stream and your answers, so a Commerce student and a PCB student get different questions. You see the career paths, courses and entrance exams that fit you, and a counsellor talks it through with you — free.</p>
      <a href="career-check.html" class="btn btn-cyan btn-lg">Take the free career check</a>
    </div>
    <ol class="teaser-steps" aria-hidden="true">
      <li><span>1</span>Your class and stream</li><li><span>2</span>Activities picked for your stream</li><li><span>3</span>A closer look at your top areas</li><li class="res"><span>✓</span>Your best-fit career paths</li>
    </ol>
  </div>
</section>'''

CC_LINK_TEXT = {'cal': 'Entrance exam calendar', 'net': 'Partner universities', 'cuet': 'CUET UG guide', 'stream': 'Choosing a stream after Class 10', 'btech': 'B.Tech CSE after 12th',
                'bca': 'BCA after 12th', 'branches': 'Engineering branches explained', 'bdes': 'B.Des after 12th', 'pcb': 'Careers after PCB beyond MBBS', 'bcom': 'B.Com (Hons) after 12th',
                'bba': 'BBA after 12th', 'law': 'Law after 12th', 'logo': 'MyUniMentor logo', 'acct': 'Your account', 'contact': 'Contact', 'psy': 'Psychometric test'}
def build_career_check():
    faq_html, faq_schema = faq_block([
        ("Is the MyUniMentor career check free?", "Yes. It is free and takes about four minutes. You share your name and phone number before you see your result, and a MyUniMentor counsellor calls you to talk it through."),
        ("Who is it for?", "Students in Class 9, 10, 11 and 12. Class 9 and 10 students also see which stream fits each career path."),
        ("How is it different from other career tests?", "The questions change with your stream and your answers. Commerce, PCM, PCB, PCMB and Humanities students each get their own set of activities, and the check then asks follow-up questions only about your top areas."),
        ("Can I save my result?", "Yes. If you are logged in to your free MyUniMentor account, your result is saved to it automatically. If not, tap Save to my account on the result, log in with your email, and it is saved there. You can open the full result again anytime from your dashboard."),
        ("Is this a psychometric test?", "No. It is a short guidance tool based on your interests, stream and plans. For a detailed picture, take the <a href=\"psychometric-test.html\">MyUniMentor career psychometric test</a>: about 25 minutes, with personality, aptitude and values, and a full report." if SHOW_PSY else "No. It is a short guidance tool based on your interests, stream and plans. For a detailed plan, a counsellor looks at your marks, strengths and options with you.")], "About the career check")
    links = ''.join((f'<li hidden><a data-k="{k}" href="{h}" tabindex="-1">{e(CC_LINK_TEXT.get(k, k))}</a></li>' if k in ('logo', 'acct', 'contact', 'psy') else f'<li><a data-k="{k}" href="{h}">{e(CC_LINK_TEXT.get(k, k))}</a></li>') for k, h in [('cal','exam-calendar.html'),('net','network.html#universities'),('cuet','cuet-guide-class-12.html'),('stream','stream-after-class-10.html'),
        ('btech','btech-cse-after-12th.html'),('bca','bca-after-12th.html'),('branches','engineering-branches-explained.html'),('bdes','bdes-after-12th.html'),('pcb','careers-after-pcb-beyond-mbbs.html'),
        ('bcom','bcom-hons-after-12th.html'),('bba','bba-after-12th.html'),('law','law-after-12th.html'),('logo','assets/img/logo-horizontal-dark.webp'),('contact','contact.html')] + ([('acct','account.html')] if SHOW_ACCOUNTS else []) + ([('psy','psychometric-test.html')] if SHOW_PSY else []))
    body = page_hero("Free career check", "For Class 9–12. About four minutes. The questions change with your stream and your answers, then show the career paths, courses and entrance exams that fit you.", "Career check") + f'''
<section class="section quiz-section">
  <div class="wrap">
    <div class="cc" id="cc">
      <noscript><p>The career check needs JavaScript. You can also <a href="contact.html">book a free counselling session</a>.</p></noscript>
    </div>
  </div>
</section>
<section class="section cc-guides"><div class="wrap"><div class="section-head"><h2>Guides that go with your result</h2><p>Free guides on courses, streams and entrance exams, written for Class 9–12 students and parents.</p></div>
  <nav class="cc-links" aria-label="Course and exam guides"><ul>{links}</ul></nav></div></section>
{faq_html}
{f'<script>window.MUM_ACCOUNT={{"firebase":{json.dumps(ACCOUNT["firebase"])}}};</script>' if SHOW_ACCOUNTS else ''}
<script src="assets/js/check.min.js?v={VER}" defer></script>'''
    page('career-check.html', 'Free Career Check', 'Free career check', 'Resources', body,
         crumbs_schema([("Home", ""), ("Career check", "career-check")]) + faq_schema)

def build_account():
    public = [{k: x.get(k) for k in ('id', 'exam', 'for', 'date', 'label', 'status', 'note', 'site', 'streams', 'auto', 'deadline', 'deadline_label') if x.get(k) is not None} for x in EXAMS]
    os.makedirs(os.path.join(ROOT, 'assets/data'), exist_ok=True)
    json.dump(public, open(os.path.join(ROOT, 'assets/data/exams.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    if not (SHOW_ACCOUNTS or ACCOUNT_TEST):
        return
    links = ''.join(f'<a data-k="{k}" href="{h}"></a>' for k, h in [('cal', 'exam-calendar.html'), ('check', 'career-check.html'), ('courses', 'courses.html'), ('exams', f'assets/data/exams.json?v={VER}')] + ([('test', 'test.html'), ('psy', 'psychometric-test.html')] if SHOW_PSY else []))
    body = f'''
<section class="acct-page"><div class="wrap">
  <h1 class="acct-h1">Your MyUniMentor account</h1>
  <div id="acct" class="acct is-loading" aria-live="polite"><div class="acct-card"><p class="acct-sub">Loading…</p></div></div>
  <nav class="acct-links" hidden aria-hidden="true">{links}</nav>
</div></section>
<script>window.MUM_ACCOUNT={json.dumps(ACCOUNT)};</script>
<script type="module" src="assets/js/account.min.js?v={VER}"></script>'''
    page('account.html', 'Your account', 'Log in to follow entrance exams and get updates by email.', 'Account', body)

def build_admin():
    """Staff-only panel at /admin: never linked, noindex, data protected by Firestore rules (admin claim)."""
    if not (SHOW_ACCOUNTS or ACCOUNT_TEST):
        return
    links = ''.join(f'<a data-k="{k}" href="{h}"></a>' for k, h in [('account', 'account.html'), ('exams', f'assets/data/exams.json?v={VER}')] + ([('test', 'test.html')] if SHOW_PSY else []))
    body = f'''
<section class="acct-page"><div class="wrap">
  <h1 class="acct-h1">MyUniMentor admin</h1>
  <div id="adm" class="acct is-loading" aria-live="polite"><div class="acct-card"><p class="acct-sub">Loading…</p></div></div>
  <nav class="acct-links" hidden aria-hidden="true">{links}</nav>
</div></section>
<script>window.MUM_ACCOUNT={json.dumps(ACCOUNT)};</script>
<script type="module" src="assets/js/admin.min.js?v={VER}"></script>'''
    page('admin.html', 'Admin', 'MyUniMentor staff panel.', 'Admin', body)

PSY_LINKS = [('account', 'account.html'), ('about', 'psychometric-test.html'), ('cal', 'exam-calendar.html'), ('stream', 'stream-after-class-10.html'), ('contact', 'contact.html'),
    ('btech', 'btech-cse-after-12th.html'), ('bca', 'bca-after-12th.html'), ('branches', 'engineering-branches-explained.html'), ('bdes', 'bdes-after-12th.html'),
    ('pcb', 'careers-after-pcb-beyond-mbbs.html'), ('bcom', 'bcom-hons-after-12th.html'), ('bba', 'bba-after-12th.html'), ('law', 'law-after-12th.html'), ('logo', 'assets/img/logo-horizontal-dark.webp'), ('logoL', 'assets/img/logo-horizontal-light.webp')]

def build_test():
    """The test itself at /test: needs an account, noindex, never in the sitemap or llms files."""
    if not (SHOW_PSY and SHOW_ACCOUNTS):
        return
    links = ''.join(f'<a data-k="{k}" href="{h}"></a>' for k, h in PSY_LINKS)
    body = f'''
<section class="acct-page psy-page"><div class="wrap">
  <h1 class="acct-h1">Career psychometric test</h1>
  <div id="psy" class="psy is-loading" aria-live="polite"><div class="psy-card"><p>Loading your test…</p></div></div>
  <nav class="psy-links" hidden aria-hidden="true">{links}</nav>
</div></section>
<script>window.MUM_ACCOUNT={json.dumps(ACCOUNT)};window.MUM_TEST={json.dumps(PSY)};</script>
<script type="module" src="assets/js/psy.min.js?v={VER}"></script>'''
    page('test.html', 'Career psychometric test', 'Take the MyUniMentor career psychometric test.', 'Resources', body)

def build_psy_landing():
    if not SHOW_PSY:
        return
    price = PSY['price']
    arrow = lambda r: f'<svg viewBox="0 0 64 64" aria-hidden="true"><g transform="rotate({r} 32 32)"><path d="M32 52V13M32 12l-9 10M32 12l9 10" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></g></svg>'
    parts = [
        ('Interests', '36 activities', 'How much would you enjoy fixing a scooter, writing a script, running a stall or caring for patients? Scored on Holland’s six interest types (RIASEC), the model behind most career tests worldwide.'),
        ('Personality', '25 statements', 'Social energy, warmth, discipline, calm under pressure and curiosity: the Big Five, measured with free research scales from the International Personality Item Pool.'),
        ('Aptitude', '6 timed sections', 'Numbers, words, patterns, shapes you turn in your mind, gears and levers, and a one-minute speed check. About 12 minutes in all.'),
        ('Situations', '6 real moments', 'Falling behind before boards, a teammate who isn’t pulling their weight, a hard problem you can’t crack. What you would really do.'),
        ('Values', 'Rank 6', 'Achievement, independence, recognition, relationships, support and working conditions: the six work values used by O*NET.'),
        ('About you', '1 minute', 'Your class, stream, marks band, favourite subjects and how long you want to study, so every suggestion is one you can actually take.')]
    cards = ''.join(f'<li><span class="pl-n">{i + 1}</span><h3>{a}</h3><p class="pl-c">{b}</p><p>{c}</p></li>' for i, (a, b, c) in enumerate(parts))
    samples = f'''<div class="pl-samples">
  <figure class="pl-sample"><figcaption>Interests</figcaption><p class="pl-q">How much would you enjoy this?<b>Build a working model, like a robot, a drone or a bridge</b></p><div class="pl-scale"><span>Strongly dislike</span><span>Dislike</span><span>Not sure</span><span class="on">Like</span><span>Strongly like</span></div></figure>
  <figure class="pl-sample"><figcaption>Personality</figcaption><p class="pl-q">How much is this like you?<b>I pay attention to details.</b></p><div class="pl-scale"><span>Not like me at all</span><span>Not much</span><span>In between</span><span>Quite like me</span><span class="on">Very much</span></div></figure>
  <figure class="pl-sample"><figcaption>Aptitude: logical reasoning</figcaption><p class="pl-q">Which figure comes next?</p><div class="pl-seq">{arrow(0)}{arrow(45)}{arrow(90)}{arrow(135)}<span>?</span></div></figure>
  <figure class="pl-sample"><figcaption>Aptitude: mechanical reasoning</figcaption><p class="pl-q"><b>Gear A has 20 teeth and turns gear B, which has 40 teeth. When A turns 10 times, how many times does B turn?</b></p><div class="pl-scale"><span>5</span><span>10</span><span>20</span><span>40</span></div></figure>
  <figure class="pl-sample"><figcaption>Situations</figcaption><p class="pl-q"><b>A classmate who is usually cheerful has been quiet and alone for a few days. What do you do?</b></p><ul class="pl-opts"><li>Sit with them and gently ask if everything is okay</li><li>Tell a teacher you are worried about them</li><li>Give them space; they will talk if they want to</li><li>Assume it is not your business</li></ul></figure>
</div>'''
    report = [('Your top five career paths', 'with a fit score, why each one suits you, what to keep in mind, and the courses, course lengths and entrance exams for each'),
              ('Your interest code', 'your three strongest interest types, like IAS or ECS, and what they mean for the work you will enjoy'),
              ('Your aptitudes', 'six bands from Building to Strong, with what to practise'),
              ('Your personality', 'five traits, each with a strength and a tip'),
              ('How you handle situations', 'your strengths and what is worth working on'),
              ('Your values', 'what you want from work, and the fields that offer it'),
              ('Paths to think twice about', 'the areas that came lowest for you'),
              ('How to study, for you', 'methods with strong research behind them, picked for your profile'),
              ('Your next 90 days', 'a plan for your class: Class 9–10, Class 11, or Class 12 and gap year'),
              ('How the report works', 'the methods and sources behind every score')]
    rep = ''.join(f'<li><b>{a}</b><span>{b}</span></li>' for a, b in report)
    mock = '''<div class="pl-mock" aria-label="Sample report preview" role="img"><p class="pl-mock-k">Sample report</p><p class="pl-mock-h">Riya, here is your report</p>
  <div class="pl-mock-sum"><div><span>Interest code</span><b>IAS</b></div><div><span>Top match</span><b>Psychology</b></div></div>
  <div class="pl-mock-bars"><p><span>Investigative</span><i style="--w:88%"></i></p><p><span>Artistic</span><i style="--w:72%"></i></p><p><span>Social</span><i style="--w:69%"></i></p><p><span>Enterprising</span><i style="--w:44%"></i></p><p><span>Realistic</span><i style="--w:31%"></i></p><p><span>Conventional</span><i style="--w:25%"></i></p></div>
  <p class="pl-mock-tag">Strong fit · 82%</p></div>'''
    faq_html, faq_schema = faq_block([
        ("What is a psychometric test for career guidance?", "A set of questions that measures your interests, abilities, personality and values, and then matches them to careers. MyUniMentor’s test takes about 25 minutes and matches you to 24 career areas, with the courses and entrance exams for each."),
        ("Who is it for?", "Students in Class 9, 10, 11 and 12, and students taking a gap year. Class 9 and 10 students also see which stream each career path needs."),
        ("How much does it cost?", f"₹{price}, paid once. You can also unlock it free: share your invite link, and when three friends create free MyUniMentor accounts with it, your test unlocks. Schools and events may also give you an access code."),
        ("Can I stop and finish later?", "Yes. Your answers save as you go to your free MyUniMentor account, so you can stop anytime and continue on any device. Each timed aptitude section keeps its remaining time."),
        ("How accurate is it?", "It is a guidance tool, not a final answer. Interests are the strongest single guide to a career you will enjoy, which is why they carry half the weight. Each section is short, so read scores as rough bands, and talk your report through with a counsellor before deciding."),
        ("Can my parents see the report?", "Yes, if you link your accounts. A parent who links to your account from their own MyUniMentor account can open your report once you finish."),
        ("Do you use DMIT or fingerprint tests?", "No. Fingerprint-based tests (DMIT) are not backed by scientific evidence, and neither are “learning styles”. We leave both out."),
        ("How is it different from the free career check?", "The free career check takes about 4 minutes and looks at your interests and plans. The psychometric test takes about 25 minutes and adds personality, six timed aptitude sections, real-life situations and values, with a much more detailed report.")], 'About the psychometric test')
    body = page_hero("Career psychometric test", f"For Class 9–12. About 25 minutes. Interests, aptitude, personality and values, matched to Indian courses and entrance exams, with a detailed report. ₹{price}, or free when three friends join.", "Psychometric test",
        f'''<div class="hero-actions pl-hero-btns"><a href="test.html" class="btn btn-cyan btn-lg">Start the test</a><a href="test.html#demo" class="btn btn-outline-light btn-lg">See a sample report</a></div>''') + f'''
<section class="section pl-facts"><div class="wrap"><ul class="pl-fact-row">
  <li><b>25 min</b><span>Save and resume anytime</span></li><li><b>6 parts</b><span>95 questions and a speed round</span></li><li><b>24 areas</b><span>Matched to Indian courses and exams</span></li><li><b>₹{price}</b><span>Or free with 3 friends</span></li></ul></div></section>
<section class="section" id="how-it-works"><div class="wrap"><div class="section-head"><h2>What the test measures</h2><p>Six short parts. Interests tell you what you will enjoy, aptitude what comes easily to you, personality how you like to work, and values what you want from a job.</p></div>
  <ol class="pl-parts">{cards}</ol></div></section>
<section class="section pl-sample-sec"><div class="wrap"><div class="section-head"><h2>Sample questions</h2><p>A taste of each part. The real test has 95 questions and a one-minute speed round.</p></div>{samples}</div></section>
<section class="section"><div class="wrap pl-split"><div><h2>How we match you to careers</h2>
  <p>Every career area has a profile. For interests, we use the U.S. Department of Labor’s O*NET interest codes for related jobs: software developers and data scientists are “Investigative and Conventional”, lawyers “Enterprising, Conventional and Investigative”, physiotherapists “Social, Investigative and Realistic”.</p>
  <p>Your answers are compared with each profile and weighted like this:</p>
  <ul class="pl-weights"><li><b>50%</b> Interests</li><li><b>25%</b> Aptitude</li><li><b>15%</b> Personality</li><li><b>10%</b> Values</li></ul>
  <p>Subjects you enjoy add a little. If you are in Class 11 or 12 and a path needs a different stream, it is marked clearly, so you only plan around options open to you.</p></div>
  {mock}</div></section>
<section class="section pl-report"><div class="wrap"><div class="section-head"><h2>What is in your report</h2><p>Ten sections on screen and as a PDF you can download, print and share.</p></div><ol class="pl-rep">{rep}</ol>
  <p class="pl-alt"><a class="btn btn-cyan" href="test.html#demo">See what a report looks like</a></p></div></section>
<section class="section"><div class="wrap pl-split pl-honest"><div><h2>What we leave out, and why</h2>
  <p><b>No fingerprint (DMIT) tests.</b> There is no scientific evidence that fingerprints predict talent or careers.</p>
  <p><b>No “learning styles”.</b> Reviews of the research have found no good evidence that teaching to a visual or auditory “style” helps. We give study tips with strong evidence instead, like testing yourself and spacing out revision.</p>
  <p><b>No personality “types”.</b> We measure traits on a scale, because people are rarely one type or the other.</p></div>
  <div><h2>Its limits, honestly</h2><p>Each section is short, so treat scores as bands, not exact numbers. Aptitudes grow with practice. And for now we compare you with your own profile; comparisons with other students will be added once enough students have taken the test. That is why every report ends with a free session with a counsellor.</p></div></div></section>
<section class="section pl-how"><div class="wrap"><div class="section-head"><h2>How to take it</h2></div>
  <ol class="steps"><li><span class="step-n">1</span><h3>Create your free account</h3><p>Log in with your email. No password needed.</p></li>
  <li><span class="step-n">2</span><h3>Unlock the test</h3><p>Pay ₹{price}, use an access code, or share your invite link: when three friends sign up with it, your test is free.</p></li>
  <li><span class="step-n">3</span><h3>Take it and get your report</h3><p>About 25 minutes. Your report is ready the moment you finish, and saved in your account.</p></li></ol>
  <p class="pl-alt">Just want a quick idea first? Try the <a href="career-check.html">free 4-minute career check</a>.</p></div></section>
{faq_html}
{cta("Ready to find your best-fit career?", "About 25 minutes. Your report is ready the moment you finish.", "Start the test", "test.html")}'''
    service = {"@context": "https://schema.org", "@type": "Service", "@id": "https://myunimentor.in/psychometric-test#service", "name": "MyUniMentor career psychometric test",
               "serviceType": "Career psychometric assessment", "description": "A 25-minute online psychometric test for Class 9–12 students in India: interests (RIASEC), Big Five personality, six timed aptitude sections, situations and work values, matched to 24 career areas with Indian courses and entrance exams.",
               "provider": {"@id": "https://myunimentor.in/#org"}, "areaServed": {"@type": "Country", "name": "India"}, "audience": {"@type": "EducationalAudience", "educationalRole": "student"},
               "url": "https://myunimentor.in/psychometric-test", "offers": {"@type": "Offer", "price": str(price), "priceCurrency": "INR", "url": "https://myunimentor.in/psychometric-test"}}
    page('psychometric-test.html', 'Career Psychometric Test, Class 9–12 | MyUniMentor', f'A 25-minute psychometric test for Class 9–12: interests, aptitude, personality and values, matched to Indian courses and exams. Detailed report for ₹{price}.', 'Resources', body,
         crumbs_schema([("Home", ""), ("Psychometric test", "psychometric-test")]) + faq_schema + '<script type="application/ld+json">' + json.dumps(service, ensure_ascii=False) + '</script>')

def build_404():
    body = f'''<section class="page-hero nf" style="--rays:url(&quot;{rays_svg(19)}&quot;)"><div class="wrap">
  <p class="nf-code">404</p><h1>This page took a wrong turn.</h1>
  <p class="page-sub">Even the best plans need a little guidance. Let's get you back on track.</p>
  <div class="hero-actions"><a href="index.html" class="btn btn-cyan btn-lg">Go to the homepage</a><a href="contact.html" class="btn btn-outline-light btn-lg">Talk to a counsellor</a></div>
</div></section>'''
    page('404.html', 'Page not found | MyUniMentor', 'This page could not be found.', '', body)

EXAMS = D('exams.json')
CITIES = D('cities.json')
TESTIMONIALS = D('testimonials.json')
CHECKED = '21 November 2026'

def build_exam_calendar():
    from datetime import date
    rows = ''
    for i, x in enumerate(sorted(EXAMS, key=lambda x: x['date'])):
        y, m, d_ = map(int, x['date'].split('-'))
        dt = date(y, m, d_)
        rows += (f'<li class="ex {x["status"]}" data-reveal style="--d:{i % 3}" data-date="{x["date"]}" data-streams="{" ".join(x["streams"])}">'
                 f'<div class="ex-date"><span class="ex-m">{dt.strftime("%b")}</span><span class="ex-d">{dt.day}</span><span class="ex-y">{dt.year}</span></div>'
                 f'<div class="ex-body"><div class="ex-top"><h3>{e(x["exam"])}</h3><span class="ex-status">{"Confirmed" if x["status"] == "confirmed" else "Tentative" if x["status"] == "tentative" else "Expected"}</span></div>'
                 f'<p class="ex-for">{e(x["for"])}</p><p class="ex-when"><strong>{e(x["label"])}</strong><span class="ex-count"></span></p>'
                 f'<p class="ex-note">{e(x["note"])}</p><a class="ex-link" href="{x["site"]}" target="_blank" rel="noopener">Official website</a></div></li>')
    faq_html, faq_schema = faq_block([
        ("When is JEE Main 2027?", "JEE Main 2027 Session 1 is scheduled for 20–24 and 28 January 2027. The last date to apply is 22 November 2026 (with late fee until 26 November). Session 2 is scheduled for 2–7 April 2027. Read our <a href=\"jee-main-2027-session-1-guide.html\">JEE Main Session 1 guide</a>."),
        ("When is JEE Advanced 2027?", "JEE Advanced 2027 will be held on 23 May 2027, organised by IIT Delhi. Only the top JEE Main candidates are eligible to appear."),
        ("When is NEET UG 2027?", "NTA has not announced the NEET UG 2027 date yet. NEET is usually held on the first Sunday of May."),
        ("When is CUET UG 2027?", "CUET UG 2027 has not been announced yet. It is expected in May 2027, and registration is usually open in January–February. Read our <a href=\"cuet-guide-class-12.html\">CUET guide</a>."),
        ("When is CLAT 2027?", "CLAT 2027 is on 6 December 2026. Applications closed on 31 October 2026. See our <a href=\"law-after-12th.html\">law after 12th guide</a>."),
        ("When are the design entrance exams (NID DAT, NIFT, UCEED) for 2027?", "NID DAT 2027 Prelims is on 20 December 2026 (last date to apply: 30 November 2026). NIFT 2027 is on 10 January 2027 (tentative; applications extended to 24 November 2026) and UCEED 2027 is on 17 January 2027. See our <a href=\"bdes-after-12th.html\">B.Des guide</a>."),
        ("When is the CHRIST University entrance test for 2027?", "The CHRIST University online entrance test for UG 2027 admissions is on 5 December 2026. The last date to apply for entrance-test programmes is 25 November 2026 (5 pm), and skill assessment and interviews run from 11 to 13 December 2026."),
        ("When is IPMAT 2027?", "IPMAT Indore 2027 is on 24 April 2027. Registration dates are awaited. It is the entrance exam for the five-year integrated management programme at IIM Indore."),
        ("When do the CBSE and CISCE board exams 2027 start?", 'CBSE Class 10 and 12 exams start on 16 February 2027; Class 12 ends on 9 April. ISC (Class 12) runs from 9 February to 8 April 2027, and ICSE (Class 10) from 15 February to 31 March 2027. See the full <a href="cbse-class-12-date-sheet-2027.html">CBSE Class 12</a>, <a href="cbse-class-10-date-sheet-2027.html">CBSE Class 10</a>, <a href="isc-date-sheet-2027.html">ISC</a> and <a href="icse-date-sheet-2027.html">ICSE</a> date sheets.'),
        ("Which entrance exams can Commerce and Humanities students take?", "CUET UG (for central and many other universities), CLAT and AILET (law), IPMAT and JIPMAT (integrated management), and NID DAT, NIFT and UCEED (design) are all open to Commerce and Humanities students. JEE and NEET need Science subjects."),
        ("Can PCB students take JEE, or PCM students take NEET?", "B.Tech admissions through JEE generally need Physics, Chemistry and Maths in Class 12, so PCB students usually focus on NEET, CUET and other exams. NEET needs Biology, so PCM students are not eligible. PCMB students can take both."),
        ("How often is this exam calendar updated?", f"We check every date against the official websites regularly. This calendar was last checked on {CHECKED}. Always confirm on the official website before you apply."),
        ("Which exam should I take?", 'It depends on your stream and the course you want. Book free 1-on-1 counselling and a counsellor will map out your exam plan with you.')], "Exam questions students ask")
    body = page_hero("Entrance exam calendar 2027", f"Key dates for JEE, NEET, CUET, CLAT, NID, NIFT, UCEED and IPMAT, in one place. Last checked on {CHECKED}. Always confirm on the official website before you apply.", "Exam calendar") + f'''
<section class="section">
  <div class="wrap">
    <h2 class="sr-only">All entrance exams by date</h2>
    <div class="cal-tools" data-reveal>
      <div class="filters" role="group" aria-label="Filter exams by stream"><button class="fbtn" aria-pressed="true" data-stream="all">All exams</button><button class="fbtn" aria-pressed="false" data-stream="pcm">PCM</button><button class="fbtn" aria-pressed="false" data-stream="pcb">PCB</button><button class="fbtn" aria-pressed="false" data-stream="com">Commerce</button><button class="fbtn" aria-pressed="false" data-stream="hum">Humanities</button></div>
      <p class="legend"><span class="dotc confirmed"></span>Date announced <span class="dotc expected"></span>Expected, not announced yet</p>
    </div>
    <p class="cal-count" aria-live="polite"></p>
    <ol class="cal">{rows}</ol>
    <p class="tc">Dates are compiled from official announcements and may change. MyUniMentor is not responsible for changes made by the conducting bodies.</p>
  </div>
</section>
<section class="section"><div class="wrap"><div class="section-head row-head" data-reveal><div><h2>Board exam date sheets 2027</h2><p>Every subject, date and timing, copied from the official CBSE and CISCE date sheets.</p></div><a class="btn btn-outline" href="class-12-board-exams-2027.html">Boards, results and rechecks</a></div>
  <ul class="posts" data-hs="m">{''.join(post_card(POST_BY[s_], i) for i, s_ in enumerate(['cbse-class-12-date-sheet-2027', 'isc-date-sheet-2027', 'cbse-class-10-date-sheet-2027', 'icse-date-sheet-2027']))}</ul></div></section>
<section class="section tint"><div class="wrap"><div class="section-head row-head" data-reveal><div><h2>Guides for these exams</h2><p>Step-by-step guides to the entrance exams on this calendar.</p></div><a class="btn btn-outline" href="blog.html">All guides</a></div>
  <ul class="posts" data-hs="m">{''.join(post_card(x, i) for i, x in enumerate([q for q in POSTS if q['tag'] == 'Entrance exams'][::-1][:3]))}</ul></div></section>
{faq_html}
{cta("Not sure which exams you should take?", "A counsellor will build your exam plan with you. 1-on-1 counselling is free for students.")}'''
    page('exam-calendar.html', 'Entrance Exam Calendar 2027 — JEE, NEET, CUET, CLAT Dates | MyUniMentor',
         'JEE Main, JEE Advanced, NEET, CUET, CLAT, NID DAT, NIFT, UCEED and IPMAT 2027 dates in one calendar, plus CBSE, ISC and ICSE board date sheets.', 'Resources', body,
         crumbs_schema([("Home", ""), ("Exam calendar", "exam-calendar")]) + faq_schema)

def build_cities():
    for c in CITIES:
        name = c['city']
        schools = [s for s in SCHOOLS if s['city'] == name]
        if name == 'Rishikesh': unis = [u for u in UNIS if u['city'] == 'Dehradun']; uni_label = 'Partner universities nearby, in Dehradun'
        elif name == 'Saharanpur': unis = [u for u in UNIS if u['city'] in ('Dehradun', 'Roorkee')]; uni_label = 'Partner universities nearby, in Dehradun and Roorkee'
        else: unis = [u for u in UNIS if u['city'] == name]; uni_label = f'Partner universities in {name}'
        active = c['status'] == 'active'
        names = {s['name'] for s in schools}
        city_ph = [k for k, x in PHOTOS.items() if x['school'] in names][:6]
        ph_html = f'<section class="section"><div class="wrap"><div class="section-head" data-reveal><h2>MyUniMentor in {name}</h2><p>From our seminars and the Career Summit at schools in {name}.</p></div>{gallery(city_ph)}</div></section>' if len(city_ph) >= 2 else ''
        sch_html = (f'<section class="section schools-wall"><div class="wrap"><div class="section-head" data-reveal><h2>Our partner schools in {name}</h2></div><ul class="wall">' +
                    ''.join(f'<li data-reveal style="--d:{i % 4}"><a href="network.html#schools">{logo("schools", s, "logo logo-round")}<span><strong>{e(s["name"])}</strong><small>{e(s["board"])}</small></span></a></li>' for i, s in enumerate(schools)) +
                    '</ul></div></section>') if schools else ''
        uni_html = (f'<section class="section tint"><div class="wrap"><div class="section-head" data-reveal><h2>{uni_label}</h2><p>Listed alphabetically. Order does not indicate ranking.</p></div><ul class="org-grid unis-grid">' +
                    ''.join(f'<li class="org-card uni" data-reveal style="--d:{i % 4}">{logo("universities", u, "logo logo-card")}<div class="org-body"><h3>{e(u["name"])}</h3><p class="org-meta">{e(u["city"])}</p></div></li>' for i, u in enumerate(unis)) +
                    '</ul></div></section>') if unis else ''
        offers = (['Free 1-on-1 counselling for students', 'Free career seminars for Class 11–12 in your school', 'The School Career Guidance Summit on your campus', 'Admission guidance for universities across India'] if active else
                  ['Free 1-on-1 counselling for students*, online', 'School seminars and the Career Summit from 2027', 'Schools can register interest now', 'Admission guidance for universities across India'])
        faq = [(f"Is there free career counselling in {name}?", f"Yes. MyUniMentor offers a free first one-on-one counselling session for Class 11–12 students in {name}. Call or WhatsApp +91 74175 57070 to book."),
               (f"Does MyUniMentor work with schools in {name}?", (f"Yes. We work with {len(schools)} partner school{'s' if len(schools) != 1 else ''} in {name}, running free career seminars and the School Career Guidance Summit." if active else f"School programmes in {name} begin in 2027. Schools can register their interest now through our partnership form.")),
               ("Who is the free session for?", "Students currently in Class 11 or Class 12, along with their parents or guardians.")]
        faq_html, faq_schema = faq_block(faq, f"Career counselling in {name}: questions")
        svc = {"@context": "https://schema.org", "@type": "Service", "serviceType": "Career counselling and admissions guidance", "provider": {"@type": "EducationalOrganization", "name": "MyUniMentor", "url": "https://myunimentor.in/"},
               "areaServed": {"@type": "City", "name": name, "containedInPlace": {"@type": "State", "name": c['state']}}, "url": f"https://myunimentor.in/career-counselling-{c['slug']}"}
        ticks = ''.join(f'<li>{o}</li>' for o in offers)
        badge = '' if active else '<p class="pill pill-sun"><span class="dot"></span>School programmes planned for 2027</p>'
        body = page_hero(f"Career counselling in {name}", f"{c['intro']}", f"{name}", badge) + f'''
<section class="section"><div class="wrap split-grid">
  <div data-reveal><h2>What we offer in {name}</h2><p class="lead">{c['local']}</p></div>
  <ul class="ticks big" data-reveal style="--d:1">{ticks}</ul>
</div></section>
{sch_html}
{ph_html}
{uni_html}
{footprint_section() if active else ''}
<section class="section" id="enquire"><div class="wrap contact-grid">
  <div data-reveal><h2>Book a session in {name}</h2><p class="muted">Tell us a little about yourself and our team will call you back.</p>
  <ul class="contact-list"><li><span>Call or WhatsApp</span><a href="tel:+917417557070">+91 74175 57070</a></li><li><span>Email</span><a href="mailto:info@myunimentor.in">info@myunimentor.in</a></li></ul></div>
  {form_card()}
</div></section>
{faq_html}
{cta(f"Plan your next step from {name}", "1-on-1 counselling is free for students.")}'''
        page(f"career-counselling-{c['slug']}.html", f"Career Counselling in {name} — Free 1-on-1 for Class 11–12 | MyUniMentor",
             f"Free career counselling for Class 11–12 students in {name}, {c['state']}. Choose the right stream, course and university with MyUniMentor." + (f" Partner schools: {', '.join(s['name'] for s in schools)}." if schools else ''),
             '', body, crumbs_schema([("Home", ""), (f"Career counselling in {name}", f"career-counselling-{c['slug']}")]) + faq_schema + f'<script type="application/ld+json">{json.dumps(svc)}</script>')

def tc(i, t):
    ph = (f'<figure class="t-photo"><img src="assets/img/testimonials/{t["photo"]}" alt="{e(t["name"])}" width="{t.get("pw", 520)}" height="{t.get("ph", 650)}"{' loading="lazy"' if i > 1 else ' fetchpriority="high"' if i == 0 else ''}></figure>'
          if t.get('photo') else f'<span class="t-init" aria-hidden="true">{e(initials(t["name"]))}</span>')
    return (f'<li class="tcard{" has-photo" if t.get("photo") else ""}"{" data-reveal" if i > 1 else ""} style="--d:{i % 2}">{ph}<div class="t-body">'
            f'<blockquote>“{e(t["quote"])}”</blockquote><div class="t-who"><strong>{e(t["name"])}</strong>'
            f'<small>{e(t.get("role", ""))}</small>{"<small class=" + chr(34) + "t-org" + chr(34) + ">" + e(t["org"]) + "</small>" if t.get("org") else ""}</div></div></li>')

def build_testimonials():
    if TESTIMONIALS:
        cards = ''.join(tc(i, t) for i, t in enumerate(TESTIMONIALS))
        content = f'<ul class="tgrid" data-hs="m">{cards}</ul>'
    else:
        content = '''<div class="t-empty" data-reveal>
      <div class="t-quote-mark" aria-hidden="true">“</div>
      <h2>Stories from our students, parents and schools are on their way.</h2>
      <p>We only publish words from real people who have worked with us, with their permission. If MyUniMentor has helped you, we'd love to hear from you.</p>
    </div>'''
    body = page_hero("What people say", "Students, parents and school leaders on working with MyUniMentor.", "Testimonials") + f'''
<section class="section"><div class="wrap">{content}</div></section>
<section class="section lor-band">
  <div class="wrap lor-grid">
    <div class="lor-stack real" data-reveal><span class="paper p1" aria-hidden="true"></span><span class="paper p2" aria-hidden="true"></span>{lor_card(next(s for s in SCHOOLS if s.get('lor')), True)}</div>
    <div data-reveal style="--d:1"><h2>Letters from our schools</h2>{lor_quote(next(s for s in SCHOOLS if s.get('lor')))}<a href="network.html#lors" class="btn">Read the letters</a></div>
  </div>
</section>
<section class="section" id="share"><div class="wrap contact-grid">
  <div data-reveal><h2>Share your experience</h2><p class="muted">Worked with us as a student, parent or school? Tell us how it went. We'll ask before publishing anything.</p></div>
  <form class="form-card lead-form" data-form="testimonial" data-reveal>
    <div class="row"><div class="field"><label for="t-name">Your name</label><input id="t-name" name="name" required autocomplete="name"></div>
    <div class="field"><label for="t-role">You are a</label><select id="t-role" name="role" required><option value="">Select</option><option>Student</option><option>Parent</option><option>School principal or teacher</option><option>University representative</option></select></div></div>
    <div class="field"><label for="t-school">School, university or city</label><input id="t-school" name="school" required></div>
    <div class="field"><label for="t-msg">Your experience</label><textarea id="t-msg" name="message" rows="5" required></textarea></div>
    <label class="consent"><input type="checkbox" name="consent" required><span>I agree that MyUniMentor may publish my words and name on its website.</span></label>
    <button class="btn btn-full btn-lg" type="submit">Send my story</button>
    <p class="form-status" role="status" aria-live="polite"></p>
  </form>
</div></section>'''
    page('testimonials.html', 'Testimonials — Students, Parents and Schools on MyUniMentor', 'What students, parents and school leaders say about MyUniMentor\'s career counselling, school seminars and the School Career Guidance Summit.', 'Our network', body,
         crumbs_schema([("Home", ""), ("Testimonials", "testimonials")]))

def build_guide_page():
    body = page_hero("The Class 12 Decision Guide", "A free, practical guide to choosing your stream, course, entrance exams and university — written by MyUniMentor's counsellors for Class 11–12 students and parents.", "Free guide") + f'''
<section class="section"><div class="wrap guide-grid">
  <div class="guide-cover" data-reveal aria-hidden="true" style="--rays:url(&quot;{rays_svg(15)}&quot;)">
    <div class="gc-book"><img src="assets/img/logo-horizontal-light.webp" alt=""><p class="gc-k">Free guide</p><p class="gc-t">The Class 12 Decision Guide</p><p class="gc-s">Stream · Course · Exams · University</p><span class="gc-rays"></span></div>
  </div>
  <div data-reveal style="--d:1">
    <h2>What's inside</h2>
    <ul class="ticks big"><li>Know yourself: a short worksheet on interests and strengths</li><li>Streams to courses: what each stream can lead to</li><li>The entrance exam map: which exam opens which door</li><li>How to shortlist a university: a 10-point checklist</li><li>12 questions to ask a university before you apply</li><li>A month-by-month plan for your Class 12 year</li></ul>
    <form class="form-card lead-form guide-form" data-form="guide">
      <h3>Get the guide free</h3>
      <div class="row"><div class="field"><label for="g-name">Name</label><input id="g-name" name="name" required autocomplete="name"></div>
      <div class="field"><label for="g-phone">Phone (WhatsApp)</label><input id="g-phone" name="phone" type="tel" required autocomplete="tel"></div></div>
      <div class="field"><label for="g-class">Class</label><select id="g-class" name="class" required><option value="">Select</option><option>Class 10</option><option>Class 11</option><option>Class 12</option><option>Passed Class 12</option><option>Parent</option></select></div>
      <label class="consent"><input type="checkbox" name="consent" required><span>I am a parent or guardian, or a student filling this with my parent's permission. I agree to the <a href="terms.html" target="_blank">Terms</a> and <a href="privacy.html" target="_blank">Privacy policy</a>.</span></label>
      <label class="consent"><input type="checkbox" name="updates"><span>Optional: also send me updates about admissions and MyUniMentor's partner universities.</span></label>
      <button class="btn btn-full btn-lg" type="submit">Get my free guide</button>
      <p class="form-status" role="status" aria-live="polite"></p>
      <a class="btn btn-cyan btn-full btn-lg guide-dl" href="assets/downloads/MyUniMentor-Class-12-Decision-Guide.pdf" download hidden>Download the guide (PDF)</a>
    </form>
  </div>
</div></section>
''' + cta("Want someone to walk you through it?", "Book free 1-on-1 counselling.")
    page('free-guide.html', 'Free Class 12 Decision Guide (PDF) — Stream, Course, Exams, University | MyUniMentor',
         'Download MyUniMentor\'s free Class 12 Decision Guide: choose your stream and course, understand entrance exams, shortlist universities and plan your Class 12 year.', 'Resources', body,
         crumbs_schema([("Home", ""), ("Free guide", "free-guide")]))

# ---------------- UNIVERSITY PAGES (partner universities: highlights + admission enquiry) ----------------
# Facts live in data/unis/<slug>.json, each taken from the university's own website or its NIRF data, with the year.
UNI_PAGES = {}
for _f in sorted(glob.glob(os.path.join(ROOT, 'data/unis/*.json'))):
    _j = json.load(open(_f, encoding='utf-8')); UNI_PAGES[_j['slug']] = _j
WA = '917417557070'
UNI_COURSES = ['B.Tech / B.E.', 'BBA', 'BCA', 'B.Com', 'Law (BA LLB / BBA LLB)', 'B.Des', 'B.Pharm', 'BA / B.Sc', 'MBA', 'Other']

def lakh(n):
    v = n / 100000
    return f"₹{v:.2f}".rstrip('0').rstrip('.') + ' lakh'

def uni_wa(name):
    from urllib.parse import quote
    return f"https://wa.me/{WA}?text=" + quote(f"Hi MyUniMentor, I want to enquire about admission to {name} for the course: ")

def uni_form(u, d):
    opts = ''.join(f'<option>{e(c)}</option>' for c in UNI_COURSES)
    return f'''<form class="lead-form uni-form" data-form="counselling" data-msg="Thanks, your admission enquiry for {e(u['name'])} has been received. Our team will call you back." aria-label="Enquire for admission to {e(u['name'])}">
  <input type="hidden" name="university" value="{e(u['name'])}"><input type="hidden" name="interest" value="Admission enquiry: {e(u['name'])}">
  <div class="field"><label for="u-name">Student's name</label><input id="u-name" name="name" required autocomplete="name"></div>
  <div class="field"><label for="u-phone">Phone (WhatsApp)</label><input id="u-phone" name="phone" type="tel" inputmode="tel" pattern="[0-9+ ]{{10,14}}" required autocomplete="tel"></div>
  <div class="row">
    <div class="field"><label for="u-class">Class</label><select id="u-class" name="class" required><option value="">Select</option><option>Class 11</option><option>Class 12</option><option>Class 12 passed</option><option>Graduate</option></select></div>
    <div class="field"><label for="u-course">Course</label><select id="u-course" name="course" required><option value="">Select</option>{opts}</select></div>
  </div>
  <label class="consent"><input type="checkbox" name="consent" required><span>I agree to be contacted by MyUniMentor about this enquiry.</span></label>
  <button class="btn btn-full btn-lg" type="submit">Enquire for admission</button>
  <p class="form-status" role="status" aria-live="polite"></p>
</form>'''

def build_unis():
    by_name = {slug(x['name']): x for x in UNIS}
    for s_, d in UNI_PAGES.items():
        u = by_name[s_]; name = u['name']; short = d.get('short') or u.get('short') or name
        city = place(u['city']); b = d['basics']; nirf = d.get('nirf') or {}; naac = d.get('naac')
        ranks = nirf.get('ranks', [])
        rank_txt = ', '.join(f"{r} in {c}" for c, r in ranks)
        if nirf.get('band'): rank_txt = (rank_txt + '; ' if rank_txt else '') + f"{nirf['band'][1]} band in {nirf['band'][0]}"
        naac_txt = (f"Grade {naac['grade']}" + (f" ({naac['score']})" if naac.get('score') else '') + (f", awarded {naac['year']}" if naac.get('year') else '')) if naac else None
        top = [('Founded', b['founded'].split(' (')[0])] + ([('NAAC', naac['grade'])] if naac else []) \
            + ([(f"NIRF {nirf['year']}", f"#{ranks[0][1]} {ranks[0][0]}")] if ranks else []) \
            + [('Campuses', u['campuses'].replace(', Uttarakhand', '')) if u.get('campuses') else ('Campus', u['city'])]
        for extra in [('Type', 'Deemed university' if 'Deemed' in b['type'] else 'Private university'), ('UGC', 'Recognised')]:
            if len(top) < 4: top.insert(-1, extra)
        facts = ''.join(f'<div><dt>{k}</dt><dd>{e(str(v))}</dd></div>' for k, v in top)
        glance = [('Type', b['type']), ('Recognition', b['ugc'])] + ([('NAAC accreditation', naac_txt)] if naac_txt else []) \
            + ([(f"NIRF {nirf['year']} rank", rank_txt)] if rank_txt else []) + [('Campus', b['campus']), ('Also', b['other']),
            ('Official website', f'<a href="{d["official"]}" target="_blank" rel="noopener">{e(d["official"].split("//")[1])}</a>')]
        glance_html = '<div class="table-wrap"><table class="kv"><tbody>' + ''.join(f'<tr><th scope="row">{k}</th><td>{v if k == "Official website" else e(v)}</td></tr>' for k, v in glance) + '</tbody></table></div>'
        pl = d.get('placements')
        if pl:
            rows = ''.join(f'<tr><td>{e(r[0])}</td><td>{r[1]:,}</td><td>{r[2]:,}</td><td><strong>{lakh(r[3])}</strong></td></tr>' for r in pl['rows'])
            place_html = (f'<p>These are the figures {e(name)} itself reported to the Government of India for the NIRF rankings, for students who graduated in {pl["batch"]}. '
                          f'The median is the middle salary: half of the placed students earned more than this and half earned less.</p>'
                          f'<div class="table-wrap"><table><thead><tr><th>Programme level</th><th>Graduated</th><th>Placed</th><th>Median salary per year</th></tr></thead><tbody>{rows}</tbody></table></div>'
                          f'<p class="src">Source: <a href="{pl["url"]}" target="_blank" rel="noopener">{e(pl["source"])}</a>, graduating batch {pl["batch"]}.</p>')
            med = pl['rows'][0]
        else:
            place_html = (f'<p>Ask {e(name)} for placement figures for your course: how many students were placed, the median salary and the year. '
                          f'Treat a single highest package as a headline, not a typical result. We can help you ask the right questions.</p>')
            med = None
        adm_rows = ''.join(f'<tr><td><strong>{e(p_)}</strong></td><td>{e(el)}</td><td>{e(r)}</td></tr>' for p_, el, r in d['admission'])
        adm_html = (f'<div class="table-wrap"><table><thead><tr><th>Programme</th><th>Eligibility</th><th>How you get in</th></tr></thead><tbody>{adm_rows}</tbody></table></div>'
                    f'<p class="src">Source: <a href="{d["admission_src"]}" target="_blank" rel="noopener">{e(short)} admissions</a>. Cut-offs and dates for 2027 can change; check them before you apply.</p>')
        def sec(key, label):
            x = d.get(key)
            if not x: return ''
            yr = f' ({e(x["year"])})' if x.get('year') and key != 'scholarships' else ''
            return f'<p>{e(x["text"])}</p><p class="src">Source: <a href="{x["url"]}" target="_blank" rel="noopener">{e(short)} {label}</a>{yr}.</p>'
        checked = nice_date(d['checked'])
        wa = uni_wa(name)
        others = [x for x in UNIS if slug(x['name']) in UNI_PAGES and slug(x['name']) != s_]
        others.sort(key=lambda x: (x['region'] != u['region'], x['name']))
        other_links = ''.join(f'<li><a href="{slug(x["name"])}.html">{e(x["name"])}</a></li>' for x in others[:5])
        faqs = [(f"How do I get admission to {name} in 2027?", f"{e(d['admission'][0][0])}: {e(d['admission'][0][2])}. Eligibility: {e(d['admission'][0][1])}. MyUniMentor gives free admission guidance: <a href=\"#enquire\">send an enquiry</a> or WhatsApp +91 74175 57070.")]
        if ranks: faqs.append((f"What is the NIRF ranking of {name}?", f"In NIRF {nirf['year']}, published by the Ministry of Education, {e(name)} was ranked {e(rank_txt)}."))
        if naac: faqs.append((f"Is {name} NAAC accredited?", f"Yes. {e(name)} is accredited by NAAC with {e(naac_txt)}."))
        if med: faqs.append((f"What is the average package at {name}?", f"Universities report the median salary to NIRF. For the {pl['batch']} batch, {e(name)} reported a median of {lakh(med[3])} a year for {e(med[0].split(' (')[0])} graduates; {med[2]:,} of {med[1]:,} graduates were placed."))
        if d.get('fees'): faqs.append((f"What are the fees at {name}?", e(d['fees']['text'])))
        if d.get('scholarships'): faqs.append((f"What scholarships does {name} offer?", e(d['scholarships']['text'])))
        if d.get('hostel'): faqs.append((f"Does {name} have hostels?", e(d['hostel']['text'])))
        faqs.append((f"Is MyUniMentor's admission help for {name} free?", f"Yes. {e(name)} is a MyUniMentor partner university, and our admission guidance is free for students: choosing the right course, checking eligibility and scholarships, and applying."))
        faq_html, faq_schema = faq_block(faqs, f"{short}: common questions")
        hero_extra = (f'<div class="uni-hero">{logo("universities", u, "logo logo-tile uni-logo")}<p class="uni-badge">MyUniMentor partner university · Free admission guidance</p></div>'
                      f'<dl class="course-facts">{facts}</dl>'
                      f'<div class="hero-actions uni-actions"><a href="#enquire" class="btn btn-cyan btn-lg">Enquire for admission</a><a href="{wa}" class="btn btn-outline-light btn-lg" target="_blank" rel="noopener">WhatsApp us</a></div>')
        body = page_hero(name if u.get('campuses') else f"{name}, {u['city']}", f"Admission 2027, courses, fees, placements and scholarships, from {e(short)}'s own website and NIRF data. Checked {checked}.", "Universities", hero_extra).replace(
            '<a href="index.html">Home</a><span aria-hidden="true">/</span><span>Universities</span>', '<a href="index.html">Home</a><span aria-hidden="true">/</span><a href="network.html#universities">Partner universities</a><span aria-hidden="true">/</span><span>' + e(short) + '</span>') + f'''
<section class="section article-section"><div class="wrap art-grid">
  <article class="article">
    <h2>{e(short)} at a glance</h2>{glance_html}
    <h2>Placements at {e(short)}</h2>{place_html}
    <h2>Courses and admission 2027</h2>{adm_html}
    <h2>Fees</h2>{sec('fees', 'fee details')}
    <h2>Scholarships</h2>{sec('scholarships', 'scholarships')}
    <h2>Hostels</h2>{sec('hostel', 'hostel details')}
    <div class="callout"><strong>How MyUniMentor helps</strong><p>{e(name)} is a MyUniMentor partner university. Our admission guidance is free: we help you pick the right course, check your eligibility and scholarship, compare it with other options, and apply. <a href="#enquire">Send an enquiry</a> or <a href="{wa}" target="_blank" rel="noopener">WhatsApp us</a>.</p></div>
    <p class="src">Every figure on this page comes from {e(short)}'s official website or the data it submitted to NIRF (Ministry of Education), checked on {checked}. Fees and rules change each year, so confirm them with the university before paying.</p>
  </article>
  <aside class="art-aside">
    <div class="aside-card uni-enquire" id="enquire"><strong>Enquire for admission</strong><p>Free admission guidance for {e(short)} from MyUniMentor.</p>{uni_form(u, d)}
      <a class="btn btn-wa btn-full" href="{wa}" target="_blank" rel="noopener">WhatsApp: enquire about {e(short)}</a></div>
    <div class="aside-card"><strong>Entrance exam dates 2027</strong><p>JEE, NEET, CUET, CLAT and more, in one calendar.</p><a class="btn btn-outline btn-full" href="exam-calendar.html">See the exam calendar</a></div>
    <div class="aside-card"><strong>Other partner universities</strong><ul class="aside-links">{other_links}<li><a href="network.html#universities">All {len(UNIS)} partner universities</a></li></ul></div>
  </aside>
</div></section>
{faq_html}
{cta(f"Want to study at {e(short)}?", "Talk to a MyUniMentor counsellor about courses, eligibility and scholarships. Admission guidance is free for students.", "Enquire for admission", "#enquire")}'''
        body = label_tables(body)
        uni_ld = {"@context": "https://schema.org", "@type": "CollegeOrUniversity", "@id": f"https://myunimentor.in/{s_}#university", "name": name,
                  "alternateName": [short] if short != name else [], "url": d['official'], "sameAs": [d['official']],
                  "logo": f"https://myunimentor.in/assets/logos/universities/{s_}.webp",
                  "address": {"@type": "PostalAddress", "addressLocality": u['city'], "addressRegion": STATE.get(u['city'], u['region']), "addressCountry": "IN"},
                  "foundingDate": re.match(r'\d{4}', b['founded']).group(0)}
        page_ld = {"@context": "https://schema.org", "@type": "WebPage", "@id": f"https://myunimentor.in/{s_}", "name": d['title'].replace(' | MyUniMentor', ''), "description": d['desc'],
                   "about": {"@id": f"https://myunimentor.in/{s_}#university"}, "publisher": {"@id": "https://myunimentor.in/#org"}, "dateModified": d['checked'], "inLanguage": "en-IN"}
        page(f"{s_}.html", d['title'], d['desc'], 'Our network', body,
             crumbs_schema([("Home", ""), ("Partner universities", "network"), (short, s_)]) + faq_schema
             + f'<script type="application/ld+json">{json.dumps(uni_ld, ensure_ascii=False)}</script><script type="application/ld+json">{json.dumps(page_ld, ensure_ascii=False)}</script>')

if __name__ == '__main__':
    build_home(); build_network(); build_unis(); build_about(); build_services(); build_summit(); build_contact(); build_blog(); build_courses(); build_profile(); (build_privacy(), build_terms()) if SHOW_LEGAL else None; (build_career_check() if SHOW_CAREER_CHECK else None); build_404(); build_account(); build_admin(); build_test(); build_psy_landing(); build_exam_calendar(); build_cities(); build_testimonials(); (build_guide_page() if SHOW_GUIDE else None); build_seo_files(); build_llms_full()
    print('built', len(UNIS), 'universities,', len(SCHOOLS), 'schools')
