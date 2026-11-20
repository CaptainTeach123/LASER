#!/usr/bin/env python3
"""Miami Dolphins logo + stylised Miami skyline coasters.

The logo's three colours become three separate engrave layers so each can be given
its own power in xTool Studio (darker navy, mid orange, light aqua):
  #005778 navy, #fc4c02 orange, #008e97 aqua  -> ENGRAVE (three tones)
  #000000 black                               -> ENGRAVE (skyline, text, border)
  #ff0000 red line                            -> CUT
"""
import math, os, sys
import numpy as np
import potrace
from PIL import Image
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_coasters import text_path, poly_d, rrect
from make_logo_coasters import circle_d, rrect_d

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLOURS = {"navy": (0, 87, 120), "orange": (252, 76, 2), "aqua": (0, 142, 151)}
UP = 3


def trace_colours(png):
    """Split the logo into one traced layer per colour. Returns ({name: curves}, bbox in upscaled px)."""
    im = Image.open(png).convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    big = np.asarray(flat.convert("RGB").resize((im.width * UP, im.height * UP), Image.LANCZOS), dtype=float)
    names = list(COLOURS) + ["white"]
    pal = np.array([*COLOURS.values(), (255, 255, 255)], dtype=float)
    nearest = ((big[:, :, None, :] - pal[None, None]) ** 2).sum(axis=3).argmin(axis=2)
    ys, xs = np.where(nearest != len(pal) - 1)
    layers = {}
    for i, name in enumerate(names[:-1]):
        curves = []
        for c in potrace.Bitmap(~(nearest == i)).trace(turdsize=UP * UP * 6, alphamax=1.0, opttolerance=0.3):
            segs = [("M", [c.start_point])]
            for s in c.segments:
                segs.append(("L", [s.c, s.end_point]) if s.is_corner else ("C", [s.c1, s.c2, s.end_point]))
            curves.append(segs)
        layers[name] = curves
    return layers, (xs.min(), ys.min(), xs.max(), ys.max())


def place(curves, bbox, cx, cy, width_mm):
    x0, y0, x1, y1 = bbox
    k = width_mm / (x1 - x0)
    ox, oy = cx - (x0 + x1) / 2 * k, cy - (y0 + y1) / 2 * k
    f = lambda p: f"{ox + p.x * k:.3f},{oy + p.y * k:.3f}"
    out = []
    for segs in curves:
        for op, pts in segs:
            out.append("L" + "L".join(map(f, pts)) if op == "L" else op + " ".join(map(f, pts)))
        out.append("Z")
    return "".join(out), (y1 - y0) * k


# (width, height, roof style) left to right, loosely after the downtown / Brickell waterfront
BUILDINGS = [(5, 6, "flat"), (4, 11, "flat"), (5, 15, "cupola"), (6, 9, "flat"), (5, 19, "slant"),
             (8, 25, "tiers"), (5, 17, "antenna"), (6, 30, "notch"), (6, 23, "saw"), (5, 27, "spire"),
             (5, 15, "flat"), (5, 21, "round"), (4, 12, "slant"), (6, 8, "flat"), (5, 5, "flat")]


def skyline(cx, base_y, width_mm, height_mm, gap=0.45):
    """Stylised Miami skyline silhouette (not a to-scale drawing) plus palms, as a shapely geometry in mm."""
    total = sum(b[0] for b in BUILDINGS)
    kx, ky = width_mm / total, height_mm / 30.0
    shapes, x = [], cx - width_mm / 2
    for w, h, style in BUILDINGS:
        w, h = w * kx, h * ky
        l, r, t = x + gap / 2, x + w - gap / 2, base_y - h
        m = (l + r) / 2
        b = box(l, t, r, base_y)
        if style == "slant":
            b = Polygon([(l, base_y), (l, t + 0.14 * h), (r, t), (r, base_y)])
        elif style == "tiers":           # three stepped tiers
            b = unary_union([box(l, t + 0.24 * h, r, base_y), box(l, t + 0.12 * h, l + (r - l) * 0.68, base_y),
                             box(l, t, l + (r - l) * 0.36, base_y)])
        elif style == "antenna":
            b = b.union(box(m - 0.18, t - 0.22 * h, m + 0.18, t))
        elif style == "notch":
            b = b.difference(box(m - (r - l) * 0.12, t - 1, m + (r - l) * 0.12, t + 0.05 * h)).union(
                box(l + 0.5, t - 0.05 * h, l + 0.9, t))
        elif style == "saw":             # sawtooth setbacks down one side
            n = 5
            b = unary_union([box(l, t + i * 0.035 * h, l + (r - l) * (0.5 + 0.5 * (i + 1) / n), base_y) for i in range(n)])
        elif style == "spire":
            b = unary_union([b, box(m - (r - l) * 0.28, t - 0.07 * h, m + (r - l) * 0.28, t),
                             Polygon([(m - 0.3, t - 0.07 * h), (m, t - 0.3 * h), (m + 0.3, t - 0.07 * h)])])
        elif style == "round":
            b = box(l, t + (r - l) / 2, r, base_y).union(Point(m, t + (r - l) / 2).buffer((r - l) / 2, resolution=12))
        elif style == "cupola":          # tiered tower with a pointed cap
            b = unary_union([box(l, t + 0.42 * h, r, base_y), box(m - (r - l) * 0.3, t + 0.2 * h, m + (r - l) * 0.3, base_y),
                             box(m - (r - l) * 0.19, t + 0.08 * h, m + (r - l) * 0.19, base_y),
                             Polygon([(m - (r - l) * 0.19, t + 0.08 * h), (m, t - 0.1 * h), (m + (r - l) * 0.19, t + 0.08 * h)])])
        shapes.append(b)
        x += w
    for px, lean, s in [(cx - width_mm * 0.39, -1, 1.0), (cx - width_mm * 0.31, 1, 0.8), (cx + width_mm * 0.36, 1, 0.95)]:
        shapes.append(palm(px, base_y, height_mm * 0.42 * s, lean))
    shapes.append(box(cx - width_mm / 2 - 2, base_y - 0.01, cx + width_mm / 2 + 2, base_y + 0.55))
    return unary_union(shapes)


def palm(x, base_y, h, lean):
    top = (x + lean * h * 0.22, base_y - h)
    trunk = LineString([(x, base_y), (x + lean * h * 0.05, base_y - h * 0.5), top]).buffer(h * 0.035, resolution=3)
    fronds = []
    for ang in (-160, -125, -90, -55, -20, 15, 195):
        L = h * 0.42
        pts = []
        for i in range(9):
            t = i / 8
            pts.append((top[0] + math.cos(math.radians(ang)) * L * t,
                        top[1] + math.sin(math.radians(ang)) * L * t + L * 0.55 * t * t))
        fronds.append(unary_union([LineString(pts[i:i + 2]).buffer(h * 0.05 * (1 - i / 9) + 0.12, resolution=2)
                                   for i in range(8)]))
    return unary_union([trunk, *fronds])


def write(path, size, layers, black_d, text_d, cut):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}mm" height="{size}mm" viewBox="0 0 {size} {size}">']
    for name, d in layers.items():
        parts.append(f'<g id="engrave-{name}"><path fill="#{"%02x%02x%02x" % COLOURS[name]}" fill-rule="evenodd" stroke="none" d="{d}"/></g>')
    parts.append(f'<g id="engrave"><path fill="#000000" fill-rule="evenodd" stroke="none" d="{black_d}"/>'
                 f'<path fill="#000000" stroke="none" d="{text_d}"/></g>')
    parts.append(f'<g id="cut" fill="none" stroke="#ff0000" stroke-width="0.1">{cut}</g></svg>')
    open(path, "w").write("\n".join(parts))
    print(f"{os.path.relpath(path, ROOT):50s} {os.path.getsize(path) / 1024:6.0f} kB")


def main(size=100.0):
    out = os.path.join(ROOT, "coasters", "dolphins")
    os.makedirs(out, exist_ok=True)
    traced, bbox = trace_colours(os.path.join(ROOT, "assets", "dolphins_logo.png"))
    c = size / 2

    # round
    disc = Point(c, c).buffer(c - 4.3, resolution=96)
    sky = skyline(c, c + 31.5, 70, 17).intersection(disc)
    layers = {n: place(cv, bbox, c, c - 12.5, 67)[0] for n, cv in traced.items()}
    ring = circle_d(c, c, c - 2.6) + circle_d(c, c, c - 3.3)
    write(f"{out}/round_skyline.svg", size, layers, ring + poly_d(sky),
          text_path("MIAMI", c, c + 39.6, 3.6, 0.5)[0], f'<circle cx="{c}" cy="{c}" r="{c}"/>')

    # square
    inner = rrect(5, 5, size - 10, size - 10, 3.5)
    sky = skyline(c, size - 16.5, 88, 21).intersection(inner)
    layers = {n: place(cv, bbox, c, c - 15.5, 74)[0] for n, cv in traced.items()}
    frame = rrect_d(3, 3, size - 6, size - 6, 5.5) + rrect_d(3.7, 3.7, size - 7.4, size - 7.4, 4.8)
    write(f"{out}/square_skyline.svg", size, layers, frame + poly_d(sky),
          text_path("MIAMI", c, size - 8.4, 4.0, 0.9)[0], f'<rect x="0" y="0" width="{size}" height="{size}" rx="8" ry="8"/>')


if __name__ == "__main__":
    main()
