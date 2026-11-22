#!/usr/bin/env python3
"""Concept render for a modular gingerbread-house kit (no cut files yet).

Every wall / roof / trim piece is drawn as flat 2D artwork in millimetres and then
placed in 3D with an affine (orthographic) projection, so the render is built from
the same kind of flat panels the laser would cut.
"""
import math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WOOD, ENG, CREAM, JOINT, DOOR = "#e4c28e", "#6b3f1c", "#fbf2de", "#b98a52", "#cf9f63"
TH, PH = math.radians(34), math.radians(20)
cT, sT, cP, sP = math.cos(TH), math.sin(TH), math.cos(PH), math.sin(PH)
CAM = (sT * cP, -cT * cP, sP)
_l = (-0.35, -0.75, 0.55)
LIGHT = tuple(c / math.sqrt(sum(v * v for v in _l)) for c in _l)
_uid = [0]


def P(p):
    x, y, z = p
    return (x * cT + y * sT, -z * cP - (-x * sT + y * cT) * sP)


def depth(p):
    x, y, z = p
    return (-x * sT + y * cT) * cP - z * sP


def dot(a, b):
    return sum(i * j for i, j in zip(a, b))


def shade(n):
    return round(0.5 * (1 - max(0.0, dot(n, LIGHT))), 3)


# ---------------------------------------------------------------- flat artwork (local mm)
def round_win(cx, cy, r):
    dots = "".join(f'<circle cx="{cx + (r + 3.6) * math.cos(a):.2f}" cy="{cy + (r + 3.6) * math.sin(a):.2f}" r="0.8" fill="{ENG}"/>'
                   for a in [i * math.tau / 18 for i in range(18)])
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#glow)" stroke="{ENG}" stroke-width="0.7"/>'
            f'<path d="M{cx - r},{cy}H{cx + r}M{cx},{cy - r}V{cy + r}" stroke="{WOOD}" stroke-width="2"/>{dots}')


def sq_win(cx, cy, w, h=None, panes=2):
    h = h or w
    bars = "".join(f"M{cx - w / 2 + w * i / panes},{cy - h / 2}v{h}" for i in range(1, panes))
    return (f'<rect x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" rx="2" fill="url(#glow)" stroke="{ENG}" stroke-width="0.7"/>'
            f'<path d="{bars}M{cx - w / 2},{cy}h{w}" stroke="{WOOD}" stroke-width="2"/>')


def arch_win(cx, cy, w, h):
    return (f'<path d="M{cx - w / 2},{cy + h / 2}V{cy - h / 2 + w / 2}a{w / 2},{w / 2} 0 0,1 {w},0V{cy + h / 2}Z" fill="url(#glow)" stroke="{ENG}" stroke-width="0.7"/>'
            f'<path d="M{cx},{cy - h / 2}V{cy + h / 2}M{cx - w / 2},{cy}h{w}" stroke="{WOOD}" stroke-width="2"/>')


def heart(cx, cy, s, fill="url(#glow)"):
    return (f'<path d="M{cx},{cy + s * 0.55}C{cx - s * 1.1},{cy - s * 0.25} {cx - s * 0.45},{cy - s * 0.85} {cx},{cy - s * 0.3}'
            f'C{cx + s * 0.45},{cy - s * 0.85} {cx + s * 1.1},{cy - s * 0.25} {cx},{cy + s * 0.55}Z" fill="{fill}" stroke="{ENG}" stroke-width="0.7"/>')


def door(cx, bottom, w, h):
    planks = "".join(f"M{cx - w / 2 + w * i / 4},{bottom - h + w * 0.42}V{bottom}" for i in (1, 2, 3))
    return (f'<path d="M{cx - w / 2},{bottom}V{bottom - h + w / 2}a{w / 2},{w / 2} 0 0,1 {w},0V{bottom}Z" fill="{DOOR}" stroke="{ENG}" stroke-width="0.9"/>'
            f'<path d="{planks}" stroke="{ENG}" stroke-width="0.4" fill="none"/>'
            f'<circle cx="{cx + w * 0.3}" cy="{bottom - h * 0.42}" r="1.3" fill="{ENG}"/>' + heart(cx, bottom - h * 0.68, 3.2, CREAM))


def outlined(d, width, cap="round"):
    return (f'<path d="{d}" fill="none" stroke="{ENG}" stroke-width="{width + 1.1}" stroke-linecap="{cap}" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{CREAM}" stroke-width="{width}" stroke-linecap="{cap}" stroke-linejoin="round"/>')


def snowflake(cx, cy, r):
    d = ""
    for i in range(6):
        a = i * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        d += f"M{cx:.2f},{cy:.2f}L{cx + r * ca:.2f},{cy + r * sa:.2f}"
        for f, l in ((0.5, 0.3), (0.75, 0.22)):
            bx, by = cx + r * f * ca, cy + r * f * sa
            for s in (-1, 1):
                b = a + s * math.pi / 3.2
                d += f"M{bx:.2f},{by:.2f}L{bx + r * l * math.cos(b):.2f},{by + r * l * math.sin(b):.2f}"
    return outlined(d, 1.7)


def tree_d(cx, base, h, w=None):
    w = w or h * 0.62
    t, trunk = h * 0.86, h * 0.14
    top = base - h
    pts = [(cx, top)]
    for i, (f, y) in enumerate(((0.45, 0.36), (0.72, 0.68), (1.0, 1.0))):
        pts += [(cx + w / 2 * f, top + t * y), (cx + w / 2 * f * 0.45, top + t * y)]
    pts = pts[:-1] + [(cx + w * 0.07, top + t), (cx + w * 0.07, base), (cx - w * 0.07, base), (cx - w * 0.07, top + t)]
    left = [(2 * cx - x, y) for x, y in reversed(pts[1:-4])]
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in pts + left) + "Z"


def tree(cx, base, h):
    return f'<path d="{tree_d(cx, base, h)}" fill="{CREAM}" stroke="{ENG}" stroke-width="0.7" stroke-linejoin="round"/>'


def cane(x, base, h, flip=1):
    r = 4.5
    d = f"M{x},{base}V{base - h + r}a{r},{r} 0 0,{1 if flip > 0 else 0} {2 * r * flip},0v3"
    return outlined(d, 3.6) + f'<path d="{d}" fill="none" stroke="{ENG}" stroke-width="3.6" stroke-dasharray="1.6 3.6" opacity="0.75"/>'


def wreath(cx, cy, r):
    d = f"M{cx - r},{cy}a{r},{r} 0 1,0 {2 * r},0a{r},{r} 0 1,0 {-2 * r},0"
    berries = "".join(f'<circle cx="{cx + r * math.cos(a):.2f}" cy="{cy + r * math.sin(a):.2f}" r="0.9" fill="{ENG}"/>' for a in (0.4, 1.7, 2.9, 4.2, 5.4))
    return outlined(d, 3.2) + berries + f'<path d="M{cx},{cy + r}l-3.5,4.5h7z" fill="{CREAM}" stroke="{ENG}" stroke-width="0.6"/>'


def star(cx, cy, r):
    pts = [(cx + (r if i % 2 == 0 else r * 0.45) * math.sin(i * math.pi / 5), cy - (r if i % 2 == 0 else r * 0.45) * math.cos(i * math.pi / 5)) for i in range(10)]
    return f'<path d="M{"L".join(f"{x:.2f},{y:.2f}" for x, y in pts)}Z" fill="{CREAM}" stroke="{ENG}" stroke-width="0.7" stroke-linejoin="round"/>'


def clock(cx, cy, r):
    ticks = "".join(f"M{cx + r * 0.78 * math.sin(a):.2f},{cy - r * 0.78 * math.cos(a):.2f}L{cx + r * 0.92 * math.sin(a):.2f},{cy - r * 0.92 * math.cos(a):.2f}"
                    for a in [i * math.pi / 6 for i in range(12)])
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{CREAM}" stroke="{ENG}" stroke-width="1"/>'
            f'<path d="{ticks}M{cx},{cy}v{-r * 0.62}M{cx},{cy}l{r * 0.38},{r * 0.2}" stroke="{ENG}" stroke-width="0.9" stroke-linecap="round" fill="none"/>')


def plaque(cx, cy, text, w=None):
    w = w or len(text) * 5.4 + 8
    return (f'<rect x="{cx - w / 2}" y="{cy - 5}" width="{w}" height="10" rx="3" fill="{CREAM}" stroke="{ENG}" stroke-width="0.7"/>'
            f'<text x="{cx}" y="{cy + 2.6}" font-family="Inter,sans-serif" font-weight="800" font-size="7" letter-spacing="0.8" text-anchor="middle" fill="{ENG}">{text}</text>')


def joints(xs, top, bottom):
    out, y = "", top + 5
    while y + 8 < bottom:
        out += "".join(f'<rect x="{x}" y="{y}" width="3" height="8" fill="{JOINT}"/>' for x in xs)
        y += 16
    return out


def gable_art(w, h, rise, decor=""):
    return f"M0,{rise}L{w / 2},0L{w},{rise}V{rise + h}H0Z", joints((0, w - 3), rise, rise + h) + decor


def rect_art(w, h, decor=""):
    return f"M0,0H{w}V{h}H0Z", joints((0, w - 3), 0, h) + decor


def roof_art(L, S):
    n = max(1, round(L / 9)); sw = L / n
    outline = f"M0,0H{L}V{S}" + f"a{sw / 2},{sw / 2} 0 0,1 {-sw},0" * n + "Z"
    _uid[0] += 1
    rows, y, k = "", 9.0, 0
    while y < S - 2:
        rows += f"M{-sw / 2 * (k % 2)},{y}" + f"a{sw / 2},{sw * 0.42} 0 0,0 {sw},0" * (n + 1)
        y += 9; k += 1
    inner = (f'<clipPath id="c{_uid[0]}"><rect width="{L}" height="{S + 5}"/></clipPath>'
             f'<path d="{rows}" clip-path="url(#c{_uid[0]})" fill="none" stroke="{ENG}" stroke-width="0.6"/>')
    return outline, inner


def barge_d(W, pitch, t=8.5):
    """Icicle bargeboard: chevron band following the roof line with drips along its lower edge."""
    tan = math.tan(pitch); Hb = W / 2 * tan
    yl = lambda x: abs(x - W / 2) * tan + t
    d = f"M0,{Hb}L{W / 2},0L{W},{Hb}L{W},{yl(W)}"
    n = max(4, round(W / 2 / 8.5)); s = W / 2 / n
    lens = (7, 12, 5, 10, 6, 13)
    for half in (1, -1):
        for i in range(n):
            xa = W - i * s if half == 1 else W / 2 - i * s
            xb = xa - s; xm = (xa + xb) / 2; ym = yl(xm); ln = lens[(i + (0 if half == 1 else 2)) % 6]
            d += f"Q{xm + s * 0.12:.2f},{ym + ln * 0.25:.2f} {xm:.2f},{ym + ln:.2f}Q{xm - s * 0.12:.2f},{ym + ln * 0.25:.2f} {xb:.2f},{yl(xb):.2f}"
    return d + "Z"


def man_art(h):
    k = h / 46
    shapes = (f'<circle cx="{14 * k}" cy="{8 * k}" r="{7.5 * k}"/><rect x="{7.5 * k}" y="{13 * k}" width="{13 * k}" height="{18 * k}" rx="{5 * k}"/>'
              f'<path d="M{9 * k},{17 * k}L{1.5 * k},{22 * k}M{19 * k},{17 * k}L{26.5 * k},{22 * k}M{11 * k},{29 * k}L{9 * k},{42 * k}M{17 * k},{29 * k}L{19 * k},{42 * k}" stroke-linecap="round" fill="none" stroke-width="{6 * k}"')
    out = (f'<g fill="{ENG}" stroke="{ENG}" stroke-width="{1.4 * k}">{shapes.replace("stroke-width=", "data-w=").replace("data-w=", "stroke-width=", 0)} stroke="{ENG}" style="stroke-width:{7.4 * k}"/></g>'
           f'<g fill="{DOOR}" stroke="{DOOR}" stroke-width="0">{shapes} stroke="{DOOR}"/></g>')
    out += (f'<circle cx="{11.5 * k}" cy="{7 * k}" r="{0.9 * k}" fill="{ENG}"/><circle cx="{16.5 * k}" cy="{7 * k}" r="{0.9 * k}" fill="{ENG}"/>'
            f'<path d="M{11 * k},{10 * k}q{3 * k},{2.6 * k} {6 * k},0" stroke="{CREAM}" stroke-width="{0.9 * k}" fill="none"/>'
            f'<circle cx="{14 * k}" cy="{18 * k}" r="{1.1 * k}" fill="{CREAM}"/><circle cx="{14 * k}" cy="{23 * k}" r="{1.1 * k}" fill="{CREAM}"/>')
    return out


# ---------------------------------------------------------------- 3D scene
class Scene:
    def __init__(self):
        self.groups, self.pts = [], []

    def panel(self, O, u, v, w, h, art, n, fill=WOOD):
        outline, inner = art
        for p in (O, [O[i] + u[i] * w for i in range(3)], [O[i] + v[i] * h for i in range(3)], [O[i] + u[i] * w + v[i] * h for i in range(3)]):
            self.pts.append(P(p))
        (a, b), (c, d), (e, f) = P(u), P(v), P(O)
        return (f'<g transform="matrix({a:.4f} {b:.4f} {c:.4f} {d:.4f} {e:.3f} {f:.3f})">'
                f'<path d="{outline}" fill="{fill}" stroke="{ENG}" stroke-width="0.6" stroke-linejoin="round"/>{inner}'
                f'<path d="{outline}" fill="#2a1403" opacity="{shade(n)}"/></g>')

    def poly(self, pts, n, fill=WOOD):
        q = [P(p) for p in pts]; self.pts += q
        d = "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in q) + "Z"
        return (f'<path d="{d}" fill="{fill}" stroke="{ENG}" stroke-width="0.6" stroke-linejoin="round"/>'
                f'<path d="{d}" fill="#2a1403" opacity="{shade(n)}"/>')

    def add(self, centre, parts, bias=0.0):
        self.groups.append((depth(centre) - bias, "".join(parts)))

    def svg(self):
        return "".join(g for _, g in sorted(self.groups, key=lambda t: -t[0]))

    def bbox(self):
        xs, ys = [p[0] for p in self.pts], [p[1] for p in self.pts]
        return min(xs), min(ys), max(xs), max(ys)


def house(sc, x0, y0, z0, w, d, h, ridge="y", pitch=45, front="", side="", ov=9, ove=10, ov_left=None, chimney=None, trim=True):
    """One box module. ridge 'y' = gable faces front, 'x' = gable faces right, None = flat top (to stack on)."""
    parts, p = [], math.radians(pitch)
    span = w if ridge == "y" else d
    rise = span / 2 * math.tan(p) if ridge else 0
    ztop = z0 + h + rise
    # right wall, then front wall
    if ridge == "x":
        parts.append(sc.panel((x0 + w, y0, ztop), (0, 1, 0), (0, 0, -1), d, h + rise, gable_art(d, h, rise, side), (1, 0, 0)))
        parts.append(sc.panel((x0, y0, z0 + h), (1, 0, 0), (0, 0, -1), w, h, rect_art(w, h, front), (0, -1, 0)))
    else:
        parts.append(sc.panel((x0 + w, y0, z0 + h), (0, 1, 0), (0, 0, -1), d, h, rect_art(d, h, side), (1, 0, 0)))
        art = gable_art(w, h, rise, front) if ridge else rect_art(w, h, front)
        parts.append(sc.panel((x0, y0, ztop), (1, 0, 0), (0, 0, -1), w, h + rise, art, (0, -1, 0)))
    if ridge is None:
        parts.append(sc.poly([(x0, y0, ztop), (x0 + w, y0, ztop), (x0 + w, y0 + d, ztop), (x0, y0 + d, ztop)], (0, 0, 1)))
    cp, sp_ = math.cos(p), math.sin(p)
    if ridge == "y":
        S, L = (w / 2 + ove) / cp, d + 2 * ov
        for sgn in (-1, 1):
            n = (sgn * sp_, 0, cp)
            if dot(n, CAM) > 0.02:
                parts.append(sc.panel((x0 + w / 2, y0 - ov, ztop), (0, 1, 0), (sgn * cp, 0, -sp_), L, S, roof_art(L, S), n))
        zr = lambda x, y: ztop - abs(x - (x0 + w / 2)) * math.tan(p)
        if trim:
            W = w + 2 * ove
            parts.append(sc.panel((x0 - ove, y0 - ov - 0.6, ztop), (1, 0, 0), (0, 0, -1), W, W / 2 * math.tan(p) + 20,
                                  (barge_d(W, p), ""), (0, -1, 0), CREAM))
    elif ridge == "x":
        ol = ov if ov_left is None else ov_left
        S, L = (d / 2 + ove) / cp, w + ov + ol
        parts.append(sc.panel((x0 - ol, y0 + d / 2, ztop), (1, 0, 0), (0, -cp, -sp_), L, S, roof_art(L, S), (0, -sp_, cp)))
        zr = lambda x, y: ztop - abs(y - (y0 + d / 2)) * math.tan(p)
        if trim:
            W = d + 2 * ove
            parts.append(sc.panel((x0 + w + ov + 0.6, y0 - ove, ztop), (0, 1, 0), (0, 0, -1), W, W / 2 * math.tan(p) + 20,
                                  (barge_d(W, p), ""), (1, 0, 0), CREAM))
    if chimney:
        cx0, cy0, cw, cd, ch = chimney
        cx1, cy1 = cx0 + cw, cy0 + cd
        zt = max(zr(cx0, cy0), zr(cx1, cy1), zr(cx0, cy1)) + ch
        parts.append(sc.poly([(cx1, cy0, zr(cx1, cy0)), (cx1, cy0, zt), (cx1, cy1, zt), (cx1, cy1, zr(cx1, cy1))], (1, 0, 0)))
        parts.append(sc.poly([(cx0, cy0, zr(cx0, cy0)), (cx0, cy0, zt), (cx1, cy0, zt), (cx1, cy0, zr(cx1, cy0))], (0, -1, 0)))
        e = 2.5
        parts.append(sc.poly([(cx0 - e, cy0 - e, zt), (cx1 + e, cy0 - e, zt), (cx1 + e, cy1 + e, zt), (cx0 - e, cy1 + e, zt)], (0, 0, 1), CREAM))
    sc.add((x0 + w / 2, y0 + d / 2, z0 + h / 2), parts)


def plate(sc, x0, y0, w, d, tab=False, socket=False):
    r = 8
    o = f"M{r},0H{w - r}Q{w},0 {w},{r}"
    if tab:
        o += f"V{d / 2 - 7}h5c-4,-9 14,-9 10,0c4,5 4,9 0,14c4,9 -14,9 -10,0h-5"
    o += f"V{d - r}Q{w},{d} {w - r},{d}H{r}Q0,{d} 0,{d - r}"
    o += f"V{r}Q0,0 {r},0Z"
    sc.groups.append((1e9 - x0, sc.panel((x0, y0, 0), (1, 0, 0), (0, 1, 0), w, d, (o, ""), (0, 0, 1), "#f3e3c3")
                      + sc.poly([(x0 + r, y0, 0), (x0 + w - r, y0, 0), (x0 + w - r, y0, -3), (x0 + r, y0, -3)], (0, -1, 0), "#d9bd8c")))


def tree_prop(sc, x, y, h):
    w = h * 0.62
    art = (tree_d(w / 2, h, h), "")
    sc.add((x, y, h / 2), [sc.panel((x, y - w / 2, h), (0, 1, 0), (0, 0, -1), w, h, art, (1, 0, 0), CREAM),
                           sc.panel((x - w / 2, y, h), (1, 0, 0), (0, 0, -1), w, h, art, (0, -1, 0), CREAM)])


def man_prop(sc, x, y, h=42):
    k = h / 46
    sc.add((x, y, h / 2), [f'<g transform="matrix({cT:.4f} {sT * sP:.4f} 0 {cP:.4f} {P((x - 14 * k, y, h + 3))[0]:.2f} {P((x - 14 * k, y, h + 3))[1]:.2f})">{man_art(h)}</g>'])
    sc.pts += [P((x - 14 * k, y, h)), P((x + 14 * k, y, 0))]


def fence(sc, x0, y, length, h=20):
    n = int(length // 8)
    d = "".join(f"M{i * 8},{h}V5l2.5,-5l2.5,5V{h}Z" for i in range(n)) + f"M0,9H{n * 8 - 3}v3H0Z" + f"M0,15H{n * 8 - 3}v2.5H0Z"
    sc.add((x0 + length / 2, y, h / 2), [sc.panel((x0, y, h), (1, 0, 0), (0, 0, -1), length, h, (d, ""), (0, -1, 0), CREAM)])


def awning(sc, x0, y0, z, w, out=26, drop=10):
    n = int(w // 8); sw = w / n
    S = math.hypot(out, drop)
    o = f"M0,0H{w}V{S}" + f"a{sw / 2},{sw / 2} 0 0,1 {-sw},0" * n + "Z"
    stripes = "".join(f'<rect x="{i * sw}" y="0" width="{sw}" height="{S}" fill="{CREAM}"/>' for i in range(0, n, 2))
    parts = [sc.panel((x0, y0, z), (1, 0, 0), (0, -out / S, -drop / S), w, S, (o, stripes), (0, -drop / S, out / S))]
    for px in (x0 + 2, x0 + w - 2):
        parts.append(sc.panel((px - 6, y0 - out + 2, z - drop + 2), (1, 0, 0), (0, 0, -1), 12, z - drop + 2,
                              ("M0,0", cane(6 if px < x0 + w / 2 else 6, z - drop + 2, z - drop - 2, 1 if px < x0 + w / 2 else -1)), (0, -1, 0)))
    sc.add((x0 + w / 2, y0 - out, z / 2), parts, bias=5)


# ---------------------------------------------------------------- configurations
def cfg_starter():
    s = Scene(); w, d, h = 120, 95, 60; r = w / 2
    plate(s, -18, -30, w + 36, d + 48)
    f = (round_win(27, r + 30, 12) + round_win(93, r + 30, 12) + sq_win(60, r + 18, 20, 20) + tree(60, r + h, 44)
         + snowflake(60, r - 22, 15) + cane(11, r + h, 30, 1) + cane(109, r + h, 30, -1))
    house(s, 0, 0, 0, w, d, h, "y", front=f, side=sq_win(28, 28, 20) + sq_win(67, 28, 20))
    return s, "1 · Starter cottage", "Core module on its own"


def cfg_wing():
    s = Scene(); w, d, h = 120, 95, 60; r = w / 2
    plate(s, -18, -30, w + 70 + 40, d + 48)
    f = door(60, r + h, 24, 42) + arch_win(25, r + 28, 18, 28) + arch_win(95, r + 28, 18, 28) + wreath(60, r - 20, 11)
    house(s, 0, 0, 0, w, d, h, "y", front=f, side=sq_win(72, 26, 18), chimney=(84, 55, 16, 16, 20))
    wr = 30
    house(s, w, 12, 0, 70, 60, 42, "x", front=sq_win(35, 22, 30, 20, 3), side=round_win(30, wr + 22, 10) + star(30, wr - 9, 7), ov_left=0)
    return s, "2 · Cottage + side wing", "Core + wing + chimney"


def cfg_two_storey():
    s = Scene(); w, d = 110, 90; r = w / 2
    plate(s, -18, -30, w + 36, d + 48)
    house(s, 0, 0, 0, w, d, 58, None, front=door(55, 58, 24, 42) + sq_win(22, 26, 20) + sq_win(88, 26, 20),
          side=sq_win(25, 26, 18) + sq_win(65, 26, 18))
    f = arch_win(30, r + 26, 16, 26) + arch_win(80, r + 26, 16, 26) + heart(55, r + 20, 9) + snowflake(55, r - 20, 14)
    house(s, 0, 0, 58, w, d, 48, "y", front=f, side=round_win(45, 24, 10), chimney=(78, 50, 15, 15, 20))
    return s, "3 · Two-storey townhouse", "Storey block + core roof"


def cfg_shop():
    s = Scene(); w, d, h = 150, 90, 64; r = d / 2
    plate(s, -18, -44, w + 40, d + 62)
    f = door(30, h, 24, 44) + sq_win(98, 36, 72, 30, 4) + plaque(98, 11, "SWEETS")
    house(s, 0, 0, 0, w, d, h, "x", front=f, side=round_win(45, r + 28, 12) + star(45, r - 16, 9), chimney=(40, 14, 15, 15, 20))
    awning(s, 60, 0, 60, 78)
    return s, "4 · Sweet shop", "Wide block turned sideways + awning"


def cfg_tower():
    s = Scene(); w = d = 82; r = w / 2 * math.tan(math.radians(58))
    plate(s, -18, -30, w + 36, d + 48)
    house(s, 0, 0, 0, w, d, 56, None, front=door(41, 56, 24, 42) + cane(11, 56, 28, 1) + cane(71, 56, 28, -1), side=sq_win(41, 26, 20))
    house(s, 0, 0, 56, w, d, 56, None, front=arch_win(24, 28, 16, 28) + arch_win(58, 28, 16, 28), side=arch_win(41, 28, 16, 28))
    house(s, 0, 0, 112, w, d, 30, "y", pitch=58, front=clock(41, r + 2, 15) + star(41, r - 32, 8), side=round_win(41, 15, 9))
    return s, "5 · Clock tower", "Three blocks stacked + steep roof"


def cfg_village():
    s = Scene()
    plate(s, -20, -60, 170, 185, tab=True); plate(s, 150, -60, 170, 185, tab=True); plate(s, 320, -60, 190, 185)
    w, d, h = 110, 90, 56; r = w / 2
    f = round_win(27, r + 28, 11) + round_win(83, r + 28, 11) + door(55, r + h, 22, 38) + snowflake(55, r - 20, 13)
    house(s, 5, 0, 0, w, d, h, "y", front=f, side=sq_win(45, 26, 18), chimney=(76, 50, 14, 14, 18))
    w2 = 100; r2 = w2 / 2
    house(s, 180, 0, 0, w2, d, 56, None, front=door(50, 56, 22, 40) + sq_win(20, 26, 18) + sq_win(80, 26, 18), side=sq_win(45, 26, 18))
    house(s, 180, 0, 56, w2, d, 46, "y", front=arch_win(28, r2 + 24, 15, 24) + arch_win(72, r2 + 24, 15, 24) + wreath(50, r2 - 18, 10),
          side=round_win(45, 23, 9))
    w3, d3 = 120, 80; r3 = d3 / 2
    house(s, 350, 5, 0, w3, d3, 54, "x", front=door(26, 54, 22, 40) + sq_win(78, 28, 56, 26, 3),
          side=heart(40, r3 + 24, 10) + star(40, r3 - 14, 8))
    tree_prop(s, 135, -28, 62); tree_prop(s, 305, -34, 78); tree_prop(s, 322, 60, 50); tree_prop(s, 492, -20, 56)
    man_prop(s, 30, -38); man_prop(s, 232, -40, 38); man_prop(s, 258, -40, 30); man_prop(s, 410, -36)
    fence(s, 40, -54, 80); fence(s, 360, -54, 110)
    return s, "6 · Village", "Base plates lock together; trees, fence and figures slot into them"


def main():
    cells = [cfg_starter(), cfg_wing(), cfg_two_storey(), cfg_shop(), cfg_tower()]
    CW, CH, PAD = 620, 520, 60
    k = min(min((CW - PAD) / (b[2] - b[0]), (CH - 110) / (b[3] - b[1])) for b in (s.bbox() for s, _, _ in cells))
    W, H = CW * 3, 110 + CH * 2 + 640
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter,sans-serif">',
           '<defs><radialGradient id="glow"><stop offset="0" stop-color="#ffe9a8"/><stop offset="1" stop-color="#f4a637"/></radialGradient>'
           '<radialGradient id="floor" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#000" stop-opacity="0.45"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient></defs>',
           f'<rect width="{W}" height="{H}" fill="#2b2f33"/>',
           f'<text x="{W / 2}" y="62" text-anchor="middle" font-size="34" font-weight="800" letter-spacing="3" fill="#f1e6d2">MODULAR GINGERBREAD VILLAGE · CONCEPT</text>',
           f'<text x="{W / 2}" y="94" text-anchor="middle" font-size="17" font-weight="500" letter-spacing="1" fill="#aab0b5">one set of 3 mm plywood panels, six ways to build it</text>']

    def place(scene, title, sub, x, y, cw, ch, scale):
        x0, y0, x1, y1 = scene.bbox()
        tx = x + cw / 2 - (x0 + x1) / 2 * scale
        ty = y + (ch - 70) / 2 + 10 - (y0 + y1) / 2 * scale
        out.append(f'<ellipse cx="{x + cw / 2}" cy="{ty + y1 * scale - 6}" rx="{(x1 - x0) * scale * 0.5}" ry="{(x1 - x0) * scale * 0.12}" fill="url(#floor)"/>')
        out.append(f'<g transform="translate({tx:.1f} {ty:.1f}) scale({scale:.4f})">{scene.svg()}</g>')
        out.append(f'<text x="{x + cw / 2}" y="{y + ch - 38}" text-anchor="middle" font-size="22" font-weight="700" letter-spacing="1.5" fill="#f1e6d2">{title.upper()}</text>')
        out.append(f'<text x="{x + cw / 2}" y="{y + ch - 12}" text-anchor="middle" font-size="16" fill="#aab0b5">{sub}</text>')

    slots = [(0, 110), (CW, 110), (2 * CW, 110), (CW * 0.5, 110 + CH), (CW * 1.5, 110 + CH)]
    for (s, t, sub), (x, y) in zip(cells, slots):
        b = s.bbox()
        place(s, t, sub, x, y, CW, CH, min(2.3, (CW - PAD) / (b[2] - b[0]), (CH - 100) / (b[3] - b[1])))
    s, t, sub = cfg_village()
    b = s.bbox()
    place(s, t, sub, 0, 110 + 2 * CH, W, 640, min((W - 160) / (b[2] - b[0]), 520 / (b[3] - b[1])))
    out.append("</svg>")
    path = os.path.join(ROOT, "gingerbread", "modular_concept.svg")
    open(path, "w").write("\n".join(out))
    print(path, f"scale {k:.2f} px/mm")


if __name__ == "__main__":
    main()
