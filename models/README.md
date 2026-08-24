# Boxing Glove Keychain — 3D printable model

`boxing_glove_keychain.3mf` is a print-ready mini boxing-glove keychain,
generated to match the design reference: a rounded fist with a thumb, a cuff
band with raised top/bottom borders and raised **FOCUS** text, and a one-piece
integrated loop.

## The file
- **`boxing_glove_keychain.3mf`** — the model. Single watertight, manifold
  body. Units are millimeters. Drop it straight into a slicer
  (Bambu Studio, PrusaSlicer, Cura, etc.).

## Dimensions (as generated)
| Property | Value |
|---|---|
| Overall height (incl. loop) | ~48 mm |
| Overall width | ~34 mm |
| Overall depth | ~25 mm |
| Cuff band height | 10 mm |
| Loop inner diameter | 6 mm (fits a standard split ring) |
| Cuff text | raised ~1 mm, ~4.3 mm tall |

## Printing
- **Orientation:** loop up, as modeled. No supports needed in this
  orientation for most printers.
- **Material:** PLA, PETG, or resin all work well.
- **Layer height:** 0.12–0.20 mm for crisp cuff text.
- Sand cut edges lightly before painting if desired. Great for single-color
  or multi-color (paint the recessed cuff / raised text for contrast).

## Regenerating / customizing
The model is parametric. Requires: `numpy trimesh shapely manifold3d
matplotlib scipy`.

```bash
# default (FOCUS)
python3 boxing_glove_keychain.py

# custom cuff text and output name
python3 boxing_glove_keychain.py --text CHAMPION --out champion.3mf

# no text
python3 boxing_glove_keychain.py --text "" --out plain.3mf

# use your own font
python3 boxing_glove_keychain.py --text USA --font /path/to/font.ttf
```

Edit the constants in `build()` (body/cuff/loop sizes) to tweak proportions.

---

# Stylized Sailor Figure (Popeye-inspired) — multi-color

`popeye_sailor_figure.3mf` is a chunky, cartoonish sailor figure in the
hands-on-hips pose (cap, pipe, big forearms, gold chain), built from
primitives. It is a **simplified stylized sculpt**, not a photo-accurate
reproduction — a detailed character like the reference photos needs an
image-to-3D AI tool or hand-sculpting in Blender/ZBrush.

- **Multi-color:** parts carry the requested palette — **white, black, red,
  blue** (+ skin, brown, yellow). Colors are embedded via the 3MF material
  extension, and the parts import as one assembled multi-color object.
  Assign one filament per color, or use an AMS/MMU for a single print.
- **Size:** ~180 mm tall (`--scale` to resize), millimeters, all parts
  watertight.

```bash
python3 popeye_sailor_figure.py                 # default, ~180 mm tall
python3 popeye_sailor_figure.py --scale 0.5     # half size (~90 mm)
python3 popeye_sailor_figure.py --out sailor.3mf
```

Requires: `numpy trimesh`. Colors live in the `PALETTE` dict; pose/proportions
are in `build()`.

