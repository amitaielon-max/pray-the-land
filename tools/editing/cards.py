#!/usr/bin/env python3
"""Series cards: opening title card and closing card, navy and gold spec.

    npm run cards -- templates
        (re)build the base templates in assets/cards/:
        title-card-base.png (navy + gold rules, no text) and
        closing-card.png (complete, identical every episode)

    npm run cards -- title <slug> <ROMAN> "<Place>" "<Film Title>"
        overlay the film's text on the base template and write
        output/<slug>/title-card.png

Spec (6.4): navy #14213d, thin gold #C9A227 rule, serif (EB Garamond),
never a startup sans-serif.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, fail, load_config, roman_or_fail

cfg = load_config()
W, H = 1920, 1080
NAVY = cfg["cards"]["navy"]
GOLD = cfg["cards"]["gold"]
CREAM = cfg["cards"]["cream"]
FONTS = os.path.join(ROOT, cfg["fontsDir"])
CARDS = os.path.join(ROOT, cfg["cardsDir"])


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def center(draw, y, text, f, fill, tracking=0):
    if tracking:
        text = (" " * 1).join(text)  # simple letterspacing for the series line
    w = draw.textlength(text, font=f)
    draw.text(((W - w) / 2, y), text, font=f, fill=fill)
    return w


def rule(draw, y, width=220):
    x = (W - width) / 2
    draw.rectangle([x, y, x + width, y + 3], fill=GOLD)


def base_card():
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    # a whisper of depth, still one navy family
    for i in range(H):
        if i > H * 0.62:
            t = (i - H * 0.62) / (H * 0.38)
            d.line([(0, i), (W, i)], fill=(20 + int(8 * t), 33 + int(7 * t), 61 + int(9 * t)))
    return im


def build_templates():
    os.makedirs(CARDS, exist_ok=True)

    # title card base: series line + rules, film text added per film
    im = base_card()
    d = ImageDraw.Draw(im)
    center(d, 214, "F I L M S   F R O M   T H E   L A N D", font("EBGaramond-SemiBold.ttf", 54), GOLD)
    rule(d, 320)
    im.save(os.path.join(CARDS, "title-card-base.png"))

    # closing card: identical every episode, complete now
    im = base_card()
    d = ImageDraw.Draw(im)
    center(d, 268, "Answer me with your own film.", font("EBGaramond-Italic.ttf", 84), CREAM)
    rule(d, 420)
    center(d, 500, "WhatsApp +972 54 444 2054", font("EBGaramond-Medium.ttf", 56), CREAM)
    center(d, 596, "pray-the-land-golan.netlify.app/films", font("EBGaramond-Medium.ttf", 56), GOLD)
    center(d, 736, "Stand with the Land  ·  paypal.me/amitaielon", font("EBGaramond-Medium.ttf", 46), CREAM)
    im.save(os.path.join(CARDS, "closing-card.png"))

    print("cards OK:")
    print("  " + os.path.join(CARDS, "title-card-base.png"))
    print("  " + os.path.join(CARDS, "closing-card.png"))


def build_title(slug, num, place, title):
    base = os.path.join(CARDS, "title-card-base.png")
    if not os.path.exists(base):
        build_templates()
    im = Image.open(base).convert("RGB")
    d = ImageDraw.Draw(im)
    center(d, 452, f"Film {num} · {place}", font("EBGaramond-Medium.ttf", 62), CREAM)
    t = f"“{title}”"
    f = font("EBGaramond-Medium.ttf", 108)
    while d.textlength(t, font=f) > W - 300 and f.size > 56:
        f = font("EBGaramond-Medium.ttf", f.size - 6)
    center(d, 596, t, f, CREAM)
    out_dir = os.path.join(ROOT, cfg["outputDir"], slug)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "title-card.png")
    im.save(out)
    print("title card OK: " + out)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["templates"]:
        build_templates()
    elif args[:1] == ["title"] and len(args) == 5:
        build_title(args[1], roman_or_fail(args[2]), args[3], args[4])
    else:
        fail('usage: cards.py templates | cards.py title <slug> <ROMAN> "<Place>" "<Film Title>"')
