#!/usr/bin/env python3
"""Baylor BU mark over a street map of downtown Waco, Texas.

Layers: black fill = ENGRAVE (map, logo, text, border), red line = CUT.
"""
import os, sys
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_coasters import MapData, text_path, poly_d, rrect, write_svg, ROOT
from make_logo_coasters import trace, UP


def logo_shape(curves, w, h, cx, cy, height_mm):
    """Traced logo as a shapely geometry in mm (curves flattened, even-odd fill)."""
    k = height_mm / (h * UP)
    ox, oy = cx - w * UP * k / 2, cy - h * UP * k / 2
    shape = Polygon()
    for segs in curves:
        pts, cur = [], None
        for op, p in segs:
            if op == "C":
                for i in range(1, 9):
                    t = i / 8
                    a, b, c_, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
                    pts.append((a * cur.x + b * p[0].x + c_ * p[1].x + d * p[2].x,
                                a * cur.y + b * p[0].y + c_ * p[1].y + d * p[2].y))
            else:
                pts += [(q.x, q.y) for q in p]
            cur = p[-1]
        if len(pts) >= 3:
            shape = shape.symmetric_difference(Polygon([(ox + x * k, oy + y * k) for x, y in pts]).buffer(0))
    return shape


def halo(logo, margin=2.0):
    """Clear zone around the logo, including the insides of its letters."""
    b = logo.buffer(margin)
    return unary_union([Polygon(g.exterior) for g in getattr(b, "geoms", [b])])


def main(size=100.0, mm_per_m=1 / 42.0):
    out = os.path.join(ROOT, "coasters", "baylor")
    md = MapData(os.path.join(ROOT, "data", "waco_osm.json.gz"), lat0=31.5545, lon0=-97.1275)
    curves, w, h = trace(os.path.join(ROOT, "assets", "baylor_logo.png"))
    c = size / 2

    # round: map fills the disc above a caption segment, BU in the middle with a clear halo
    ty = c + 30.0
    disc = Point(c, c).buffer(c - 4.2, resolution=64)
    window = disc.intersection(box(0, 0, size, ty - 0.9))
    logo = logo_shape(curves, w, h, c, c - 8.5, 40)
    engrave, _ = md.build(mm_per_m, c, c - 8.5, 1.15, window.difference(halo(logo)))
    ring = Point(c, c).buffer(c - 2.6, resolution=96).difference(Point(c, c).buffer(c - 3.2, resolution=96))
    rule = box(0, ty - 0.2, size, ty + 0.2).intersection(disc)
    texts = text_path("BAYLOR BEARS", c, ty + 6.6, 3.5, 0.2)[0] + text_path("WACO, TEXAS", c, ty + 11.4, 2.0, 0.3)[0]
    write_svg(f"{out}/round_waco_map.svg", size, size, poly_d(unary_union([engrave, logo, ring, rule])), texts,
              f'<circle cx="{c}" cy="{c}" r="{c}"/>')

    # square
    strip = 15.0
    inner = rrect(5, 5, size - 10, size - 10, 3.5)
    window = inner.intersection(box(0, 0, size, size - 5 - strip))
    cy = (size - strip) / 2
    logo = logo_shape(curves, w, h, c, cy, 42)
    engrave, _ = md.build(mm_per_m, c, cy, 1.15, window.difference(halo(logo)))
    frame = rrect(3, 3, size - 6, size - 6, 5.5).difference(rrect(3.55, 3.55, size - 7.1, size - 7.1, 4.95))
    base = size - 5 - strip
    rule = box(5, base + 0.9, size - 5, base + 1.3)
    texts = text_path("BAYLOR BEARS", c, base + 8.3, 4.4, 0.2)[0] + text_path("WACO, TEXAS", c, base + 12.6, 1.9, 0.3)[0]
    write_svg(f"{out}/square_waco_map.svg", size, size, poly_d(unary_union([engrave, logo, frame, rule])), texts,
              f'<rect x="0" y="0" width="{size}" height="{size}" rx="8" ry="8"/>')


if __name__ == "__main__":
    main()
