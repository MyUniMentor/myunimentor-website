"""Add campus photos to a university page.
Usage: python3 tools/uniphotos.py <university-slug> photo1.jpg [photo2.jpg ...]
The first photo is the hero; the rest form the gallery. Makes a 1200px and a 640px WebP of each.
"""
import sys, os
from PIL import Image, ImageOps
slug, files = sys.argv[1], sys.argv[2:]
out = 'assets/img/unis'; os.makedirs(out, exist_ok=True)
for i, f in enumerate(files, 1):
    im = ImageOps.exif_transpose(Image.open(f)).convert('RGB')
    w, h = im.size
    if w / h > 1.6: nw = int(h * 1.6); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w / h < 1.1: nh = int(w / 1.1); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    for width, suffix in [(1200, ''), (640, '-sm')]:
        r = im.copy(); r.thumbnail((width, 10000), Image.LANCZOS)
        r.save(f'{out}/{slug}-{i}{suffix}.webp', 'WEBP', quality=72, method=6)
    print(f'{out}/{slug}-{i}.webp', os.path.getsize(f'{out}/{slug}-{i}.webp') // 1024, 'KB')
