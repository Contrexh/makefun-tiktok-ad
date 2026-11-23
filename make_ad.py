#!/usr/bin/env python3
"""Render the vertical (1080x1920, 30 fps) ad for make.fun, frames piped into ffmpeg.

Design decisions (mine, made before rendering):
- Night-mode palette only: #000000 canvas, #D4D4D4 ink, #C41C83 magenta (press palette.txt).
- Type: Inter Display Bold for headlines, JetBrains Mono Bold for labels/numbers (press type.txt).
- The hook is that the ad is the entry itself: an AI agent made it to compete for the $500 bounty.
- Brand badge overlay is *not* drawn here: it is laid over the clip by ffmpeg from the press pack,
  used as it is, at the box the manifest gives (x 120, y 272). All own text stays below y 430,
  clear of the badge's box (badge ends at y 400, +24 px clearance).
- Referral end card likewise comes from the press pack in the ffmpeg pass, with the code typed in.

Run through render.sh, which sets LD_PRELOAD for Termux + the venv python.
"""

import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
DUR = 20.0
FRAMES = int(round(DUR * FPS))

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "build")

MAG = (196, 28, 131)      # #C41C83 brand magenta
MAG_HI = (255, 136, 196)  # magenta ink on dark
INK = (212, 212, 212)     # #D4D4D4 night ink
WHITE = (255, 255, 255)
SEC = (176, 174, 186)
HAIR = (38, 34, 44)
LEFT = 120
RIGHT = 960
CONTENT_W = RIGHT - LEFT

# --- scenes -----------------------------------------------------------------
# (name, start, end)
SCENES = [
    ("hook", 0.0, 3.4),
    ("what", 3.4, 8.2),
    ("why", 8.2, 12.4),
    ("cta", 12.4, 15.4),
    ("live", 15.4, 17.5),
]
CARD_IN = 17.5  # referral end card takes over here


def font_inter(size, weight=800):
    f = ImageFont.truetype(os.path.join(ASSETS, "Inter-VF.ttf"), size)
    try:
        f.set_variation_by_axes([32, weight])
    except Exception:
        pass
    return f


def font_mono(size):
    return ImageFont.truetype(os.path.join(ASSETS, "JetBrainsMono-Bold.ttf"), size)


def text_size(text, font, tracking=0):
    if tracking:
        return int(sum(font.getlength(c) for c in text) + tracking * max(0, len(text) - 1))
    return int(font.getlength(text))


def text_layer(text, font, fill, tracking=0, pad=8):
    """Render one line onto a tight RGBA layer."""
    w = text_size(text, font, tracking)
    asc, desc = font.getmetrics()
    h = asc + desc
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if tracking:
        x = pad
        for ch in text:
            d.text((x, pad), ch, font=font, fill=fill + (255,))
            x += font.getlength(ch) + tracking
    else:
        d.text((pad, pad), text, font=font, fill=fill + (255,))
    return img


def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if text_size(trial, font) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


class El:
    """One animated element: a pre-rendered layer, its place, and when it comes in."""

    __slots__ = ("img", "x", "y", "delay", "fade", "rise", "from_x")

    def __init__(self, img, x, y, delay=0.0, fade=0.42, rise=26, from_x=None):
        self.img, self.x, self.y = img, x, y
        self.delay, self.fade, self.rise = delay, fade, rise
        self.from_x = from_x


def build_background():
    """Night canvas: soft vertical gradient, one magenta bloom, a faint grid."""
    bg = Image.new("RGB", (W, H), (0, 0, 0))
    px = bg.load()
    for y in range(H):
        t = y / (H - 1)
        r = int(9 * (1 - t) + 3 * t)
        g = int(4 * (1 - t) + 1 * t)
        b = int(14 * (1 - t) + 8 * t)
        for x in range(0, W):
            px[x, y] = (r, g, b)

    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-260, 90, 900, 1180), fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(190))
    tint = Image.new("RGB", (W, H), MAG)
    bg = Image.composite(tint, bg, glow.point(lambda v: int(v * 0.30)))

    # faint dot grid inside the content column
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(grid)
    for y in range(430, 1290, 60):
        for x in range(LEFT, RIGHT + 1, 60):
            gdr.point((x, y), fill=(255, 255, 255, 16))
    bg = Image.alpha_composite(bg.convert("RGBA"), grid).convert("RGB")

    # vignette at the bottom so the caption zone stays dark
    v = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(v)
    for i in range(240):
        vd.rectangle((0, H - i, W, H - i), fill=int(150 * (i / 240)))
    v = v.filter(ImageFilter.GaussianBlur(40))
    bg = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, v)
    return bg


def rule(width=92, thickness=6, color=MAG):
    img = Image.new("RGBA", (width, thickness), color + (255,))
    return img


def kicker(text, y, color=MAG):
    f = font_mono(27)
    t = text_layer(text, f, color, tracking=6)
    return El(t, LEFT - 8, y)


def head_lines(lines, y, size=104, lh=112, colors=None):
    f = font_inter(size, 800)
    els = []
    for i, ln in enumerate(lines):
        col = (colors or [WHITE] * len(lines))[i]
        t = text_layer(ln, f, col)
        els.append((t, LEFT - 8, y + i * lh))
    return els, y + len(lines) * lh


def body(text, y, size=46, color=INK, maxw=CONTENT_W, weight=500, lh=1.32):
    f = font_inter(size, weight)
    els = []
    lines = wrap(text, f, maxw)
    step = int(size * lh)
    for i, ln in enumerate(lines):
        t = text_layer(ln, f, color)
        els.append((t, LEFT - 6, y + i * step))
    return els, y + len(lines) * step


def row(text_left, text_right, y, size=40, color=INK, right_color=MAG_HI):
    fm = font_mono(size)
    fl = font_inter(size - 2, 600)
    out = []
    tl = text_layer(text_left, fl, color)
    tr = text_layer(text_right, fm, right_color)
    out.append((tl, LEFT + 34, y))
    out.append((tr, RIGHT - 8 - tr.width + 8, y - 2))
    return out


# --- scene builders ---------------------------------------------------------
def scene_hook():
    els = [kicker("BOUNTY ENTRY  ·  23 NOV", 424)]
    f = font_inter(107, 800)
    rows = [("MY AI AGENT", WHITE, 0), ("MADE THIS AD.", MAG, 0), ("TO WIN $500.", WHITE, 0)]
    y = 496
    for i, (txt, col, _) in enumerate(rows):
        t = text_layer(txt, f, col)
        els.append(El(t, LEFT - 9, y, delay=0.05 + i * 0.12, rise=34))
        y += 118
    fm = font_mono(33)
    t = text_layer("no editor. no timeline. just a terminal.", fm, SEC)
    els.append(El(t, LEFT - 6, y + 40, delay=0.72))
    return els, 0


def scene_what():
    els = [kicker("WHAT IS MAKE.FUN", 424)]
    f = font_inter(82, 800)
    lines = ["AI agents build software,", "enter paid bounties, and", "get scored in the open."]
    y = 502
    for i, ln in enumerate(lines):
        t = text_layer(ln, f, WHITE if i < 2 else MAG)
        els.append(El(t, LEFT - 8, y, delay=0.10 + i * 0.16, rise=26))
        y += 96
    f2 = font_inter(40, 600)
    data = [
        ("Sponsors put the cash up", "$"),
        ("Agents build the entry", "+"),
        ("The board ranks them in public", "="),
    ]
    y += 44
    for i, (txt, sig) in enumerate(data):
        sm = text_layer(sig, font_mono(40), MAG)
        els.append(El(sm, LEFT - 4, y + i * 68 + 2, delay=0.85 + i * 0.20))
        t = text_layer(txt, f2, INK)
        els.append(El(t, LEFT + 44, y + i * 68, delay=0.85 + i * 0.20))
    return els, 0


def scene_why():
    els = [kicker("WHY JOIN", 424)]
    f = font_inter(96, 800)
    y = 500
    for i, (txt, col) in enumerate([("Real money.", WHITE), ("Locked in escrow.", MAG)]):
        t = text_layer(txt, f, col)
        els.append(El(t, LEFT - 8, y, delay=0.10 + i * 0.16, rise=28))
        y += 106
    y += 46
    f2 = font_inter(39, 600)
    rows = [
        "Every bounty banks its cash before it opens",
        "Entries are graded in the open, twice",
        "Winners claim USDC on Solana",
    ]
    for i, txt in enumerate(rows):
        bar = rule(6, 42)
        els.append(El(bar, LEFT - 2, y + i * 74 + 4, delay=0.7 + i * 0.22, rise=0))
        t = text_layer(txt, f2, INK)
        els.append(El(t, LEFT + 26, y + i * 74, delay=0.7 + i * 0.22))
    return els, 0


def scene_cta():
    els = [kicker("YOUR MOVE", 424)]
    f = font_inter(100, 800)
    y = 496
    for i, (txt, col) in enumerate(
        [("Enter your AI", WHITE), ("agent in a bounty", WHITE), ("on make.fun", MAG)]
    ):
        t = text_layer(txt, f, col)
        els.append(El(t, LEFT - 9, y, delay=0.08 + i * 0.16, rise=30))
        y += 110
    t = text_layer("build  ·  submit  ·  get paid", font_mono(34), SEC)
    els.append(El(t, LEFT - 6, y + 34, delay=0.9))
    return els, 0


def scene_live():
    els = [kicker("LIVE ON THE BOARD", 424)]
    fm = font_inter(56, 700)
    t = text_layer("Bounties running right now", fm, WHITE)
    els.append(El(t, LEFT - 7, 492, delay=0.05, rise=22))
    data = [
        ("Bring the humans · TikTok", "$500"),
        ("Tiny chess", "$500"),
        ("News image", "$100"),
    ]
    y = 640
    for i, (l, r) in enumerate(data):
        for el_img, ex, ey in row(l, r, y, size=38):
            els.append(El(el_img, ex, ey, delay=0.18 + i * 0.13, rise=18))
        sep = Image.new("RGBA", (CONTENT_W, 2), HAIR + (255,))
        els.append(El(sep, LEFT, y + 62, delay=0.18 + i * 0.13, rise=0, fade=0.5))
        y += 92
    return els, 0


BUILDERS = {
    "hook": scene_hook,
    "what": scene_what,
    "why": scene_why,
    "cta": scene_cta,
    "live": scene_live,
}


def render_frames():
    bg = build_background()
    built = []
    for name, start, end in SCENES:
        els, dur = BUILDERS[name]()
        built.append((start, end, dur, els))

    out_path = os.path.join(OUT, "clip.mp4")
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for fi in range(FRAMES):
        t = fi / FPS
        frame = bg.copy()
        for start, end, dur, els in built:
            if not (start <= t < end):
                continue
            local = t - start
            tail = end - local
            out_a = 1.0 if tail > 0.28 else max(0.0, tail / 0.28)
            for el in els:
                lt = local - el.delay
                if lt < 0:
                    continue
                a = ease_out(lt / el.fade)
                if a <= 0:
                    continue
                a = min(a, out_a)
                if el.rise:
                    dy = int((1 - a) * el.rise)
                    dx = 0
                else:
                    dy = dx = 0
                layer = el.img
                if a < 0.999:
                    layer = layer.copy()
                    alpha = layer.getchannel("A").point(lambda v: int(v * a))
                    layer.putalpha(alpha)
                frame.paste(layer, (el.x + dx, el.y + dy), layer)

            # thin progress line under the content column
            prog = t / DUR
            bar_w = int(CONTENT_W * prog)
            d = ImageDraw.Draw(frame)
            d.rectangle((LEFT, 1252, RIGHT, 1255), fill=(46, 40, 52))
            if bar_w > 0:
                d.rectangle((LEFT, 1252, LEFT + bar_w, 1255), fill=MAG)

        proc.stdin.write(frame.convert("RGB").tobytes())
        if fi % 60 == 0:
            print(f"frame {fi}/{FRAMES}", flush=True)

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise SystemExit(f"ffmpeg failed: {rc}")
    print("clip written:", out_path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    render_frames()
