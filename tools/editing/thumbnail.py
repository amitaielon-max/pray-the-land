#!/usr/bin/env python3
"""YouTube thumbnail: best land frame, warm grade, serif title over a navy
gradient from the bottom, thin gold rule. 1280x720, readable at phone size.

    npm run thumbnail -- <slug> <video-or-clip> <seconds> "<Film Title>"

Writes output/<slug>/<slug>_thumbnail.jpg
"""

import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, fail, load_config, run

cfg = load_config()
W, H = 1280, 720
NAVY = (20, 33, 61)
GOLD = "#C9A227"
CREAM = "#fdfcf8"
FONTS = os.path.join(ROOT, cfg["fontsDir"])

if len(sys.argv) != 5:
    fail('usage: thumbnail.py <slug> <video> <seconds> "<Film Title>"')
slug, video, secs, title = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
if not os.path.exists(video):
    fail("no such video: " + video)

out_dir = os.path.join(ROOT, cfg["outputDir"], slug)
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, f"{slug}_thumbnail.jpg")

with tempfile.TemporaryDirectory() as td:
    frame = os.path.join(td, "frame.png")
    run([
        "ffmpeg", "-y", "-ss", secs, "-i", video, "-frames:v", "1",
        "-vf", cfg["grade"]["filter"] + f",scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
        frame,
    ])
    im = Image.open(frame).convert("RGB")

# navy gradient from the bottom
grad = Image.new("L", (1, H), 0)
for y in range(H):
    t = max(0.0, (y / H - 0.45) / 0.55)
    grad.putpixel((0, y), int(235 * (t ** 1.4)))
grad = grad.resize((W, H))
im = Image.composite(Image.new("RGB", (W, H), NAVY), im, grad)

d = ImageDraw.Draw(im)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


f = font("EBGaramond-SemiBold.ttf", 92)
while d.textlength(title, font=f) > W - 140 and f.size > 48:
    f = font("EBGaramond-SemiBold.ttf", f.size - 6)
tw = d.textlength(title, font=f)
ty = H - 96 - f.size
# thin gold rule above the title
d.rectangle([(W - 170) / 2, ty - 34, (W + 170) / 2, ty - 31], fill=GOLD)
d.text(((W - tw) / 2, ty), title, font=f, fill=CREAM)
d.text(((W - d.textlength("FILMS FROM THE LAND", font=font("EBGaramond-Medium.ttf", 30))) / 2, H - 62),
       "FILMS FROM THE LAND", font=font("EBGaramond-Medium.ttf", 30), fill=GOLD)

im.save(out, quality=88, optimize=True)
print("thumbnail OK: " + out)
