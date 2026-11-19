"""news-image-20261119 v3 — "The World in One Day".

A broadsheet front page summing up Thursday 19 November 2026 in one
1024x1024 PNG. Pure Python standard library only: a small rasteriser,
a hand-drawn 5x7 bitmap font and a hand-rolled PNG encoder.

Six verified stories of the day (each first reported 19 Nov 2026):
  1. EU proposes a 45bn euro loan for Ukraine, repaid only after
     Russia pays reparations (Financial Times / Jagran Josh).
  2. GTA VI begins its global rollout; gamers enter Vice City
     (Jagran Josh top world news).
  3. NASA's Voyager 1 reaches one light-day from Earth after almost
     50 years in space (Jagran Josh / Disclosure News).
  4. Australia, Canada, Italy and the UK call on Israel to open
     Gaza aid access as floods worsen (The Paris Eye).
  5. Israel's president taps Gadi Eisenkot to form the next
     government, bypassing Netanyahu (The Paris Eye).
  6. Finland approves the world's first spent-nuclear-fuel
     repository for operation (The Germany Eye).

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   -> out/entry.png
The output is deterministic: two runs write identical bytes.
"""
import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap font, drawn from scratch for this entry.
# '#' = ink, '.' = empty.
FONT = {
    "A": ("..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
}

MASTHEAD_TITLE = "THE WORLD IN ONE DAY"
MASTHEAD_DATE = "THURSDAY 19 NOVEMBER 2026"

# panel rects: (x0, y0, x1, y1)
STORIES = [
    {
        "kicker": "EUROPE",
        "headline": "EU PROPOSES 45BN EURO LOAN FOR UKRAINE",
        "subhead": "BRUSSELS WILL BORROW ON THE MARKETS. KYIV REPAYS ONLY AFTER RUSSIA PAYS REPARATIONS.",
        "panel": (16, 132, 640, 576),
        "art": "eu",
        "text_w": 592,
        "headline_scale": 4,
    },
    {
        "kicker": "CULTURE",
        "headline": "VICE CITY RETURNS",
        "subhead": "GTA VI BEGINS ITS GLOBAL ROLLOUT.",
        "panel": (656, 132, 1008, 348),
        "art": "gta",
        "text_w": 320,
        "headline_scale": 3,
    },
    {
        "kicker": "SPACE",
        "headline": "VOYAGER 1 REACHES ONE LIGHT-DAY",
        "subhead": "AFTER ALMOST 50 YEARS.",
        "panel": (656, 360, 1008, 576),
        "art": "voyager",
        "text_w": 320,
        "headline_scale": 3,
    },
    {
        "kicker": "MIDDLE EAST",
        "headline": "FOUR NATIONS DEMAND GAZA AID ACCESS",
        "subhead": "AUSTRALIA, CANADA, ITALY AND THE UK URGE ISRAEL TO OPEN CROSSINGS AS FLOODS WORSEN.",
        "panel": (16, 592, 338, 1008),
        "art": "gaza",
        "text_w": 290,
        "headline_scale": 3,
    },
    {
        "kicker": "ISRAEL",
        "headline": "EISENKOT TAPPED TO LEAD ISRAEL",
        "subhead": "PRESIDENT HERZOG ASKS THE EX-ARMY CHIEF TO FORM A GOVERNMENT, PASSING OVER NETANYAHU.",
        "panel": (350, 592, 672, 1008),
        "art": "israel",
        "text_w": 290,
        "headline_scale": 3,
    },
    {
        "kicker": "SCIENCE",
        "headline": "FINLAND OPENS FIRST NUCLEAR WASTE TOMB",
        "subhead": "WORLD'S FIRST SPENT-FUEL REPOSITORY APPROVED FOR OPERATION.",
        "panel": (684, 592, 1008, 1008),
        "art": "finland",
        "text_w": 292,
        "headline_scale": 3,
    },
]

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 227)
INK = (23, 19, 14)
RED = (179, 39, 30)
GOLD = (242, 183, 5)
EU_BLUE = (32, 64, 140)
EU_BLUE_DARK = (22, 44, 96)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SLATE = (52, 68, 92)
SKY = (176, 205, 224)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        for y in range(y0, y1):
            i = self._idx(x0, y)
            for x in range(x0, x1):
                self.buf[i] = color[0]
                self.buf[i + 1] = color[1]
                self.buf[i + 2] = color[2]
                i += 3

    def vgrad_rect(self, x0, y0, x1, y1, top, bottom):
        for y in range(y0, y1):
            t = (y - y0) / max(1, (y1 - y0 - 1))
            c = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
            self.fill_rect(x0, y, x1, y + 1, c)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, color)

    def ring(self, cx, cy, r, thick, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if (r - thick) ** 2 <= d2 <= r * r:
                    self.set(x, y, color)

    def poly(self, pts, color):
        """Scanline fill of a simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, color)

    def star(self, cx, cy, r_outer, r_inner, color, rot=-math.pi / 2):
        pts = []
        for i in range(10):
            r = r_outer if i % 2 == 0 else r_inner
            a = rot + i * math.pi / 5
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        self.poly(pts, color)


# ---------------------------------------------------------------- text
def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, color):
    cx = x
    for ch in text:
        if ch == " ":
            cx += 6 * scale
            continue
        glyph = FONT[ch]
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 cx + (col + 1) * scale, y + (row + 1) * scale,
                                 color)
        cx += 6 * scale
    return cx


def wrap_text(text, scale, max_w):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


def draw_text_block(cv, x, y, text, scale, max_w, color, leading=2):
    lines = wrap_text(text, scale, max_w)
    for line in lines:
        draw_text(cv, x, y, line, scale, color)
        y += 7 * scale + leading
    return y


def draw_text_centered(cv, cx, y, text, scale, color):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, scale, color)


# ---------------------------------------------------------------- art
def art_eu(cv, x0, y0, x1, y1):
    cv.fill_rect(x0, y0, x1, y1, EU_BLUE)
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2 - 30
    R = 92
    for i in range(12):
        a = -math.pi / 2 + i * math.pi / 6
        cv.star(int(cx + R * math.cos(a)), int(cy + R * math.sin(a)),
                17, 7, GOLD)
    draw_text_centered(cv, cx, cy - 26, "45BN", 6, GOLD)
    draw_text_centered(cv, cx, cy + 22, "EURO LOAN", 3, WHITE)
    # gold baseline of coins
    for i in range(9):
        cv.circle(x0 + 60 + i * 56, y1 - 26, 14, GOLD)
        cv.ring(x0 + 60 + i * 56, y1 - 26, 14, 3, (200, 150, 0))


def art_gta(cv, x0, y0, x1, y1):
    ah = y1 - y0
    cv.vgrad_rect(x0, y0, x1, y1 - 30, (255, 46, 136), (123, 47, 247))
    cv.vgrad_rect(x0, y1 - 30, x1, y1, (40, 16, 80), (20, 8, 48))
    cx = (x0 + x1) // 2
    sun_r = min(34, ah // 4)
    cv.circle(cx, y0 + ah // 3, sun_r, (255, 214, 130))
    cv.circle(cx, y0 + ah // 3, max(8, sun_r - 8), (255, 236, 180))
    # skyline silhouette, heights scaled to the art region
    base = y1 - 30
    raw_heights = [52, 88, 40, 110, 66, 96, 48, 78, 58, 92, 44]
    max_h = ah - 45
    heights = [int(h * max_h / 110) for h in raw_heights]
    bw = (x1 - x0) // len(heights)
    for i, hgt in enumerate(heights):
        bx = x0 + i * bw
        cv.fill_rect(bx + 2, base - hgt, bx + bw - 2, base, (24, 10, 44))
        # lit windows
        for wy in range(base - hgt + 8, base - 6, 14):
            for wx in range(bx + 6, bx + bw - 6, 12):
                if (wx * 7 + wy * 13) % 5 < 2:
                    cv.fill_rect(wx, wy, wx + 4, wy + 5, (255, 200, 90))
    # palm silhouettes
    for px, lean in ((x0 + 26, -1), (x1 - 30, 1)):
        cv.line(px, base, px + lean * 10, base - 40, (16, 8, 32))
        for k in range(5):
            ang = -math.pi / 2 + (k - 2) * 0.45
            ex = int(px + lean * 10 + 24 * math.cos(ang))
            ey = int(base - 40 + 13 * math.sin(ang))
            cv.line(px + lean * 10, base - 40, ex, ey, (16, 8, 32))
    # sun reflection on water
    for i in range(6):
        cv.fill_rect(cx - 60 + i * 20, y1 - 22 + i * 3, cx + 60 - i * 20,
                     y1 - 19 + i * 3, (255, 120, 170))


def art_voyager(cv, x0, y0, x1, y1):
    cv.fill_rect(x0, y0, x1, y1, (4, 6, 18))
    # deterministic star field
    seed = 1234567
    for _ in range(90):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sx = x0 + seed % (x1 - x0)
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sy = y0 + seed % (y1 - y0)
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        r = 1 + seed % 2
        cv.circle(sx, sy, r, (220, 225, 240) if seed % 4 else (255, 240, 200))
    # pale blue dot (Earth, far behind)
    cv.circle(x0 + 40, y0 + 34, 5, (120, 170, 230))
    # probe: gold body, dish, boom
    px, py = (x0 + x1) // 2 + 30, (y0 + y1) // 2
    cv.line(px - 70, py + 40, px + 30, py - 10, (200, 200, 210))
    cv.fill_rect(px - 6, py - 22, px + 34, py + 6, (212, 175, 55))
    cv.fill_rect(px - 6, py - 22, px + 34, py - 14, (240, 205, 90))
    cv.ring(px - 52, py + 26, 30, 5, (230, 230, 235))
    cv.line(px - 52, py + 26, px - 6, py - 8, (200, 200, 210))
    cv.line(px + 34, py - 8, px + 58, py - 34, (200, 200, 210))
    cv.circle(px + 58, py - 34, 3, (255, 80, 60))
    # signal waves from the dish
    for r in (44, 56):
        cv.ring(px - 52, py + 26, r, 2, (140, 180, 255))


def art_gaza(cv, x0, y0, x1, y1):
    cv.vgrad_rect(x0, y0, x1, y1, (96, 116, 140), (160, 178, 196))
    # rain streaks
    seed = 987654
    for _ in range(70):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        rx = x0 + seed % (x1 - x0)
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        ry = y0 + seed % (y1 - y0 - 30)
        cv.line(rx, ry, rx - 6, ry + 16, (210, 225, 240))
    # flooded ground
    cv.fill_rect(x0, y1 - 46, x1, y1, (70, 96, 122))
    cv.fill_rect(x0, y1 - 46, x1, y1 - 40, (200, 214, 228))
    # aid truck
    tx, ty = x0 + 40, y1 - 120
    cv.fill_rect(tx, ty, tx + 150, ty + 56, WHITE)
    cv.fill_rect(tx + 150, ty + 14, tx + 196, ty + 56, (200, 40, 30))
    cv.fill_rect(tx + 158, ty + 20, tx + 188, ty + 36, (170, 205, 225))
    cv.circle(tx + 40, ty + 60, 13, BLACK)
    cv.circle(tx + 40, ty + 60, 6, (120, 120, 120))
    cv.circle(tx + 160, ty + 60, 13, BLACK)
    cv.circle(tx + 160, ty + 60, 6, (120, 120, 120))
    draw_text(cv, tx + 34, ty + 18, "AID", 3, RED)
    # stacked boxes
    for bx, by in ((x0 + 236, y1 - 84), (x0 + 262, y1 - 84), (x0 + 249, y1 - 110)):
        cv.fill_rect(bx, by, bx + 24, by + 24, (196, 164, 110))
        cv.fill_rect(bx, by, bx + 24, by + 4, (160, 128, 80))


def art_israel(cv, x0, y0, x1, y1):
    cv.vgrad_rect(x0, y0, x1, y1, (214, 228, 240), (240, 236, 222))
    cx = (x0 + x1) // 2
    base = y1 - 30
    # Knesset: steps, columns, dome
    cv.fill_rect(x0 + 30, base - 12, x1 - 30, base, (150, 146, 132))
    cv.fill_rect(x0 + 46, base - 22, x1 - 46, base - 12, (168, 164, 150))
    for i in range(6):
        colx = x0 + 58 + i * 38
        cv.fill_rect(colx, base - 92, colx + 16, base - 22, (226, 222, 208))
    # dome: full circle first, then the roofline drawn over its lower
    # half so only the semicircle shows above the building
    cv.circle(cx, base - 106, 52, (196, 190, 172))
    cv.fill_rect(x0 + 46, base - 106, x1 - 46, base - 92, (210, 206, 192))
    # flag on a pole (kept short so it stays inside the art region)
    cv.line(x1 - 52, base - 116, x1 - 52, base - 96, (90, 90, 90))
    cv.fill_rect(x1 - 50, base - 116, x1 - 8, base - 86, WHITE)
    cv.fill_rect(x1 - 50, base - 116, x1 - 8, base - 110, (0, 56, 184))
    cv.fill_rect(x1 - 50, base - 92, x1 - 8, base - 86, (0, 56, 184))
    cv.star(x1 - 29, base - 101, 7, 3, (0, 56, 184))
    # ballot box
    cv.fill_rect(x0 + 34, base - 52, x0 + 78, base - 12, (179, 39, 30))
    cv.fill_rect(x0 + 46, base - 62, x0 + 66, base - 52, WHITE)


def art_finland(cv, x0, y0, x1, y1):
    # cross-section: green surface, brown rock strata, dark tunnel
    cv.fill_rect(x0, y0, x1, y0 + 34, (96, 140, 84))
    cv.fill_rect(x0, y0 + 34, x1, y1, (122, 96, 70))
    cv.fill_rect(x0, y0 + 90, x1, y1, (104, 80, 58))
    cv.fill_rect(x0, y0 + 150, x1, y1, (88, 66, 48))
    for yy in (y0 + 60, y0 + 120, y0 + 178):
        cv.fill_rect(x0, yy, x1, yy + 3, (70, 52, 38))
    # pine trees on the surface
    for tx in (x0 + 30, x0 + 70, x1 - 60, x1 - 26):
        cv.poly([(tx, y0 + 4), (tx - 10, y0 + 26), (tx + 10, y0 + 26)],
                (34, 84, 48))
        cv.fill_rect(tx - 2, y0 + 26, tx + 2, y0 + 34, (60, 44, 28))
    # tunnel with canister
    tx0, ty0 = x0 + 60, y1 - 96
    cv.fill_rect(tx0, ty0, x1 - 60, y1 - 26, (24, 18, 14))
    # copper canister
    canx = (x0 + x1) // 2 - 34
    cv.fill_rect(canx, y1 - 82, canx + 68, y1 - 30, (184, 115, 51))
    cv.fill_rect(canx, y1 - 82, canx + 68, y1 - 74, (214, 145, 80))
    cv.fill_rect(canx + 8, y1 - 66, canx + 60, y1 - 62, (140, 84, 34))
    cv.fill_rect(canx + 8, y1 - 48, canx + 60, y1 - 44, (140, 84, 34))
    draw_text(cv, x0 + 14, y0 + 44, "ONKALO", 2, (235, 225, 205))
    draw_text(cv, x0 + 14, y0 + 62, "500 M DOWN", 2, (235, 225, 205))


ART = {
    "eu": art_eu,
    "gta": art_gta,
    "voyager": art_voyager,
    "gaza": art_gaza,
    "israel": art_israel,
    "finland": art_finland,
}


def story_layout(story):
    """Vertical geometry of one story panel, shared by render() and
    the tests: art height by panel size, then kicker / headline /
    subhead stacked with fixed gaps. Returns the art bottom, the text
    top and the y where the text block ends."""
    x0, y0, x1, y1 = story["panel"]
    height = y1 - y0
    if story["art"] == "eu":
        art_h = 280
    elif height <= 220:
        art_h = 100
    else:
        art_h = 230
    text_top = y0 + art_h + 12
    kicker_h = 7 * 2  # scale 2
    headline_lines = wrap_text(story["headline"], story["headline_scale"],
                               story["text_w"])
    headline_h = len(headline_lines) * (7 * story["headline_scale"] + 2)
    subhead_lines = wrap_text(story["subhead"], 2, story["text_w"])
    subhead_h = len(subhead_lines) * (7 * 2 + 2)
    # kicker, gap 6, headline, gap 6, subhead
    text_end = text_top + kicker_h + 6 + headline_h + 6 + subhead_h
    return {
        "art_h": art_h,
        "art_bottom_y": y0 + art_h,
        "text_top_y": text_top,
        "text_end_y": text_end,
    }


# ---------------------------------------------------------------- layout
def render():
    cv = Canvas(W, H, PAPER)
    # masthead
    draw_text_centered(cv, W // 2, 22, MASTHEAD_TITLE, 6, INK)
    draw_text_centered(cv, W // 2, 76, MASTHEAD_DATE, 3, RED)
    cv.fill_rect(16, 112, 1008, 116, RED)
    cv.fill_rect(16, 120, 1008, 122, INK)

    for story in STORIES:
        x0, y0, x1, y1 = story["panel"]
        # panel frame
        cv.fill_rect(x0, y0, x1, y1, WHITE)
        cv.fill_rect(x0, y0, x1, y0 + 2, INK)
        cv.fill_rect(x0, y1 - 2, x1, y1, INK)
        cv.fill_rect(x0, y0, x0 + 2, y1, INK)
        cv.fill_rect(x1 - 2, y0, x1, y1, INK)
        pad = 16
        layout = story_layout(story)
        art_h = layout["art_h"]
        text_y = layout["text_top_y"]
        ART[story["art"]](cv, x0 + 2, y0 + 2, x1 - 2, y0 + art_h)
        draw_text(cv, x0 + pad, text_y, story["kicker"], 2, RED)
        y = draw_text_block(cv, x0 + pad, text_y + 20,
                            story["headline"], story["headline_scale"],
                            story["text_w"], INK)
        draw_text_block(cv, x0 + pad, y + 6, story["subhead"], 2,
                        story["text_w"], SLATE)
    return cv


# ---------------------------------------------------------------- png
def encode_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        start = y * cv.w * 3
        raw += cv.buf[start:start + cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)

    def chunk(ctype, payload):
        return (struct.pack(">I", len(payload)) + ctype + payload +
                struct.pack(">I", zlib.crc32(ctype + payload) & 0xFFFFFFFF))

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return bytes(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(render())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
