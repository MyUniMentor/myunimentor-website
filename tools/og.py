"""Share images (1200x630) for each page: title on the brand background. Called by build.py.
Needs Pillow + fonttools + brotli (to read the site's woff2 fonts). If they are missing, pages keep the default image."""
import os, hashlib, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'data', 'og.json')
_fonts = {}

def font(name, size):
    path = f'/tmp/mum-fonts/{name}.ttf'
    if not os.path.exists(path):
        from fontTools.ttLib import TTFont
        os.makedirs('/tmp/mum-fonts', exist_ok=True)
        t = TTFont(os.path.join(ROOT, 'assets/fonts', name + '.woff2')); t.flavor = None; t.save(path)
    k = (name, size)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]

def wrap(d, text, f, width):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= width: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def background():
    W, H = 1200, 630
    im = Image.new('RGB', (W, H), '#0B1C33'); px = ImageDraw.Draw(im)
    for y in range(H): px.line([(0, y), (W, y)], fill=(11, 28 + y * 10 // H, 51 + y * 14 // H))
    glow = Image.new('L', (W, H), 0); ImageDraw.Draw(glow).ellipse((760, 330, 1420, 900), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    im = Image.composite(Image.new('RGB', (W, H), '#11BDDE'), im, glow.point(lambda v: v * 6 // 10))
    d = ImageDraw.Draw(im)
    for x in range(40, W, 34):
        for y in range(40, H, 34): d.point((x, y), fill=(40, 70, 100))
    logo = Image.open(os.path.join(ROOT, 'assets/img/logo-horizontal-light.webp')).convert('RGBA')
    logo.thumbnail((300, 64)); im.paste(logo, (64, 52), logo)
    return im

def render(title, kicker, out):
    im = background(); d = ImageDraw.Draw(im)
    d.text((64, 178), kicker, font=font('figtree-latin-600-normal', 30), fill='#6FD9EE')
    for size in (78, 70, 62, 56, 50):
        f = font('bricolage-grotesque-latin-800-normal', size); lines = wrap(d, title, f, 1072)
        if len(lines) <= 3: break
    y = 228
    for ln in lines[:3]:
        d.text((64, y), ln, font=f, fill='#FFFFFF'); y += int(size * 1.12)
    small = font('figtree-latin-500-normal', 27)
    d.text((64, 548), 'myunimentor.in', font=small, fill='#9FB4C6')
    pill = 'Free 1-on-1 career counselling'; w = d.textlength(pill, font=small)
    d.rounded_rectangle((1136 - w - 40, 534, 1136, 590), radius=28, outline='#3B5A78', width=2)
    d.text((1136 - w - 20, 547), pill, font=small, fill='#FFFFFF')
    im.save(out, 'JPEG', quality=84, optimize=True, progressive=True)

def og_image(slug, title, kicker):
    """Returns the public URL of the share image for a page, creating it if the title changed."""
    try: cache = json.load(open(CACHE))
    except Exception: cache = {}
    key = hashlib.md5(f'v1|{title}|{kicker}'.encode()).hexdigest()[:10]
    rel = f'assets/og/{slug}.jpg'; out = os.path.join(ROOT, rel)
    if cache.get(slug) != key or not os.path.exists(out):
        try: render(title, kicker, out)
        except Exception as ex:
            print('share image skipped for', slug, '-', ex); return None
        cache[slug] = key
        json.dump(dict(sorted(cache.items())), open(CACHE, 'w'), indent=1)
    return f'https://myunimentor.in/{rel}'
