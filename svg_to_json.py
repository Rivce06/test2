from svgpathtools import svg2paths
import numpy as np
import json
import math

SAMPLES_PER_SEGMENT = 8  # Slightly increased for better curve definition
MIN_POINT_SPACING = 1.5


def hex_to_rgb(color):
    if not color:
        return [1.0, 1.0, 1.0]
    color = color.strip().replace("#", "")
    if len(color) == 6:
        try:
            return [
                round(int(color[0:2], 16) / 255, 3),
                round(int(color[2:4], 16) / 255, 3),
                round(int(color[4:6], 16) / 255, 3),
            ]
        except ValueError:
            pass
    return [1.0, 1.0, 1.0]


def get_color(attr):
    if attr.get("fill"):
        fill_val = attr["fill"].strip()
        if fill_val.lower() != "none" and not fill_val.startswith("url"):
            return hex_to_rgb(fill_val)

    if attr.get("style"):
        styles = attr["style"].split(";")
        for style in styles:
            style = style.strip()
            if style.startswith("fill:"):
                color = style.replace("fill:", "").strip()
                if color.lower() != "none" and not color.startswith("url"):
                    return hex_to_rgb(color)
    return [0.1, 0.1, 0.1]


def transform_points(points, tx, ty, scale, angle):
    angle = math.radians(angle)

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    transformed = []

    for x, y in points:

        # Escalar
        x *= scale
        y *= scale

        # Rotar
        xr = x * cos_a - y * sin_a
        yr = x * sin_a + y * cos_a

        # Trasladar
        xr += tx
        yr += ty

        transformed.append([
            round(xr, 2),
            round(yr, 2)
        ])

    return transformed


BOUQUET = [
    #     nombre           x     y   escala rotación
    ("centro",              0,    0, 1.00,   0),

    ("izquierda",         -55,   25, 0.92, -10),
    ("derecha",            55,   25, 0.92,  10),

    ("izquierda_arriba", -110,   70, 0.88, -18),
    ("derecha_arriba",    110,   70, 0.88,  18),

    ("abajo_izquierda",   -30,   55, 0.82,  -5),
    ("abajo_derecha",      30,   55, 0.82,   5),

    ("extrema_izquierda",-30, 90, 0.76, -5),
    ("extrema_derecha",   32, 93, 0.76,  5),

    ("frente_izquierda",  -80, 105, 0.78, -12),
    ("frente_derecha",     80, 107, 0.78,  12),
]

try:
    paths, attributes = svg2paths("input/flower.svg")
    print(f"Loaded {len(paths)} vectors successfully.")
except Exception as e:
    print(f"Error opening SVG file: {str(e)}")
    exit(1)

result = {"coordenadas": [], "color": []}

for name, tx, ty, scale, rotation in BOUQUET:

    for path, attr in zip(paths, attributes):

        subpaths = (
            path.continuous_subpaths()
            if hasattr(path, "continuous_subpaths")
            else [path]
        )

        for subpath in subpaths:

            puntos = []

            for segment in subpath:

                for t in np.linspace(0, 1, SAMPLES_PER_SEGMENT):

                    try:
                        point = segment.point(t)

                        x = float(point.real)
                        y = float(point.imag)

                        punto = [x, y]

                    except Exception:
                        continue

                    if not puntos:
                        puntos.append(punto)
                        continue

                    dx = punto[0] - puntos[-1][0]
                    dy = punto[1] - puntos[-1][1]

                    if math.sqrt(dx*dx + dy*dy) >= MIN_POINT_SPACING:
                        puntos.append(punto)

            if len(puntos) > 2:

                puntos = transform_points(
                    puntos,
                    tx,
                    ty,
                    scale,
                    rotation
                )

                result["coordenadas"].append(puntos)
                result["color"].append(get_color(attr))

with open("output/data.json", "w") as file:
    json.dump(result, file, indent=2, ensure_ascii=False)

print("Optimized layout JSON file written completely.")