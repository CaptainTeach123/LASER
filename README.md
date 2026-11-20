# Laser gift files

## Kearney, Nebraska map coasters

Ready-to-import SVGs in `coasters/kearney/`, each 100 x 100 mm (about 4 in). Previews are in `previews/`.

| File | What it is |
| --- | --- |
| `round_engrave.svg` | Round coaster, whole city, engraved streets |
| `square_engrave.svg` | Square coaster, whole city, with coordinates |
| `set4_1_NW` ... `set4_4_SE` `_engrave.svg` | Set of four; pushed together they form one larger map |
| `sheet_set4_*.svg` | The set of four laid out on one 204 x 204 mm sheet (fits a 12 x 12 in board) |
| `sheet_all6_*.svg` | All six coasters on one 308 x 204 mm sheet |
| `*_score.svg` | Same designs with streets as single score lines (much faster, thinner look) |

### Layers (by colour)

| Colour | Operation |
| --- | --- |
| Black fill | Engrave |
| Blue line (score files only) | Score |
| Red line | Cut (the coaster outline) |

In xTool Studio: import the SVG, select the black shapes and set them to Engrave, the red outline to Cut
(and blue to Score). Engrave first, cut last. Check the imported size is 100 mm; if not, scale with the aspect ratio locked.

For pre-made blanks (slate, cork, bamboo rounds), delete the red outline and centre the artwork on the blank.

### xTool X1 (55 W CO2) notes

- Work area is 615 x 320 mm, so every file here fits, including the six-coaster sheet.
- The CO2 spot is 0.175 mm. The thinnest street lines are 0.3 mm, so they will resolve; engrave at roughly
  100-140 lines/cm so adjacent passes just overlap.
- Pick the material in xTool Studio (for example 3 mm basswood plywood) and start from its built-in settings,
  then run Studio's material test array on an offcut. A 55 W tube needs low engrave power on thin plywood;
  too much power makes the fine street grid char together.
- Mask the wood with transfer tape before engraving to keep smoke stains off the surface, and seal the finished
  coasters (polyurethane or similar) so drinks do not stain them.

### Regenerating or changing the design

    pip install shapely fonttools
    python3 tools/make_coasters.py     # rewrites coasters/kearney/*.svg
    node tools/render_preview.js       # rewrites previews/*.png (needs playwright)

Size, map centre, zoom, line widths and text are parameters in `tools/make_coasters.py`.
`tools/extract_osm.py` rebuilds `data/kearney_osm.json.gz` from raw OpenStreetMap tiles.

Map data (c) OpenStreetMap contributors, ODbL.
