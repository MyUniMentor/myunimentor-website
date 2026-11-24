"""Board exam date sheet pages (2027). Data: data_boards.py (from the official PDFs). Added to POSTS in content_blog.py."""
import datetime, html
import data_boards as D

CBSE_CIRC = 'https://www.cbse.gov.in/cbsenew/examination_Circular.html'
CISCE_PAGE = 'https://cisce.org/regulations-and-syllabuses-isc/'
CISCE_ICSE = 'https://cisce.org/'
e = lambda s: html.escape(s, quote=True)
day = lambda d: datetime.date.fromisoformat(d)
nice = lambda d: day(d).strftime('%-d %B %Y')
short = lambda d: day(d).strftime('%a, %-d %b')
ext = lambda url, text: f'<a href="{url}" target="_blank" rel="noopener">{text}</a>'

def clock(t):
    """'10:30 am' -> (10, 30) in IST."""
    hm, ap = t.split(' '); h, m = map(int, hm.split(':'))
    return (h % 12 + (12 if ap == 'pm' else 0), m)

def pick(date, start, end, title):
    """Checkbox the calendar tool reads: start/end as IST wall-clock times."""
    return f'<input type="checkbox" class="ds-pick" aria-label="Add {e(title)} to my calendar" data-d="{date}" data-s="{start[0]:02d}{start[1]:02d}" data-e="{end[0]:02d}{end[1]:02d}" data-t="{e(title)}">'

def cbse_span(timing):
    a, b = timing.replace('–', '-').split('-')
    s = clock(a.strip()); eh, em = map(int, b.strip().split(' ')[0].split(':'))
    return s, ((eh % 12) + 12 if 'pm' in b and eh != 12 else eh, em)

def cbse_full(rows, board):
    out = []
    for d_, timing, subs in rows:
        s, en = cbse_span(timing)
        for code, name in subs:
            out.append(f'<tr><td>{pick(d_, s, en, f"{board} {name} ({code})")}</td><td><time datetime="{d_}">{short(d_)}</time></td><td>{e(name)}</td><td>{code}</td><td>{timing}</td></tr>')
    return ('<div class="table-wrap ds-table"><table><thead><tr><th><span class="sr-only">Add</span></th><th>Date</th><th>Subject</th><th>Code</th><th>Time (IST)</th></tr></thead><tbody>'
            + ''.join(out) + '</tbody></table></div>')

def find(rows, code):
    for d_, timing, subs in rows:
        for c, n in subs:
            if c == code: return d_, timing, n
    raise KeyError(code)

def glance(rows, codes):
    out = []
    for code in codes:
        d_, timing, n = find(rows, code)
        out.append((d_, f'<tr><td><time datetime="{d_}"><strong>{short(d_)}</strong></time></td><td>{e(n)} ({code})</td><td>{timing}</td></tr>'))
    out.sort()
    return ('<div class="table-wrap"><table><thead><tr><th>Date</th><th>Subject (code)</th><th>Time (IST)</th></tr></thead><tbody>'
            + ''.join(r for _, r in out) + '</tbody></table></div>')

def streams(rows, plans):
    blocks = []
    for name, codes in plans:
        items = sorted((find(rows, c)[0], find(rows, c)[2]) for c in codes)
        li, prev = [], None
        for d_, n in items:
            gap = '' if prev is None else f' <span class="ds-gap">{(day(d_) - day(prev)).days} days after the previous paper</span>'
            li.append(f'<li><time datetime="{d_}"><strong>{short(d_)}</strong></time> {e(n)}{gap}</li>'); prev = d_
        blocks.append(f'<div class="ds-stream"><h3>{name}</h3><ol>{"".join(li)}</ol></div>')
    return '<div class="ds-streams">' + ''.join(blocks) + '</div>'

TOOL = '''<div class="ds-tool" hidden><p><strong>Make your own exam calendar.</strong> Tick your subjects in the table below, then add them to your phone or laptop calendar, with a 7 pm reminder the evening before each paper.</p>
<div class="ds-tool-row"><button type="button" class="btn btn-cyan btn-small ds-ics" disabled>Tick your subjects first</button><span class="ds-note">Works with Google Calendar, Apple Calendar and Outlook.</span></div></div>
<script src="assets/js/ds.min.js?v={VER}" defer></script>'''

def isc_full(rows, board, hours=None):
    out = []
    for r in rows:
        d_, t, papers = r[0], r[1], r[2]; h = r[3] if len(r) > 3 else 3
        s = clock(t); en = (s[0] + h, s[1])
        for p in papers:
            out.append(f'<tr><td>{pick(d_, s, en, f"{board} {p}")}</td><td><time datetime="{d_}">{short(d_)}</time></td><td>{e(p)}</td><td>{t}</td><td>{h} hours</td></tr>')
    return ('<div class="table-wrap ds-table"><table><thead><tr><th><span class="sr-only">Add</span></th><th>Date</th><th>Subject / paper</th><th>Starts (IST)</th><th>Duration</th></tr></thead><tbody>'
            + ''.join(out) + '</tbody></table></div>')

def isc_find(rows, word):
    for r in rows:
        for p in r[2]:
            if p.startswith(word): return r[0], r[1], p
    raise KeyError(word)

def isc_glance(rows, words):
    items = sorted(isc_find(rows, w) for w in words)
    return ('<div class="table-wrap"><table><thead><tr><th>Date</th><th>Subject / paper</th><th>Starts (IST)</th></tr></thead><tbody>'
            + ''.join(f'<tr><td><time datetime="{d_}"><strong>{short(d_)}</strong></time></td><td>{e(p)}</td><td>{t}</td></tr>' for d_, t, p in items) + '</tbody></table></div>')

def facts(rows_):
    return '<div class="table-wrap"><table><tbody>' + ''.join(f'<tr><th scope="row">{a}</th><td>{b}</td></tr>' for a, b in rows_) + '</tbody></table></div>'

AFTER = '''<h2>After the boards</h2>
<p>Most entrance exams start soon after the boards. See every date on our <a href="exam-calendar.html">entrance exam calendar</a>, and read <a href="class-12-board-exams-2027.html">what to do when results come out</a>. Not sure which course fits you? Try our <a href="psychometric-test.html">psychometric test</a> or <a href="contact.html">book a free counselling session</a>.</p>'''

# ---------------- CBSE Class 12 ----------------
X12 = D.XII
c12_main = ['042', '043', '041', '241', '044', '301', '302', '055', '054', '030', '028', '027', '029', '037', '039', '083', '065', '048', '074']
c12_body = f'''
<h2>Key facts</h2>
{facts([('First exam', 'Tuesday, 16 February 2027 (Physics)'), ('Last exam', 'Friday, 9 April 2027 (Retail, Web Application)'), ('Start time', 'All papers start at 10:30 am IST'), ('Subjects', '121 subjects in Class 12'), ('Students registered', 'Over 19.8 lakh in Class 12'), ('Date sheet released', '6 November 2026, 101 days before the exams'), ('Official source', ext(CBSE_CIRC, 'cbse.gov.in, Examination circulars') + ': “Date Sheet for Class X and Class XII Board Examinations, 2027”')])}
<p>Every date on this page is taken from CBSE’s official date sheet, dated 6 November 2026. CBSE says it planned the schedule so that no two subjects a student has chosen fall on the same day, and so that the boards finish before the major entrance exams.</p>

<h2>Main subjects at a glance</h2>
{glance(X12, c12_main)}

<h2>Stream-wise schedule and preparation gaps</h2>
<p>How many days you get between papers matters more than the dates themselves. Here are the common subject combinations, with the gap before each paper.</p>
{streams(X12, [('Science (PCM)', ['042', '043', '041', '301']), ('Science (PCB)', ['042', '043', '044', '301']), ('Commerce with Maths', ['055', '301', '030', '054', '041']), ('Humanities', ['029', '037', '301', '030', '028', '027', '039'])])}
<p class="ds-small">Add your own optional subject (for example Physical Education, Computer Science or a language) from the full table below.</p>

<div class="callout"><strong>MyUniMentor tip</strong><p>Use the long gaps for your hardest subjects. In PCM, the 11 days between Physics and Chemistry are your biggest block, and Mathematics comes 4 days after English; in PCB, you get 20 days between English and Biology. Plan backwards from each date, and keep the last two days before every paper for past papers only.</p></div>

<h2>Full CBSE Class 12 date sheet 2027</h2>
{TOOL}
{cbse_full(X12, 'CBSE Class 12')}
<p class="ds-small">Source: CBSE’s “Date Sheet for Class X and Class XII Board Examinations, 2027”, published on {ext(CBSE_CIRC, 'cbse.gov.in')} on 6 November 2026. Dates can change; always check your admit card and CBSE’s website.</p>
{AFTER}
'''

# ---------------- CBSE Class 10 ----------------
X10 = D.X
c10_main = ['041', '241', '086', '184', '101', '165', '417', '402', '122', '002', '085', '087', '018']
c10_body = f'''
<h2>Key facts</h2>
{facts([('First exam', 'Tuesday, 16 February 2027 (Painting)'), ('Main subjects begin', 'Wednesday, 17 February 2027 (Mathematics Standard and Basic)'), ('Last exam', 'Tuesday, 9 March 2027 (languages, NCC, Book Keeping & Accountancy)'), ('Start time', 'All papers start at 10:30 am IST'), ('Subjects', '83 subjects in Class 10'), ('Students registered', 'Over 26.5 lakh in Class 10'), ('Date sheet released', '6 November 2026'), ('Official source', ext(CBSE_CIRC, 'cbse.gov.in, Examination circulars') + ': “Date Sheet for Class X and Class XII Board Examinations, 2027”')])}
<p>Every date on this page is taken from CBSE’s official date sheet for the main board examination, dated 6 November 2026.</p>

<h2>Main subjects at a glance</h2>
{glance(X10, c10_main)}
{streams(X10, [('The five core subjects', ['041', '086', '184', '002', '087'])])}

<div class="callout"><strong>MyUniMentor tip</strong><p>Mathematics comes first, on 17 February, so start full-length practice papers in December. After that, the five core papers are four to five days apart, which is enough for one subject at a time if your first revision is done by early February. Class 10 is also when you choose your stream. Our guide on <a href="stream-after-class-10.html">choosing a stream after Class 10</a> can help.</p></div>

<h2>Full CBSE Class 10 date sheet 2027</h2>
{TOOL}
{cbse_full(X10, 'CBSE Class 10')}
<p class="ds-small">Source: CBSE’s “Date Sheet for Class X and Class XII Board Examinations, 2027”, published on {ext(CBSE_CIRC, 'cbse.gov.in')} on 6 November 2026. Dates can change; always check your admit card and CBSE’s website.</p>
'''

# ---------------- ISC Class 12 ----------------
isc_main = ['English – Paper 1', 'English – Paper 2', 'Economics', 'Chemistry', 'Accountancy', 'Mathematics', 'Physical Education', 'Physics', 'Business Studies', 'Geography', 'Biology', 'Computer Science', 'History', 'Sociology', 'Commerce', 'Psychology', 'Political Science', 'Legal Studies']
isc_body = f'''
<h2>Key facts</h2>
{facts([('First exam', 'Tuesday, 9 February 2027 (Environmental Science, Western Music)'), ('Last exam', 'Thursday, 8 April 2027 (Legal Studies)'), ('Start time', 'Most papers at 2:00 pm; Art papers at 9:00 am'), ('Reporting time', 'Be seated by 1:30 pm for 2:00 pm papers, and by 8:30 am for 9:00 am papers'), ('Reading time', '15 minutes, in addition to the writing time'), ('Duration', '3 hours for every paper'), ('Results', 'April or May 2027, on cisce.org'), ('Timetable issued', '10 November 2026, by CISCE')])}
<p>Every date on this page is taken from CISCE’s official “ISC (Class XII) Year 2027 Examination Timetable and Instructions for Candidates”, available on {ext(CISCE_PAGE, 'cisce.org')}.</p>

<h2>Main subjects at a glance</h2>
{isc_glance(D.ISC, isc_main)}

<div class="callout"><strong>MyUniMentor tip</strong><p>ISC starts a week before CBSE, and most papers are in the afternoon. Write your mock papers at 2 pm, not in the morning, so you are used to the timing. Physics, Biology and Computer Science all fall in March, so finish your first revision of them by the end of February.</p></div>

<h2>Full ISC 2027 timetable</h2>
{TOOL}
{isc_full(D.ISC, 'ISC')}

<h2>What you can and cannot take into the hall</h2>
<ul><li><strong>Allowed:</strong> your CISCE admission card, blue or black pens, pencils, scale, eraser, sharpener, colour pencils, drawing instruments, and a calculator of the type CISCE allows (Casio fx-82 MS or similar, or a basic calculator).</li>
<li><strong>Not allowed:</strong> books or notes, mobile phones, smart watches, earbuds, AI or smart glasses, smart rings, smart or scanner pens, wallets and cash.</li></ul>

<h2>Results, recheck and re-evaluation</h2>
<p>CISCE will declare the ISC 2027 results in April or May 2027 on cisce.org. If you are not satisfied, you can apply online for a <strong>recheck</strong>; the request must reach CISCE within four days of the results. After the recheck results, you can apply for <strong>re-evaluation</strong> within three days, only in the subjects you asked to recheck. Both are paid services. You can also take an <strong>improvement exam</strong> in up to three subjects in the same year.</p>
{AFTER}
'''

# ---------------- ICSE Class 10 ----------------
icse_main = ['English Language', 'Literature in English', 'Mathematics', 'History & Civics', 'Geography', 'Hindi', 'Physics', 'Chemistry', 'Biology', 'Group III Elective, Section A', 'Languages', 'Environmental Science', 'Commercial Studies', 'Economics']
icse_body = f'''
<h2>Key facts</h2>
{facts([('First exam', 'Monday, 15 February 2027 (English Language)'), ('Last exam', 'Wednesday, 31 March 2027 (Economics, French and Sanskrit as Group II electives)'), ('Start time', 'Most papers at 10:15 am; Art papers at 9:00 am'), ('Reporting time', 'Be seated by 9:45 am for 10:15 am papers, and by 8:30 am for 9:00 am papers'), ('Reading time', '15 minutes, in addition to the writing time'), ('Results', 'April or May 2027, on cisce.org'), ('Timetable issued', '10 November 2026, by CISCE')])}
<p>Every date on this page is taken from CISCE’s official “ICSE (Class X) Year 2027 Examination Timetable and Instructions for Candidates”, available on {ext(CISCE_ICSE, 'cisce.org')}.</p>

<h2>Main subjects at a glance</h2>
{isc_glance(D.ICSE, icse_main)}

<div class="callout"><strong>MyUniMentor tip</strong><p>The three Science papers come one after another in March, with three to four days between them. Finish your first full revision of all three by the end of February, and use the gaps for past papers. After the boards, the next big decision is your stream; read our guide on <a href="stream-after-class-10.html">choosing a stream after Class 10</a>.</p></div>

<h2>Full ICSE 2027 timetable</h2>
{TOOL}
{isc_full(D.ICSE, 'ICSE')}

<h2>Results, recheck and re-evaluation</h2>
<p>CISCE will declare the ICSE 2027 results in April or May 2027 on cisce.org. A <strong>recheck</strong> request must reach CISCE within four days of the results, and <strong>re-evaluation</strong> can be requested within three days of the recheck results. You can also take an <strong>improvement exam</strong> in up to three subjects.</p>
'''

def post(slug, title, h1, desc, lede, body, faq, related, read):
    return {"slug": slug, "date": "2026-11-24", "tag": "Board exams", "title": title, "h1": h1, "desc": desc, "read": read, "lede": lede, "body": body, "faq": faq, "related": related}

BOARD_POSTS = [
 post("cbse-class-12-date-sheet-2027", "CBSE Class 12 Date Sheet 2027: All Subjects | MyUniMentor",
      "CBSE Class 12 date sheet 2027: every subject, date and timing",
      "CBSE Class 12 board exams 2027 run from 16 February to 9 April. Subject-wise dates from the official date sheet, stream-wise gaps and a calendar download.",
      "CBSE’s Class 12 board exams 2027 begin on Tuesday, 16 February with Physics and end on 9 April. Below are all 121 subjects with their dates and timings, copied from CBSE’s official date sheet of 6 November 2026, plus the gaps between papers for each stream.",
      c12_body,
      [("When does the CBSE Class 12 exam 2027 start?", "On Tuesday, 16 February 2027, with Physics (042). All papers start at 10:30 am IST."),
       ("When is the CBSE Class 12 Maths exam 2027?", "Mathematics (041) and Applied Mathematics (241) are on Tuesday, 9 March 2027, from 10:30 am to 1:30 pm."),
       ("When are Chemistry and Biology in CBSE Class 12 2027?", "Chemistry (043) is on Saturday, 27 February 2027, and Biology (044) is on Thursday, 25 March 2027."),
       ("When is the English exam for CBSE Class 12 2027?", "English Core (301) and English Elective (001) are on Friday, 5 March 2027."),
       ("When is the last CBSE Class 12 exam in 2027?", "The last papers are Retail (801) and Web Application (803) on Friday, 9 April 2027. Among the main subjects, Legal Studies (074) is on 8 April and Business Studies (054) on 1 April."),
       ("When will CBSE Class 12 results 2027 come out?", "CBSE has not announced the date. For reference, it declared the 2026 Class 12 results on 13 May 2026.")],
      ["class-12-board-exams-2027", "cbse-class-10-date-sheet-2027", "jee-main-2027-session-1-guide"], 6),
 post("cbse-class-10-date-sheet-2027", "CBSE Class 10 Date Sheet 2027: All Subjects | MyUniMentor",
      "CBSE Class 10 date sheet 2027: every subject, date and timing",
      "CBSE Class 10 board exams 2027 run from 16 February to 9 March. Subject-wise dates and timings from the official date sheet, with a calendar download.",
      "CBSE’s Class 10 board exams 2027 begin on 16 February, with Mathematics on 17 February, and end on 9 March. Below are all 83 subjects with their dates and timings, copied from CBSE’s official date sheet of 6 November 2026.",
      c10_body,
      [("When does the CBSE Class 10 exam 2027 start?", "The first paper is Painting (049) on Tuesday, 16 February 2027. The main subjects begin with Mathematics Standard (041) and Basic (241) on Wednesday, 17 February 2027."),
       ("When is the CBSE Class 10 Science exam 2027?", "Science (086) is on Monday, 22 February 2027, from 10:30 am to 1:30 pm."),
       ("When is the CBSE Class 10 Social Science exam 2027?", "Social Science (087) is on Monday, 8 March 2027."),
       ("When is the CBSE Class 10 English exam 2027?", "English Language and Literature (184) and English Communicative (101) are on Friday, 26 February 2027."),
       ("When is the last CBSE Class 10 exam in 2027?", "Tuesday, 9 March 2027, with several languages, NCC and Elements of Book Keeping & Accountancy.")],
      ["cbse-class-12-date-sheet-2027", "stream-after-class-10", "icse-date-sheet-2027"], 5),
 post("isc-date-sheet-2027", "ISC Date Sheet 2027 (Class 12): All Papers | MyUniMentor",
      "ISC Class 12 timetable 2027: every paper, date and timing",
      "ISC Class 12 exams 2027 run from 9 February to 8 April. Every paper's date and time from the official CISCE timetable, reporting times, results and rechecks.",
      "CISCE’s ISC (Class 12) exams 2027 begin on Tuesday, 9 February and end on Thursday, 8 April. Below is every paper with its date and time, from CISCE’s official timetable of 10 November 2026, along with reporting times, what you can take into the hall, and how rechecks work.",
      isc_body,
      [("When does the ISC 2027 exam start?", "On Tuesday, 9 February 2027, with Environmental Science and Western Music Paper 1. Most papers start at 2:00 pm."),
       ("When is the ISC 2027 English exam?", "English Paper 1 (English Language) is on Wednesday, 10 February 2027, and English Paper 2 (Literature in English) on Monday, 15 February 2027."),
       ("When are ISC 2027 Physics, Chemistry and Maths?", "Chemistry Paper 1 is on 24 February, Mathematics on 1 March and Physics Paper 1 on 8 March 2027, all at 2:00 pm."),
       ("What time should I reach for ISC exams?", "You must be seated by 1:30 pm for papers that start at 2:00 pm, and by 8:30 am for Art papers that start at 9:00 am. Reading time is an extra 15 minutes."),
       ("When will ISC 2027 results be declared?", "CISCE says the ISC 2027 results will be declared in April or May 2027 on cisce.org.")],
      ["class-12-board-exams-2027", "icse-date-sheet-2027", "cbse-class-12-date-sheet-2027"], 6),
 post("icse-date-sheet-2027", "ICSE Date Sheet 2027 (Class 10): All Papers | MyUniMentor",
      "ICSE Class 10 timetable 2027: every paper, date and timing",
      "ICSE Class 10 exams 2027 run from 15 February to 31 March. Every paper's date and time from the official CISCE timetable, with reporting times and results.",
      "CISCE’s ICSE (Class 10) exams 2027 begin on Monday, 15 February with English Language and end on Wednesday, 31 March. Below is every paper with its date and time, from CISCE’s official timetable of 10 November 2026.",
      icse_body,
      [("When does the ICSE 2027 exam start?", "On Monday, 15 February 2027, with English Language (English Paper 1) at 10:15 am."),
       ("When is the ICSE 2027 Maths exam?", "Mathematics is on Monday, 22 February 2027, at 10:15 am, for 3 hours."),
       ("When are the ICSE 2027 Science papers?", "Physics is on 8 March, Chemistry on 12 March and Biology on 15 March 2027, each at 10:15 am for 2 hours."),
       ("What time should I reach for ICSE exams?", "You must be seated by 9:45 am for papers that start at 10:15 am, and by 8:30 am for Art papers that start at 9:00 am."),
       ("When will ICSE 2027 results be declared?", "CISCE says the ICSE 2027 results will be declared in April or May 2027 on cisce.org.")],
      ["cbse-class-10-date-sheet-2027", "stream-after-class-10", "isc-date-sheet-2027"], 5),
]
