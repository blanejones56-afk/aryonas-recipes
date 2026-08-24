#!/usr/bin/env python3
"""
Stylized sailor figure generator (Popeye-inspired, hands-on-hips pose).

Produces a chunky, print-ready, MULTI-COLOR figure and writes a colored .3mf
(3MF material extension) whose parts carry the requested palette:
white, black, red, blue (+ skin, brown, yellow where the figure needs them).

This is a simplified, cartoonish sculpt built from primitives -- it is NOT a
photo-accurate reproduction, but it reads clearly as the character and prints
in the right colors as separate parts (assign one filament per color, or use
an AMS/MMU).

Usage:
  python3 popeye_sailor_figure.py [--out popeye_sailor_figure.3mf] [--scale 1.0]
"""

import argparse
import numpy as np
import trimesh
from trimesh.creation import icosphere, capsule, cylinder


# --------------------------------------------------------------------------
# palette (name -> hex RGB)
# --------------------------------------------------------------------------
PALETTE = {
    "white": "#F2F2F2",
    "black": "#1A1A1A",
    "red":   "#C0271F",
    "blue":  "#2C6FB0",
    "skin":  "#E7B48C",
    "brown": "#6B3F22",
    "yellow": "#E6B325",
}

PARTS = []  # list of (trimesh, color_name)


def add(mesh, color):
    mesh = mesh.copy()
    mesh.merge_vertices()
    PARTS.append((mesh, color))
    return mesh


# --------------------------------------------------------------------------
# primitive helpers
# --------------------------------------------------------------------------
def ball(r, center, subdiv=3, scale=(1, 1, 1)):
    m = icosphere(subdivisions=subdiv, radius=r)
    m.apply_scale(scale)
    m.apply_translation(center)
    return m


def limb(a, b, r, sections=24):
    """Capsule from point a to point b with radius r."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    vec = b - a
    h = np.linalg.norm(vec)
    m = capsule(height=h, radius=r, count=[sections, sections])
    # capsule is along +Z from 0..h; align to vec, then move to a
    z = np.array([0, 0, 1.0])
    d = vec / h
    axis = np.cross(z, d)
    if np.linalg.norm(axis) < 1e-9:
        R = np.eye(4) if d[2] > 0 else trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    else:
        axis = axis / np.linalg.norm(axis)
        ang = np.arccos(np.clip(np.dot(z, d), -1, 1))
        R = trimesh.transformations.rotation_matrix(ang, axis)
    m.apply_transform(R)
    m.apply_translation(a)
    return m


def disc(r, h, center, sections=48):
    m = cylinder(radius=r, height=h, sections=sections)
    m.apply_translation(center)
    return m


# --------------------------------------------------------------------------
# the figure  (Z up, millimeters, ~150 mm tall before --scale)
# --------------------------------------------------------------------------
def build():
    PARTS.clear()

    # ---- shoes (brown) + soles (black) -----------------------------------
    for sx in (-20, 20):
        add(ball(11, (sx, 6, 8), scale=(1.15, 1.7, 0.85)), "brown")   # shoe
        add(disc(11.5, 4, (sx, 6, 3), sections=40), "black")          # sole
        # slight toe bump forward (-Y is front)
        add(ball(8, (sx, -6, 8), scale=(1.0, 1.2, 0.7)), "brown")

    # ---- legs / pants (blue), bowed stance -------------------------------
    add(limb((-20, 3, 14), (-9, 0, 64), 12), "blue")   # left leg
    add(limb((20, 3, 14), (9, 0, 64), 12), "blue")     # right leg
    # hips / seat
    add(ball(16, (0, 0, 66), scale=(1.25, 1.0, 0.9)), "blue")

    # ---- belt (white) ----------------------------------------------------
    add(disc(15.5, 6, (0, 0, 74), sections=56), "white")
    # buckle (yellow) at front
    add(ball(3.5, (0, -15, 74), scale=(1.4, 0.6, 1.2)), "yellow")

    # ---- torso / shirt (black) -------------------------------------------
    # tapered: narrow waist -> broad chest/shoulders
    torso = limb((0, 0, 76), (0, 0, 108), 15)
    torso.apply_scale([1.0, 1.0, 1.0])
    add(torso, "black")
    add(ball(20, (0, 0, 104), scale=(1.35, 0.95, 0.8)), "black")   # chest/shoulders

    # ---- red collar trim around the shoulders / neckline -----------------
    add(disc(18.5, 6, (0, 0, 110), sections=56), "red")
    add(ball(19, (0, 0, 110), scale=(1.28, 0.98, 0.45)), "red")

    # ---- neck (skin) -----------------------------------------------------
    add(limb((0, 0, 108), (0, 0, 120), 7), "skin")

    # ---- gold chain (yellow) around neck ---------------------------------
    add(disc(9.5, 3.5, (0, -2, 114), sections=48), "yellow")

    # ---- arms akimbo (hands on hips) -------------------------------------
    for sx in (-1, 1):
        shoulder = (sx * 19, 0, 106)
        elbow = (sx * 36, 3, 97)
        hand = (sx * 16, -6, 76)
        add(ball(9, shoulder, scale=(1.1, 1.1, 1.0)), "black")        # sleeve
        add(disc(9.5, 4, (sx * 23, 1, 101), sections=32), "red")      # sleeve trim
        add(limb(shoulder, elbow, 8.0), "skin")                       # upper arm
        # big Popeye forearm angling down onto the hip
        add(limb(elbow, hand, 11), "skin")
        add(ball(7.5, hand, scale=(1.0, 1.1, 1.0)), "skin")           # fist on hip
        # anchor-tattoo hint: a tiny dark bump on the outer forearm
        add(ball(1.6, (sx * 30, -9, 90)), "blue")

    # ---- head (skin): cranium + big jaw/chin -----------------------------
    add(ball(15, (0, 0, 134), scale=(1.0, 1.05, 1.0)), "skin")        # cranium
    add(ball(12, (0, -6, 126), scale=(1.15, 1.2, 1.0)), "skin")       # jaw/cheeks
    add(ball(7, (0, -12, 124), scale=(1.2, 1.0, 0.9)), "skin")        # big chin
    add(ball(4, (0, -6, 132), scale=(1.6, 1.0, 1.0)), "skin")         # brow
    # ears
    for sx in (-15, 15):
        add(ball(3.5, (sx, 2, 133), scale=(0.7, 1.1, 1.2)), "skin")

    # ---- pipe (brown stem + black bowl) ----------------------------------
    add(limb((6, -12, 128), (20, -20, 130), 1.6), "brown")           # stem
    add(ball(3.2, (20, -20, 132)), "black")                          # bowl

    # ---- sailor cap: white crown + black brim ----------------------------
    add(ball(15, (0, 1, 146), scale=(1.05, 1.05, 0.7)), "white")     # crown
    add(disc(15.5, 4.5, (0, 0, 141), sections=56), "black")         # brim band
    # little front peak of brim
    add(ball(6, (0, -13, 140), scale=(1.6, 1.0, 0.5)), "black")


# --------------------------------------------------------------------------
# colored 3MF writer (3MF material extension)
# --------------------------------------------------------------------------
def hex_to_3mf(h):
    return h.upper() + "FF" if len(h) == 7 else h.upper()


def write_3mf(path, parts):
    colors = list(dict.fromkeys(c for _, c in parts))     # unique, ordered
    cidx = {c: i for i, c in enumerate(colors)}

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append('<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">')
    L.append('<metadata name="Title">Stylized Sailor Figure</metadata>')
    L.append('<resources>')

    # base materials (one per color)
    L.append('<basematerials id="1">')
    for c in colors:
        L.append(f'<base name="{c}" displaycolor="{hex_to_3mf(PALETTE[c])}"/>')
    L.append('</basematerials>')

    # one mesh object per part, colored via pid/pindex
    oid = 2
    part_ids = []
    for mesh, color in parts:
        v = mesh.vertices
        f = mesh.faces
        L.append(f'<object id="{oid}" type="model" pid="1" pindex="{cidx[color]}">')
        L.append('<mesh><vertices>')
        L.append("".join(
            f'<vertex x="{x:.3f}" y="{y:.3f}" z="{z:.3f}"/>' for x, y, z in v))
        L.append('</vertices><triangles>')
        L.append("".join(
            f'<triangle v1="{a}" v2="{b}" v3="{c2}"/>' for a, b, c2 in f))
        L.append('</triangles></mesh></object>')
        part_ids.append(oid)
        oid += 1

    # assembled object made of all parts (single multicolor model)
    L.append(f'<object id="{oid}" type="model"><components>')
    for pid in part_ids:
        L.append(f'<component objectid="{pid}"/>')
    L.append('</components></object>')
    L.append('</resources>')
    L.append(f'<build><item objectid="{oid}"/></build>')
    L.append('</model>')
    model_xml = "\n".join(L)

    content_types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                     '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')

    import zipfile
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model_xml)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="popeye_sailor_figure.3mf")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="uniform scale (1.0 -> ~150 mm tall)")
    args = ap.parse_args()

    build()
    if args.scale != 1.0:
        for m, _ in PARTS:
            m.apply_scale(args.scale)

    # report
    allv = np.vstack([m.vertices for m, _ in PARTS])
    dims = allv.max(0) - allv.min(0)
    wt = sum(1 for m, _ in PARTS if m.is_watertight)
    print(f"parts       : {len(PARTS)}  (watertight: {wt}/{len(PARTS)})")
    print(f"colors      : {', '.join(dict.fromkeys(c for _, c in PARTS))}")
    print(f"bbox WxDxH  : {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")

    write_3mf(args.out, PARTS)
    print(f"wrote       : {args.out}")


if __name__ == "__main__":
    main()
