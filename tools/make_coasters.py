#!/usr/bin/env python3
"""Generate laser-ready map coaster SVGs (xTool Creative Space / LightBurn).

Layers are separated by colour:
  black fill  (#000000) -> ENGRAVE  (roads, water, text, border)
  blue stroke (#0000ff) -> SCORE    (only in *_score.svg variants: road centrelines)
  red stroke  (#ff0000) -> CUT      (coaster outline)
All geometry is real vector outlines in millimetres; text is converted to paths.
"""
import gzip, json, math, os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from shapely.geometry import LineString, Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union, polygonize
from shapely import affinity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

# road class -> engraved line width in mm (at width_scale 1.0)
WIDTHS = {"motorway": 0.95, "trunk": 0.85, "primary": 0.8, "secondary": 0.62,
          "tertiary": 0.5, "residential": 0.32, "unclassified": 0.32,
          "living_street": 0.32, "motorway_link": 0.45, "trunk_link": 0.45,
          "primary_link": 0.4, "secondary_link": 0.35, "tertiary_link": 0.35}
WATERLINE = {"river": 0.6, "canal": 0.45, "stream": 0.25}
RAIL = 0.3


class MapData:
    def __init__(self, path, lat0, lon0):
        self.raw = json.load(gzip.open(path, "rt"))
        self.lat0, self.lon0 = lat0, lon0
        self.kx = 111320.0 * math.cos(math.radians(lat0))
        self.ky = 110574.0

    def xy(self, pts, mm_per_m, ox, oy):
        return [((lon - self.lon0) * self.kx * mm_per_m + ox,
                 -(lat - self.lat0) * self.ky * mm_per_m + oy) for lon, lat in pts]

    def build(self, mm_per_m, ox, oy, wscale, window):
        """Return (engrave polygon, list of (class, LineString) centrelines) in mm."""
        P = lambda pts: self.xy(pts, mm_per_m, ox, oy)
        shapes, lines = [], []
        for cls, pts in self.raw["roads"]:
            if cls not in WIDTHS:
                continue
            ln = LineString(P(pts))
            if ln.intersects(window):
                lines.append((cls, ln))
                shapes.append(ln.buffer(WIDTHS[cls] * wscale / 2, cap_style=1, join_style=1, resolution=4))
        for pts in self.raw["rails"]:
            ln = LineString(P(pts))
            if ln.intersects(window):
                lines.append(("rail", ln))
                shapes.append(ln.buffer(RAIL * wscale / 2, resolution=2))
        for cls, pts in self.raw["waterlines"]:
            ln = LineString(P(pts))
            if ln.intersects(window):
                shapes.append(ln.buffer(WATERLINE[cls] * wscale / 2, resolution=3))
        outer = unary_union([p.buffer(0) for p in polygonize(unary_union(
            [LineString(P(g)) for g in self.raw["water_outer"]]))])
        inner = unary_union([p.buffer(0) for p in polygonize(unary_union(
            [LineString(P(g)) for g in self.raw["water_inner"]]))])
        water = outer.difference(inner)
        shapes.append(water)
        return unary_union(shapes).intersection(window), lines


_font = TTFont(FONT)
_gs, _cmap, _upm = _font.getGlyphSet(), _font.getBestCmap(), _font["head"].unitsPerEm
_cap = _font["OS/2"].sCapHeight


def text_path(s, cx, baseline, cap_mm, tracking=0.0):
    """SVG path data for `s`, centred on cx, cap height cap_mm, tracking in em."""
    k = cap_mm / _cap
    adv = [(_gs[_cmap[ord(c)]].width + tracking * _upm) * k for c in s]
    total = sum(adv) - tracking * _upm * k
    x, d = cx - total / 2, []
    for c, a in zip(s, adv):
        pen = RecordingPen()
        _gs[_cmap[ord(c)]].draw(pen)
        for op, args in pen.value:
            pts = " ".join(f"{x + px * k:.3f},{baseline - py * k:.3f}" for px, py in args)
            d.append({"moveTo": "M", "lineTo": "L", "curveTo": "C", "qCurveTo": "Q",
                      "closePath": "Z", "endPath": "Z"}[op] + pts)
        x += a
    return "".join(d), total


def poly_d(geom):
    out = []
    polys = [geom] if isinstance(geom, Polygon) else [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]
    for p in polys:
        if p.area < 0.01:
            continue
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)
            out.append("M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in c[:-1]) + "Z")
    return "".join(out)


def line_d(geom):
    out = []
    geoms = [geom] if geom.geom_type == "LineString" else getattr(geom, "geoms", [])
    for g in geoms:
        if g.geom_type == "LineString" and g.length > 0.3:
            out.append("M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in g.coords))
    return "".join(out)


def rrect(x, y, w, h, r):
    return box(x + r, y, x + w - r, y + h).union(box(x, y + r, x + w, y + h - r)).union(
        unary_union([Point(px, py).buffer(r, resolution=16) for px, py in
                     [(x + r, y + r), (x + w - r, y + r), (x + r, y + h - r), (x + w - r, y + h - r)]]))


def write_svg(path, w, h, engrave_d, text_d, cut_svg, score_d=None):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">']
    if engrave_d:
        parts.append(f'<g id="engrave"><path fill="#000000" fill-rule="evenodd" stroke="none" d="{engrave_d}"/>'
                     f'<path fill="#000000" stroke="none" d="{text_d}"/></g>')
    else:
        parts.append(f'<g id="engrave"><path fill="#000000" stroke="none" d="{text_d}"/></g>')
    if score_d:
        parts.append(f'<g id="score"><path fill="none" stroke="#0000ff" stroke-width="0.1" d="{score_d}"/></g>')
    parts.append(f'<g id="cut" fill="none" stroke="#ff0000" stroke-width="0.1">{cut_svg}</g></svg>')
    with open(path, "w") as fh:
        fh.write("\n".join(parts))
    print(f"{os.path.relpath(path, ROOT):55s} {os.path.getsize(path) / 1024:7.0f} kB")


def emit(outdir, name, size, engrave, texts, cut_svg, lines, window, decor):
    """Write the engraved version and the faster score-line version."""
    text_d = "".join(texts)
    write_svg(f"{outdir}/{name}_engrave.svg", size, size, poly_d(engrave), text_d, cut_svg)
    sc = unary_union([ln for _, ln in lines]).intersection(window)
    write_svg(f"{outdir}/{name}_score.svg", size, size, poly_d(decor), text_d, cut_svg, line_d(sc))


def round_coaster(md, outdir, city, state, coords, mm_per_m=1 / 92.0, size=100.0):
    c, R = size / 2, size / 2
    ty = c + 27.0                                   # top of the text segment
    disc = Point(c, c).buffer(R - 4.2, resolution=64)
    window = disc.intersection(box(0, 0, size, ty - 0.9))
    engrave, lines = md.build(mm_per_m, c, c - 9.5, 1.0, window)
    ring = Point(c, c).buffer(R - 2.6, resolution=96).difference(Point(c, c).buffer(R - 3.2, resolution=96))
    rule = box(0, ty - 0.2, size, ty + 0.2).intersection(disc)
    decor = ring.union(rule)
    t1, _ = text_path(city, c, ty + 9.0, 5.2, 0.14)
    t2, _ = text_path(state, c, ty + 14.2, 2.3, 0.3)
    cut = f'<circle cx="{c}" cy="{c}" r="{R}"/>'
    emit(outdir, "round", size, engrave.union(decor), [t1, t2], cut, lines, window, decor)


def square_coaster(md, outdir, city, state, coords, mm_per_m=1 / 92.0, size=100.0):
    strip = 15.0
    frame = rrect(3, 3, size - 6, size - 6, 5.5).difference(rrect(3.55, 3.55, size - 7.1, size - 7.1, 4.95))
    inner = rrect(5, 5, size - 10, size - 10, 3.5)
    window = inner.intersection(box(0, 0, size, size - 5 - strip))
    engrave, lines = md.build(mm_per_m, size / 2, (size - strip) / 2, 1.0, window)
    rule = box(5, size - 5 - strip + 0.9, size - 5, size - 5 - strip + 1.3)
    decor = frame.union(rule)
    base = size - 5 - strip
    t1, _ = text_path(city, size / 2, base + 8.3, 4.8, 0.16)
    t2, _ = text_path(f"{state}  ·  {coords}", size / 2, base + 12.6, 1.9, 0.22)
    cut = f'<rect x="0" y="0" width="{size}" height="{size}" rx="8" ry="8"/>'
    emit(outdir, "square", size, engrave.union(decor), [t1, t2], cut, lines, window, decor)


def set_of_four(md, outdir, city, state, mm_per_m=1 / 46.0, size=100.0):
    """One big map split over a 2x2 set; push the coasters together to see the whole city."""
    names = {(0, 0): "NW", (1, 0): "NE", (0, 1): "SW", (1, 1): "SE"}
    for (i, j), tag in names.items():
        frame = rrect(3, 3, size - 6, size - 6, 5.5).difference(rrect(3.55, 3.55, size - 7.1, size - 7.1, 4.95))
        window = rrect(5, 5, size - 10, size - 10, 3.5)
        texts = []
        decor = frame
        if tag == "SE":                             # title block in the outer corner
            plate = rrect(size - 5 - 44, size - 5 - 13, 44, 13, 3.5).union(box(size - 12, size - 12, size - 5, size - 5)).intersection(window)
            window = window.difference(plate.buffer(0.9))
            px = size - 5 - 22
            texts.append(text_path(city, px, size - 5 - 5.6, 3.6, 0.14)[0])
            texts.append(text_path(state, px, size - 5 - 2.2, 1.6, 0.3)[0])
        engrave, lines = md.build(mm_per_m, size - i * size, size - j * size, 1.3, window)
        cut = f'<rect x="0" y="0" width="{size}" height="{size}" rx="8" ry="8"/>'
        emit(outdir, f"set4_{'%d' % (j * 2 + i + 1)}_{tag}", size, engrave.union(decor), texts, cut, lines, window, decor)


def sheet(outdir, name, files, cols, size=100.0, gap=4.0):
    """Lay several finished coaster files out on one sheet (keeps the layer colours)."""
    import re
    rows = -(-len(files) // cols)
    w, h = cols * size + (cols - 1) * gap, rows * size + (rows - 1) * gap
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">']
    for layer in ("engrave", "score", "cut"):       # group by operation so the cut runs last
        parts.append(f'<g id="{layer}">')
        for n, f in enumerate(files):
            body = open(f"{outdir}/{f}").read()
            m = re.search(rf'<g id="{layer}"([^>]*)>(.*?)</g>', body, re.S)
            if m:
                x, y = (n % cols) * (size + gap), (n // cols) * (size + gap)
                parts.append(f'<g transform="translate({x},{y})"{m.group(1)}>{m.group(2)}</g>')
        parts.append("</g>")
    parts.append("</svg>")
    path = f"{outdir}/{name}"
    open(path, "w").write("\n".join(parts))
    print(f"{os.path.relpath(path, ROOT):55s} {os.path.getsize(path) / 1024:7.0f} kB  ({w:.0f} x {h:.0f} mm)")


if __name__ == "__main__":
    out = os.path.join(ROOT, "coasters", "kearney")
    os.makedirs(out, exist_ok=True)
    md = MapData(os.path.join(ROOT, "data", "kearney_osm.json.gz"), lat0=40.7000, lon0=-99.0830)
    round_coaster(md, out, "KEARNEY", "NEBRASKA", "")
    square_coaster(md, out, "KEARNEY", "NEBRASKA", "40.70° N  99.08° W")
    set_of_four(md, out, "KEARNEY", "NEBRASKA")
    for kind in ("engrave", "score"):
        four = [f"set4_{n}_{t}_{kind}.svg" for n, t in ((1, "NW"), (2, "NE"), (3, "SW"), (4, "SE"))]
        sheet(out, f"sheet_set4_{kind}.svg", four, cols=2)                       # 204 x 204 mm, fits a 12 x 12 in sheet
        sheet(out, f"sheet_all6_{kind}.svg", four[:2] + [f"round_{kind}.svg"] + four[2:] + [f"square_{kind}.svg"], cols=3)  # 308 x 204 mm
