#!/usr/bin/env python3
"""Generate Open Graph share cards (1200×630 JPEG).

Default (no args): regenerate the homepage card at assets/img/og-card.jpg
(portrait + name/title), then every article/index card listed in CARDS.

Article cards: dark IIoT grid, section eyebrow, wrapped headline, domain.
Cards with a ``visual`` (a screenshot/diagram from the page itself) render a
two-panel layout: brand text on the left, the page's own diagram on the
right, plus a reading-time line. Cards without a visual keep the text-only
layout. Requires Pillow + TTFs in tools/fonts/ (see README / original script
header).

    python3 tools/generate-og-card.py          # all cards
    python3 tools/generate-og-card.py --home   # homepage only
    python3 tools/generate-og-card.py --articles note-ignition-alarms
    make og-cards
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

FONT_DIR = Path("tools/fonts")
PORTRAIT = Path("assets/img/portrait.jpg")
OUT_DIR = Path("assets/img/og")

# Homepage identity
NAME = "Sam Donche"
HOME_TITLE = "Industry 4.0 Consultant"
HOME_EYEBROW = "DIGITAL BACKBONE FOR FACTORIES"
HOME_CTA = "Get in touch →"
DOMAIN = "samdonche.com"
HOME_OUT = Path("assets/img/og-card.jpg")

# Per-page cards (slug → eyebrow, title, optional visual + reading minutes).
# Output: assets/img/og/<slug>.jpg. ``visual`` is an image from the page's own
# content (screenshot, diagram or animation poster); ``minutes`` is the article
# reading time shown on the card.
CARDS = [
    {"slug": "notes", "eyebrow": "NOTES", "title": "Field notes on industrial digital architecture"},
    {"slug": "case-studies", "eyebrow": "CASE STUDIES", "title": "Selected work on the plant floor"},
    {"slug": "publications", "eyebrow": "PUBLICATIONS", "title": "Research output from UZ Gent"},
    {
        "slug": "ignition-secrets",
        "eyebrow": "NOTE",
        "title": "Ignition credentials belong in your secrets manager",
        "visual": "assets/img/notes/designer-light.jpg",
        "minutes": 5,
    },
    {
        "slug": "ignition-observability",
        "eyebrow": "NOTE",
        "title": "Put your Ignition gateway on the same dashboards as everything else",
        "visual": "assets/img/notes/shot-observability.jpg",
        "minutes": 3,
    },
    {
        "slug": "ignition-historian",
        "eyebrow": "NOTE",
        "title": "Tag history that stays fast when retention gets long",
        "visual": "assets/img/notes/shot-historian.jpg",
        "minutes": 2,
    },
    {
        "slug": "ignition-amqp",
        "eyebrow": "NOTE",
        "title": "Stop scripting RabbitMQ inside Ignition",
        "visual": "assets/img/notes/shot-amqp.jpg",
        "minutes": 2,
    },
    {
        "slug": "ignition-alarms",
        "eyebrow": "NOTE",
        "title": "Page the channel the crew actually watches",
        "visual": "assets/img/notes/designer-dark.jpg",
        "minutes": 3,
    },
    {
        "slug": "ignition-perspective",
        "eyebrow": "NOTE",
        "title": "Fourteen Perspective components the platform never shipped",
        "visual": "assets/img/notes/poster-panzoom.jpg",
        "minutes": 2,
    },
    {
        "slug": "ignition-doom",
        "eyebrow": "NOTE",
        "title": "Yes, your Ignition gateway can run Doom",
        "visual": "assets/img/notes/doom-control-room.jpg",
        "minutes": 2,
    },
    {
        "slug": "ignition-dark-mode",
        "eyebrow": "NOTE",
        "title": "A dark Ignition Designer from one menu item",
        "visual": "assets/img/notes/designer-light.jpg",
        "minutes": 2,
    },
    {
        "slug": "ignition-modules",
        "eyebrow": "NOTE",
        "title": "Ignition modules for the gaps the platform leaves",
        "visual": "assets/img/notes/poster-grid.jpg",
        "minutes": 6,
    },
    {
        "slug": "mqtt-sparkplug-b",
        "eyebrow": "NOTE",
        "title": "MQTT and Sparkplug B: why factories stopped polling",
        "visual": "assets/img/notes/poster-timeline.jpg",
        "minutes": 8,
    },
    {
        "slug": "mes-scada-vs-historian",
        "eyebrow": "NOTE",
        "title": "MES vs SCADA vs historian: what actually goes where",
        "visual": "assets/img/notes/shot-grid.jpg",
        "minutes": 5,
    },
    {
        "slug": "factory-data-backbone",
        "eyebrow": "CASE STUDY",
        "title": "From data islands to a factory-wide backbone",
        "visual": "assets/img/notes/poster-grid.jpg",
        "minutes": 3,
    },
    {
        "slug": "plant-hmi",
        "eyebrow": "CASE STUDY",
        "title": "A chocolate plant in a browser tab",
        "visual": "assets/img/work/plant-hmi.jpg",
        "minutes": 5,
    },
    {
        "slug": "plant",
        "eyebrow": "PLANT LIVE VIEW",
        "title": "Line 3 — simulated packaging line at the edge",
        "visual": "assets/img/work/plant-hmi.jpg",
        "minutes": None,
    },
]

# Palette (site tokens)
S = 2
W, H = 1200 * S, 630 * S
BG = (2, 6, 23)
GRID = (12, 17, 34)
CYAN = (34, 211, 238)
CYAN_L = (103, 232, 249)
WHITE = (241, 245, 249)
SLATE3 = (203, 213, 225)
SLATE4 = (148, 163, 184)
BORDER = (30, 41, 59)
CARD_BG = (10, 16, 34)
ACCENT = (52, 211, 153)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size * S)


def tracked(draw: ImageDraw.ImageDraw, xy, text, fnt, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking * S
    return x


def base_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 48 * S):
        d.line([(x, 0), (x, H)], fill=GRID, width=S)
    for y in range(0, H, 48 * S):
        d.line([(0, y), (W, y)], fill=GRID, width=S)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-300 * S, -350 * S, 900 * S, 450 * S], fill=26)
    glow = glow.filter(ImageFilter.GaussianBlur(160 * S))
    img = Image.composite(Image.new("RGB", (W, H), CYAN), img, glow)
    return img, ImageDraw.Draw(img)


def wrap_title(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    """Greedy word wrap to fit max_width pixels."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = w if not cur else f"{cur} {w}"
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize((1200, 630), Image.LANCZOS).save(
        path, "JPEG", quality=90, optimize=True, progressive=True
    )
    print(f"wrote {path}")


def generate_home() -> None:
    img, d = base_canvas()
    eyebrow_f = font("jbm-500.ttf", 26)
    name_f = font("inter-800.ttf", 98)
    title_f = font("inter-600.ttf", 44)
    mono_f = font("jbm-400.ttf", 28)
    tiny_f = font("jbm-500.ttf", 18)
    cta_f = font("inter-600.ttf", 30)

    LX = 90 * S
    ey_y = 160 * S
    d.line([(LX, ey_y + 16 * S), (LX + 56 * S, ey_y + 16 * S)], fill=CYAN, width=2 * S)
    tracked(d, (LX + 76 * S, ey_y), HOME_EYEBROW, eyebrow_f, CYAN, tracking=3)
    d.text((LX, 215 * S), NAME, font=name_f, fill=WHITE)
    d.text((LX, 345 * S), HOME_TITLE, font=title_f, fill=SLATE3)

    cta_y = 440 * S
    pad_x, pad_y = 30 * S, 18 * S
    cta_w = int(d.textlength(HOME_CTA, font=cta_f)) + 2 * pad_x
    cta_h = 30 * S + 2 * pad_y
    d.rounded_rectangle([LX, cta_y, LX + cta_w, cta_y + cta_h], radius=10 * S, fill=CYAN)
    d.text((LX + pad_x, cta_y + pad_y - 2 * S), HOME_CTA, font=cta_f, fill=BG)

    dx = LX + cta_w + 40 * S
    d.ellipse(
        [dx, cta_y + cta_h // 2 - 7 * S, dx + 14 * S, cta_y + cta_h // 2 + 7 * S],
        fill=ACCENT,
    )
    d.text((dx + 28 * S, cta_y + cta_h // 2 - 17 * S), DOMAIN, font=mono_f, fill=SLATE4)

    card_w = 340 * S
    photo = Image.open(PORTRAIT)
    ph_h = int(card_w * photo.height / photo.width)
    head_h = 48 * S
    card_h = head_h + ph_h
    cx1 = W - card_w - 80 * S
    cy1 = (H - card_h) // 2
    cx2, cy2 = cx1 + card_w, cy1 + card_h
    d.rounded_rectangle(
        [cx1, cy1, cx2, cy2], radius=14 * S, fill=CARD_BG, outline=BORDER, width=2 * S
    )
    tracked(d, (cx1 + 20 * S, cy1 + 15 * S), "◇ samdonche/profile", tiny_f, CYAN_L, tracking=2)
    d.line([(cx1, cy1 + head_h), (cx2, cy1 + head_h)], fill=BORDER, width=2 * S)
    photo = photo.resize((card_w, ph_h), Image.LANCZOS)
    mask = Image.new("L", (card_w, ph_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, -20 * S, card_w, ph_h], radius=13 * S, fill=255)
    img.paste(photo, (cx1, cy1 + head_h), mask)
    d.rounded_rectangle([cx1, cy1, cx2, cy2], radius=14 * S, outline=BORDER, width=2 * S)

    save(img, HOME_OUT)


def generate_article(slug: str, eyebrow: str, title: str, visual: str | None = None, minutes: int | None = None) -> None:
    img, d = base_canvas()
    eyebrow_f = font("jbm-500.ttf", 26)
    title_f = font("inter-800.ttf", 64)
    mono_f = font("jbm-400.ttf", 28)
    name_f = font("inter-600.ttf", 32)
    tiny_f = font("jbm-500.ttf", 20)

    LX = 90 * S
    max_w = (W - 2 * LX) if not visual else int((W - 2 * LX) * 0.58)

    ey_y = 120 * S
    d.line([(LX, ey_y + 16 * S), (LX + 56 * S, ey_y + 16 * S)], fill=CYAN, width=2 * S)
    tracked(d, (LX + 76 * S, ey_y), eyebrow.upper(), eyebrow_f, CYAN, tracking=3)

    lines = wrap_title(d, title, title_f, max_w)
    # Cap at 3 lines; shrink font if still overflowing
    while len(lines) > 3:
        title_f = font("inter-800.ttf", max(40, title_f.size // S - 4))
        lines = wrap_title(d, title, title_f, max_w)

    line_h = int(title_f.size * 1.15)
    y = 200 * S
    for line in lines:
        d.text((LX, y), line, font=title_f, fill=WHITE)
        y += line_h

    # Visual panel: the page's own screenshot/diagram on the right half
    if visual:
        panel_x = int(W * 0.60)
        panel_w = W - panel_x - 60 * S
        panel_h = int(panel_w * 0.72)
        panel_y = (H - panel_h) // 2 + 20 * S
        try:
            shot = Image.open(visual)
            # cover-crop into the panel box
            scale = max(panel_w / shot.width, panel_h / shot.height)
            sw, sh = int(shot.width * scale), int(shot.height * scale)
            shot = shot.resize((sw, sh), Image.LANCZOS)
            left = (sw - panel_w) // 2
            top = (sh - panel_h) // 2
            shot = shot.crop((left, top, left + panel_w, top + panel_h))
            panel = Image.new("RGB", (panel_w, panel_h), CARD_BG)
            panel.paste(shot, (0, 0))
            d.rounded_rectangle(
                [panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                radius=14 * S, fill=CARD_BG, outline=BORDER, width=2 * S,
            )
            mask = Image.new("L", (panel_w, panel_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, panel_w, panel_h], radius=12 * S, fill=255)
            img.paste(panel, (panel_x, panel_y), mask)
            # header strip label on the panel
            d.rounded_rectangle(
                [panel_x + 16 * S, panel_y + 16 * S, panel_x + 138 * S, panel_y + 46 * S],
                radius=8 * S, fill=CARD_BG, outline=CYAN, width=1 * S,
            )
            tracked(d, (panel_x + 24 * S, panel_y + 23 * S), "FIG/PREVIEW", tiny_f, CYAN_L, tracking=2)
            d.rounded_rectangle(
                [panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                radius=14 * S, outline=BORDER, width=2 * S,
            )
        except Exception as e:  # noqa: BLE001 - be resilient; keep text-only card
            print(f"  (visual panel skipped for {slug}: {e})")

    # Reading-time line
    if minutes:
        rt_f = font("jbm-500.ttf", 26)
        rt_y = y + 12 * S
        d.ellipse([LX, rt_y + 12 * S, LX + 14 * S, rt_y + 26 * S], fill=ACCENT)
        tracked(d, (LX + 30 * S, rt_y), f"{minutes} MIN READ", rt_f, SLATE3, tracking=2)

    # Footer brand strip
    foot_y = H - 100 * S
    d.line([(LX, foot_y), (W - LX, foot_y)], fill=BORDER, width=S)
    d.text((LX, foot_y + 28 * S), NAME, font=name_f, fill=SLATE3)
    d.ellipse(
        [W - LX - 14 * S, foot_y + 40 * S, W - LX, foot_y + 54 * S],
        fill=ACCENT,
    )
    dom_w = d.textlength(DOMAIN, font=mono_f)
    d.text((W - LX - 28 * S - dom_w, foot_y + 28 * S), DOMAIN, font=mono_f, fill=SLATE4)

    save(img, OUT_DIR / f"{slug}.jpg")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--home", action="store_true", help="homepage card only")
    ap.add_argument("--articles", nargs="*", metavar="SLUG", help="article cards only (default: all); pass slugs to select")
    ap.add_argument("--list", action="store_true", help="list card slugs")
    args = ap.parse_args()

    if args.list:
        for card in CARDS:
            print(card["slug"])
        return 0

    if args.home:
        generate_home()
        return 0

    if args.articles:
        slugs = set(args.articles)
        selected = [c for c in CARDS if c["slug"] in slugs]
        missing = slugs - {c["slug"] for c in selected}
        if missing:
            print(f"unknown slugs: {sorted(missing)}")
            return 2
        for card in selected:
            generate_article(card["slug"], card["eyebrow"], card["title"], card.get("visual"), card.get("minutes"))
        return 0

    generate_home()
    for card in CARDS:
        generate_article(card["slug"], card["eyebrow"], card["title"], card.get("visual"), card.get("minutes"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
