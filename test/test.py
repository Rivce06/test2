"""
Extrae automáticamente tx, ty, scale, rotation de cada grupo <g> de un SVG
compuesto visualmente en Inkscape/Illustrator/Figma.

Flujo de trabajo:
  1. Abrís el SVG con las 7 (u 11) flores en Inkscape.
  2. Cada flor debe estar en su propio grupo <g>.
  3. Movés, rotás y escalás cada grupo con el mouse hasta que quede como querés.
  4. Guardás el SVG.
  5. Corrés este script -> te imprime la lista BOUQUET lista para pegar en tu
     script principal.

No necesitas escribir NINGÚN número a mano.
"""

import re
import numpy as np
from lxml import etree


def parse_transform(transform_str):
    """Convierte un string transform="..." de SVG en una matriz 3x3
    (coordenadas homogéneas). Soporta translate, rotate, matrix y scale,
    encadenados en cualquier orden (como los escribe Inkscape)."""

    M = np.identity(3)

    # Cada función de transform: nombre(args...)
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", transform_str):
        nums = [float(x) for x in re.split(r"[,\s]+", args.strip()) if x]

        if name == "translate":
            tx = nums[0]
            ty = nums[1] if len(nums) > 1 else 0
            T = np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]])

        elif name == "matrix":
            a, b, c, d, e, f = nums
            T = np.array([[a, c, e], [b, d, f], [0, 0, 1]])

        elif name == "rotate":
            ang = np.radians(nums[0])
            cos_a, sin_a = np.cos(ang), np.sin(ang)
            if len(nums) == 3:
                cx, cy = nums[1], nums[2]
                T1 = np.array([[1, 0, cx], [0, 1, cy], [0, 0, 1]])
                R = np.array([[cos_a, -sin_a, 0], [sin_a, cos_a, 0], [0, 0, 1]])
                T2 = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]])
                T = T1 @ R @ T2
            else:
                T = np.array([[cos_a, -sin_a, 0], [sin_a, cos_a, 0], [0, 0, 1]])

        elif name == "scale":
            sx = nums[0]
            sy = nums[1] if len(nums) > 1 else sx
            T = np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]])

        else:
            continue  # skewX/skewY u otros, poco comunes acá

        M = M @ T

    return M


def decompose(M):
    """Descompone una matriz afín (traslación + rotación + escala uniforme)
    en tx, ty, scale, rotation_deg -- exactamente lo que usa transform_points().

    También detecta si el grupo fue volteado en espejo (flip horizontal),
    algo muy común al armar composiciones simétricas en Inkscape (Ctrl+H)."""
    a, c, e = M[0]
    b, d, f = M[1]

    det = a * d - b * c
    flip = det < 0

    if flip:
        # Deshacemos el flip para poder leer el ángulo de rotación "puro"
        a, b = -a, -b

    scale = round(float(np.hypot(a, b)), 4)
    rotation = round(float(np.degrees(np.arctan2(b, a))), 2)
    tx = round(float(e), 2)
    ty = round(float(f), 2)

    return tx, ty, scale, rotation, flip


def main(svg_path, group_ids=None):
    tree = etree.parse(svg_path)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Transform acumulado de los <g> padres (ej: la capa "layer1")
    def accumulated_transform(elem):
        M = np.identity(3)
        node = elem
        chain = []
        while node is not None:
            t = node.get("transform")
            if t:
                chain.append(t)
            node = node.getparent()
        for t in reversed(chain):
            M = M @ parse_transform(t)
        return M

    groups = root.findall(".//svg:g[@transform]", ns)

    # Ignorar la(s) capa(s) de Inkscape (inkscape:groupmode="layer"):
    # no son flores, son el contenedor general.
    layer_ns = "{http://www.inkscape.org/namespaces/inkscape}groupmode"
    groups = [g for g in groups if g.get(layer_ns) != "layer"]

    if group_ids:
        groups = [g for g in groups if g.get("id") in group_ids]

    any_flip = False
    print("BOUQUET = [")
    for i, g in enumerate(groups, start=1):
        M = accumulated_transform(g)
        tx, ty, scale, rotation, flip = decompose(M)
        gid = g.get("id", f"grupo_{i}")
        flip_note = "  <-- volteada en espejo (ver nota abajo)" if flip else ""
        any_flip = any_flip or flip
        print(f'    ("flower_{i}", {tx:>10}, {ty:>10}, {scale:>6}, {rotation:>7}),  # {gid}{flip_note}')
    print("]")

    if any_flip:
        print(
            "\n# NOTA: una o más flores están volteadas en espejo horizontal en el SVG.\n"
            "# Tu transform_points() actual NO soporta flip, solo escala/rota/traslada.\n"
            "# Si querés reproducir el espejo exacto, agregá un flag 'flip' por flor y,\n"
            "# dentro de transform_points, antes de escalar hacé: x = -x  (si flip=True)."
        )


if __name__ == "__main__":
    import sys
    svg_file = sys.argv[1] if len(sys.argv) > 1 else "input/composicion.svg"
    main(svg_file)