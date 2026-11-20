#!/usr/bin/env python3
"""Trace a logo PNG to vectors and build laser-ready logo coasters.

Usage: make_logo_coasters.py [logo.png] [output-name]
Layers: black fill = ENGRAVE, red stroke = CUT (same convention as make_coasters.py).
"""
import math, os, sys
import numpy as np
import potrace
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UP = 6  # upscale factor before thresholding, for smoother traced edges


def trace(png):
    """Return (list of closed curves in source-pixel units, width, height)."""
    im = Image.open(png).convert("RGBA")
    a = np.asarray(im, dtype=float)
    lum = a[..., :3].mean(axis=2)
    ink = (a[..., 3] / 255.0) * (1 - lum / 255.0)          # opaque and dark = ink
    big = Image.fromarray((ink * 255).astype("uint8")).resize((im.width * UP, im.height * UP), Image.BICUBIC)
    mask = np.asarray(big) > 255 * 0.28
    curves = []
    for c in potrace.Bitmap(~mask).trace(turdsize=UP * UP, alphamax=1.0, opttolerance=0.3):
        segs = [("M", [c.start_point])]
        for s in c.segments:
            segs.append(("L", [s.c, s.end_point]) if s.is_corner else ("C", [s.c1, s.c2, s.end_point]))
        curves.append(segs)
    return curves, im.width, im.height


def logo_d(curves, w, h, cx, cy, box_w, box_h):
    """Path data with the logo scaled to fit box_w x box_h mm, centred on (cx, cy)."""
    k = min(box_w / w, box_h / h) / UP
    ox, oy = cx - w * UP * k / 2, cy - h * UP * k / 2
    out = []
    for segs in curves:
        for op, pts in segs:
            if op == "L":
                out.append("L" + "L".join(f"{ox + p.x * k:.3f},{oy + p.y * k:.3f}" for p in pts))
            else:
                out.append(op + " ".join(f"{ox + p.x * k:.3f},{oy + p.y * k:.3f}" for p in pts))
        out.append("Z")
    return "".join(out)


def circle_d(cx, cy, r):
    return f"M{cx - r},{cy}A{r},{r} 0 1,0 {cx + r},{cy}A{r},{r} 0 1,0 {cx - r},{cy}Z"


def rrect_d(x, y, w, h, r):
    return (f"M{x + r},{y}H{x + w - r}A{r},{r} 0 0,1 {x + w},{y + r}V{y + h - r}A{r},{r} 0 0,1 {x + w - r},{y + h}"
            f"H{x + r}A{r},{r} 0 0,1 {x},{y + h - r}V{y + r}A{r},{r} 0 0,1 {x + r},{y}Z")


def write(path, size, engrave_d, cut):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}mm" height="{size}mm" viewBox="0 0 {size} {size}">\n'
           f'<g id="engrave"><path fill="#000000" fill-rule="evenodd" stroke="none" d="{engrave_d}"/></g>\n'
           f'<g id="cut" fill="none" stroke="#ff0000" stroke-width="0.1">{cut}</g></svg>')
    open(path, "w").write(svg)
    print(f"{os.path.relpath(path, ROOT):50s} {os.path.getsize(path) / 1024:6.0f} kB")


def main(png, name, size=100.0):
    out = os.path.join(ROOT, "coasters", name)
    os.makedirs(out, exist_ok=True)
    curves, w, h = trace(png)
    c = size / 2
    cut_round = f'<circle cx="{c}" cy="{c}" r="{c}"/>'
    cut_square = f'<rect x="0" y="0" width="{size}" height="{size}" rx="8" ry="8"/>'
    ring = circle_d(c, c, c - 2.6) + circle_d(c, c, c - 3.3)
    frame = rrect_d(3, 3, size - 6, size - 6, 5.5) + rrect_d(3.7, 3.7, size - 7.4, size - 7.4, 4.8)
    # the largest box of the logo's proportions that fits inside a circle of radius r
    r = c - 7.5
    ang = math.atan2(h, w)
    fit_w, fit_h = 2 * r * math.cos(ang), 2 * r * math.sin(ang)

    # logo engraved (dark logo on light wood)
    write(f"{out}/round_engrave.svg", size, ring + logo_d(curves, w, h, c, c, fit_w, fit_h), cut_round)
    write(f"{out}/square_engrave.svg", size, frame + logo_d(curves, w, h, c, c, size - 18, size - 18), cut_square)
    # background engraved, logo left as bare wood (even-odd fill knocks the logo out of the disc)
    r2 = c - 5.5
    a2 = math.atan2(h, w)
    write(f"{out}/round_inverted.svg", size,
          ring + circle_d(c, c, c - 4.3) + logo_d(curves, w, h, c, c, 2 * (r2 - 3) * math.cos(a2), 2 * (r2 - 3) * math.sin(a2)),
          cut_round)
    write(f"{out}/square_inverted.svg", size,
          frame + rrect_d(4.8, 4.8, size - 9.6, size - 9.6, 3.7) + logo_d(curves, w, h, c, c, size - 22, size - 22),
          cut_square)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "lopers_logo.png"),
         sys.argv[2] if len(sys.argv) > 2 else "lopers")
