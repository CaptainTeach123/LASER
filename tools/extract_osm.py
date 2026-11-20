#!/usr/bin/env python3
"""Condense raw OpenStreetMap .osm tiles into one small feature file.

Usage: extract_osm.py <dir-with-.osm-tiles> <out.json.gz>
Tiles come from https://api.openstreetmap.org/api/0.6/map?bbox=W,S,E,N
"""
import glob, gzip, json, sys
import xml.etree.ElementTree as ET

src, out = sys.argv[1], sys.argv[2]
nodes, ways, rels = {}, {}, {}
for f in sorted(glob.glob(f"{src}/*.osm")):
    for el in ET.parse(f).getroot():
        i = el.get("id")
        if el.tag == "node":
            nodes[i] = (round(float(el.get("lon")), 6), round(float(el.get("lat")), 6))
        elif el.tag == "way":
            ways[i] = ([n.get("ref") for n in el.findall("nd")],
                       {t.get("k"): t.get("v") for t in el.findall("tag")})
        elif el.tag == "relation":
            rels[i] = ([(m.get("type"), m.get("ref"), m.get("role")) for m in el.findall("member")],
                       {t.get("k"): t.get("v") for t in el.findall("tag")})

def geom(wid):
    return [nodes[n] for n in ways[wid][0] if n in nodes]

def is_water(t):
    return t.get("natural") == "water" or t.get("waterway") == "riverbank"

feat = {"roads": [], "rails": [], "waterlines": [], "water_outer": [], "water_inner": []}
ROADS = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
         "secondary", "secondary_link", "tertiary", "tertiary_link", "residential",
         "unclassified", "living_street", "service"}
for wid, (nds, t) in ways.items():
    g = geom(wid)
    if len(g) < 2:
        continue
    hw = t.get("highway")
    if hw in ROADS and t.get("service") not in ("parking_aisle", "driveway"):
        feat["roads"].append([hw, g])
    elif t.get("railway") == "rail" and t.get("service") not in ("yard", "spur", "siding"):
        feat["rails"].append(g)
    elif t.get("waterway") in ("river", "canal", "stream"):
        feat["waterlines"].append([t["waterway"], g])
    if is_water(t) and len(g) >= 4:
        feat["water_outer"].append(g)
for members, t in rels.values():
    if is_water(t):
        for typ, ref, role in members:
            if typ == "way" and ref in ways:
                g = geom(ref)
                if len(g) >= 2:
                    feat["water_inner" if role == "inner" else "water_outer"].append(g)

with gzip.open(out, "wt") as fh:
    json.dump(feat, fh, separators=(",", ":"))
print({k: len(v) for k, v in feat.items()})
