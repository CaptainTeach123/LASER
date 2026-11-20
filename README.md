# Laser gift files

## Kearney, Nebraska map coasters

Ready-to-import SVGs in `coasters/kearney/`, each 100 x 100 mm (about 4 in). Previews are in `previews/`.

| File | What it is |
| --- | --- |
| `round_engrave.svg` | Round coaster, whole city, engraved streets |
| `square_engrave.svg` | Square coaster, whole city, with coordinates |
| `set4_1_NW` ... `set4_4_SE` `_engrave.svg` | Set of four; pushed together they form one larger map |
| `*_score.svg` | Same designs with streets as single score lines (much faster, thinner look) |

### Layers (by colour)

| Colour | Operation |
| --- | --- |
| Black fill | Engrave |
| Blue line (score files only) | Score |
| Red line | Cut (the coaster outline) |

In xTool Creative Space: import the SVG, select the black shapes and set them to Engrave, the red outline to Cut
(and blue to Score). Engrave first, cut last. Check the imported size is 100 mm; if not, scale with the aspect ratio locked.

For pre-made blanks (slate, cork, bamboo rounds), delete the red outline and centre the artwork on the blank.

Street lines are 0.3 mm at their thinnest, so run a small material test before the real piece; power and speed
depend on the machine wattage and the material.

### Regenerating or changing the design

    pip install shapely fonttools
    python3 tools/make_coasters.py     # rewrites coasters/kearney/*.svg
    node tools/render_preview.js       # rewrites previews/*.png (needs playwright)

Size, map centre, zoom, line widths and text are parameters in `tools/make_coasters.py`.
`tools/extract_osm.py` rebuilds `data/kearney_osm.json.gz` from raw OpenStreetMap tiles.

Map data (c) OpenStreetMap contributors, ODbL.
