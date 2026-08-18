#!/usr/bin/env python3
"""
Parametric boxing-glove keychain generator.

Produces a one-piece, print-ready 3D model (glove body + thumb + cuff band
with raised borders, an integrated loop, and wrapped raised cuff text) and
exports it to .3mf.

Dimensions follow the design reference:
  Overall height ~45 mm, width ~32 mm, depth ~24 mm,
  cuff band height 10 mm, loop inner diameter 6 mm, text height ~3.5 mm.

Usage:
  python3 boxing_glove_keychain.py [--text FOCUS] [--out out.3mf]
"""

import argparse
import numpy as np
import trimesh
from trimesh.creation import icosphere, cylinder, extrude_polygon
from shapely.geometry import Polygon
from shapely.ops import unary_union
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def ellipsoid(ax, ay, az, center=(0, 0, 0), subdiv=4):
    """A unit sphere scaled to semi-axes (ax, ay, az)."""
    m = icosphere(subdivisions=subdiv, radius=1.0)
    m.apply_scale((ax, ay, az))
    m.apply_translation(center)
    return m


def text_to_mesh(text, font_size, depth, font=None):
    """Extrude a string into a mesh lying in the XY plane.

    Letters run along +X, baseline at y=0, extruded along +Z by `depth`.
    Returns (mesh, width) where width is the glyph run length in mm.
    """
    fp = FontProperties(family="DejaVu Sans", weight="bold")
    if font:
        fp = FontProperties(fname=font)
    tp = TextPath((0, 0), text, size=font_size, prop=fp)

    polys = []
    for poly in tp.to_polygons():
        if len(poly) < 3:
            continue
        polys.append(Polygon(poly))
    if not polys:
        raise ValueError("no glyph geometry produced")

    # resolve holes (e.g. the counters in O, C) via even-odd union
    shell = None
    for p in polys:
        p = p.buffer(0)
        shell = p if shell is None else shell.symmetric_difference(p)
    shell = unary_union(shell)

    geoms = list(shell.geoms) if shell.geom_type == "MultiPolygon" else [shell]
    meshes = [extrude_polygon(g, height=depth) for g in geoms if not g.is_empty]
    mesh = trimesh.util.concatenate(meshes)
    # center on X, baseline-ish center on Y
    b = mesh.bounds
    width = b[1][0] - b[0][0]
    mesh.apply_translation((-(b[0][0] + b[1][0]) / 2.0,
                            -(b[0][1] + b[1][1]) / 2.0, 0.0))
    return mesh, width


def wrap_around_cylinder(mesh, radius, z_center, y_axis_angle=0.0):
    """Bend a flat XY-plane mesh onto a cylinder about the Z axis.

    Input convention: local x -> arc position, local y -> vertical (Z),
    local z -> radial (outward) thickness.  The text is placed facing -Y
    (the front of the glove) by default.
    """
    v = mesh.vertices.copy()
    theta0 = -np.pi / 2 + y_axis_angle      # front of glove = -Y direction
    theta = theta0 + v[:, 0] / radius       # arc-length wrap (F at -X, S at +X)
    r = radius + v[:, 2]                    # radial offset from thickness
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = z_center + v[:, 1]
    out = mesh.copy()
    out.vertices = np.column_stack([x, y, z])
    out.fix_normals()
    return out


def torus(major_r, minor_r, sections=64, minor_sections=28):
    """Torus centered at origin, tube axis along the Y axis (loop hangs in XZ)."""
    u = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    w = np.linspace(0, 2 * np.pi, minor_sections, endpoint=False)
    U, W = np.meshgrid(u, w)
    # ring in XZ plane, tube swept around Y
    X = (major_r + minor_r * np.cos(W)) * np.cos(U)
    Z = (major_r + minor_r * np.cos(W)) * np.sin(U)
    Y = minor_r * np.sin(W)
    verts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

    ny, nx = W.shape
    faces = []
    for i in range(ny):
        for j in range(nx):
            a = i * nx + j
            b = i * nx + (j + 1) % nx
            c = ((i + 1) % ny) * nx + j
            d = ((i + 1) % ny) * nx + (j + 1) % nx
            faces.append([a, b, d])
            faces.append([a, d, c])
    m = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
    m.fix_normals()
    if m.volume < 0:
        m.invert()
    return m


# ---------------------------------------------------------------------------
# model
# ---------------------------------------------------------------------------
def build(cuff_text="FOCUS", font=None):
    parts = []

    # --- glove fist body (rounded, slightly flattened front-to-back) --------
    # width 32 -> ax 16, depth 24 -> ay 12, height of fist bulb ~ 30
    body = ellipsoid(16.0, 12.0, 15.0, center=(0, 0, 15.0), subdiv=4)
    parts.append(body)

    # knuckle fullness: a second bulge at the front to read as a fist
    knuckle = ellipsoid(14.0, 8.5, 11.0, center=(0, -3.0, 17.0), subdiv=4)
    parts.append(knuckle)

    # --- thumb (bump on the front-side, near the top of the fist) -----------
    thumb = ellipsoid(6.5, 7.5, 8.5, center=(11.5, -4.5, 17.0), subdiv=3)
    parts.append(thumb)

    # --- cuff band (cylinder that caps the top of the fist) -----------------
    cuff_r = 11.5
    cuff_bottom, cuff_top = 27.0, 37.0     # 10 mm band
    cuff = cylinder(radius=cuff_r, height=cuff_top - cuff_bottom, sections=96)
    cuff.apply_translation((0, 0, (cuff_bottom + cuff_top) / 2.0))
    parts.append(cuff)

    # raised top & bottom border rings on the cuff
    for zc in (cuff_bottom + 1.1, cuff_top - 1.1):
        ring = cylinder(radius=cuff_r + 0.8, height=2.2, sections=96)
        ring.apply_translation((0, 0, zc))
        parts.append(ring)

    # blend the cuff into the fist a touch
    blend = ellipsoid(11.5, 11.5, 4.0, center=(0, 0, 27.5), subdiv=3)
    parts.append(blend)

    # --- integrated loop ----------------------------------------------------
    loop_inner_d = 6.0
    minor_r = 1.7
    major_r = loop_inner_d / 2.0 + minor_r          # inner hole = 6 mm
    loop_z = cuff_top + 0.3 + major_r
    ring = torus(major_r, minor_r)
    ring.apply_translation((0, 0, loop_z))
    parts.append(ring)

    # neck connecting loop to cuff (short pillar, fully overlapping both)
    neck = cylinder(radius=2.6, height=6.0, sections=48)
    neck.apply_translation((0, 0, cuff_top + 1.0))
    parts.append(neck)

    # --- union everything into a single watertight solid --------------------
    glove = trimesh.boolean.union(parts, engine="manifold")

    # --- raised cuff text, wrapped onto the band ----------------------------
    if cuff_text:
        text_mesh, _ = text_to_mesh(cuff_text, font_size=6.0, depth=1.0,
                                    font=font)
        # text_mesh: x=along band, y=vertical, z=radial thickness
        text_z_center = (cuff_bottom + cuff_top) / 2.0
        wrapped = wrap_around_cylinder(text_mesh, radius=cuff_r,
                                       z_center=text_z_center)
        glove = trimesh.boolean.union([glove, wrapped], engine="manifold")

    # final cleanup
    glove.merge_vertices()
    glove.update_faces(glove.nondegenerate_faces())
    glove.update_faces(glove.unique_faces())
    glove.remove_unreferenced_vertices()
    glove.fix_normals()
    return glove


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="FOCUS", help="cuff text (\"\" for none)")
    ap.add_argument("--out", default="boxing_glove_keychain.3mf")
    ap.add_argument("--font", default=None, help="path to a .ttf font")
    args = ap.parse_args()

    mesh = build(cuff_text=args.text, font=args.font)

    print(f"watertight : {mesh.is_watertight}")
    print(f"volume     : {mesh.volume:.1f} mm^3")
    b = mesh.bounds
    dims = b[1] - b[0]
    print(f"bbox (mm)  : {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f}  (W x D x H)")
    print(f"triangles  : {len(mesh.faces)}")

    mesh.export(args.out)
    print(f"wrote      : {args.out}")


if __name__ == "__main__":
    main()
