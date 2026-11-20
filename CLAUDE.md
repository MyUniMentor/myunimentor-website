# MyUniMentor website — notes for automated updates

Static site for myunimentor.in, served by GitHub Pages from the `main` branch (custom domain in `CNAME` — never delete it).
All HTML pages are generated. Never hand-edit `*.html`; edit the sources and rebuild.

## Build
```
pip install --break-system-packages rcssmin rjsmin pillow
python3 build.py          # must end with "built 29 universities, 12 schools" (numbers may grow)
```
`CLEAN_URLS` defaults to 1 (links like `/about`). Leave it that way for anything pushed to GitHub.

## Where content lives
- `data/exams.json` — exam calendar. Fields: exam, for, date (YYYY-MM-DD), label (as shown), status (`confirmed` | `tentative` | `expected`), streams, note, site (official URL).
- `build.py` → `CHECKED = '...'` — the "last checked" date shown on the exam calendar. Update it every time you check.
- `content_blog.py` → `POSTS` — blog articles (slug, tag, title ≤60 chars, h1, desc ≤160 chars, read, lede, body HTML, faq, related). New posts get added to the sitemap and llms files automatically.
- `content_courses.py`, `data/*.json` — courses, schools, universities, testimonials, photos.

## House rules (do not break)
- English only, plain and specific. Facts only from official or primary sources checked in the same run. No fees, salary figures or rankings unless taken from an official source and dated.
- Never mention "up to 15 universities", "North India", "2026–27", or "T&C apply". Expansion plans are always "we plan to…".
- Never show or link the hidden pages: career check, Class 12 guide, privacy, terms (switches `SHOW_*` in build.py stay False).
- Never invent testimonials, LORs, numbers, partners or quotes. Never credit Om Garg as author of anything except articles on this site.
- Keep internal links pointing to existing pages; prefer linking new articles to the exam calendar, course guides and /contact.

## After changes
1. `python3 build.py` and confirm no errors.
2. Check every `href="/..."` in the HTML resolves to a page or file.
3. Commit with a short message and push to `main`.
