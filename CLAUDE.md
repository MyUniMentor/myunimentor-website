# MyUniMentor website — notes for automated updates

Static site for myunimentor.in, served by GitHub Pages from the `main` branch (custom domain in `CNAME` — never delete it).
All HTML pages are generated. Never hand-edit `*.html`; edit the sources and rebuild.

## Build
```
pip install --break-system-packages rcssmin rjsmin pillow fonttools brotli
python3 build.py          # must end with "built 29 universities, 12 schools" (numbers may grow)
```
`CLEAN_URLS` defaults to 1 (links like `/about`). Leave it that way for anything pushed to GitHub.

Share images: `tools/og.py` makes a 1200×630 image per page in `assets/og/` (cached in `data/og.json`; it only redraws when a title changes). Commit both. CSS rules that only style `/account`, `/admin` and `/test` (`.acct`, `.adm`, `.psy`) are split into `assets/css/app.min.css` at build time and loaded only on those pages.

## Where content lives
- `data/exams.json` — exam calendar. Fields: exam, for, date (YYYY-MM-DD), label (as shown), status (`confirmed` | `tentative` | `expected`), streams, note, site (official URL).
  Also keep these fields when editing: `id` (stable slug without the year, never change it), `auto` (streams that get this exam by default), and optional `deadline` (YYYY-MM-DD) + `deadline_label` for the registration deadline. Give new exams an `id` and `auto` too.
- `build.py` → `CHECKED = '...'` — the "last checked" date shown on the exam calendar. Update it every time you check.
- `content_blog.py` → `POSTS` — blog articles (slug, tag, title ≤60 chars, h1, desc ≤160 chars, read, lede, body HTML, faq, related, and `date` = the day you publish it, YYYY-MM-DD). `data/lastmod.json` is updated by the build: commit it, never edit it. New posts get added to the sitemap and llms files automatically.
- `content_courses.py`, `data/*.json` — courses, schools, universities, testimonials, photos.
- Emails to account holders: `tools/notify.py` run by `.github/workflows/notify.yml`. A push that changes `data/exams.json` emails everyone following that exam (keep `id`s stable, keep `deadline` + `deadline_label` accurate: reminders go 3 days and 1 day before the deadline, and an all-the-best email goes the evening before an exam with an exact date). A new post in `content_blog.py` becomes a draft announcement that Om approves in `/admin`. Never send emails yourself and never edit the workflow's secrets.

## House rules (do not break)
- Every change must be SEO and AI-search friendly (titles, descriptions, structured data, llms files) and must never slow the site down or break a page. Load extra scripts only when needed (see how `tour.min.js` loads after the page), and keep Lighthouse at its current scores.
- English only, plain and specific. Facts only from official or primary sources checked in the same run. No fees, salary figures or rankings unless taken from an official source and dated.
- Never mention "up to 15 universities", "North India", "2026–27", or "T&C apply". Expansion plans are always "we plan to…".
- Never show or link the hidden pages: Class 12 guide, privacy, terms (`SHOW_GUIDE` and `SHOW_LEGAL` in build.py stay False). Student and parent accounts are live (`SHOW_ACCOUNTS`): "Log in" in the header, `/account` (noindex, never in the sitemap or llms files), code in `assets/js/account.js`. The career check is live (`SHOW_CAREER_CHECK = True`); its questions and course facts live in `assets/js/check.js` — no fees, salaries or rankings there either.
- Psychometric test (`SHOW_PSY`): public landing page `/psychometric-test` (indexed) and the test itself at `/test` (noindex, never in the sitemap or llms files). Code in `assets/js/psy.js`; its career areas (courses, exams, lengths) are injected at build time from the `CL` block in `assets/js/check.js`, so edit course facts there only. Interest profiles of each area come from O*NET OnLine interest codes (keep the CC BY 4.0 attribution in the report); personality items are IPIP (public domain). Price is `PSY['price']` in build.py and `TEST_PRICE` in the accounts Apps Script: keep them equal. `PSY['payLive']` stays False until Razorpay keys are in the Apps Script and Om confirms. Unlocks are written only by the Apps Script (payment, 3 invites, code) or by staff in `/admin`. Previews: `/test#demo` (report), `#demo-test` (take the test, nothing saved), `#demo-unlock`.
- Career check results save to the student's account (`users.check`, including the answers as `a`); the dashboard reopens them via `/career-check#r=…`.
- Never invent testimonials, LORs, numbers, partners or quotes. Never credit Om Garg as author of anything except articles on this site.
- Keep internal links pointing to existing pages; prefer linking new articles to the exam calendar, course guides and /contact.

## After changes
1. `python3 build.py` and confirm no errors.
2. Check every `href="/..."` in the HTML resolves to a page or file.
3. Commit with a short message and push to `main`.
