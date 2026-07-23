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


def transform_points(points, a, b, c, d, e, f):
    transformed = []

    for x, y in points:
        xr = a * x + c * y + e
        yr = b * x + d * y + f

        transformed.append([
            round(xr, 2),
            round(yr, 2)
        ])

    return transformed

BOUQUET = [
    ("flower1_g25846", 1.0, 0.0, 0.0, 1.0, 39.532, -11.889),

    ("flower2_g8649",
        1.000887,
        -0.111368,
        0.113896,
        0.981345,
        2.348,
        14.207),

    ("flower3_g17298",
        -1.000887,
        -0.111368,
        -0.113896,
        0.981345,
        297.705,
        16.607),

    ("flower4_g34596",
        0.950514,
        -0.332717,
        0.330803,
        0.930902,
        -45.646,
        75.153),

    ("flower5_g43245",
        -0.950514,
        -0.332717,
        -0.330803,
        0.930902,
        347.600,
        70.953),

    ("flower6_g51894",
        0.987515,
        0.157522,
        -0.157522,
        0.987515,
        88.451,
        26.810),

    ("flower7_g60543",
        0.985696,
        -0.168536,
        0.168536,
        0.985696,
        4.977,
        73.946),
]

try:
    paths, attributes = svg2paths("input/flower.svg")
    print(f"Loaded {len(paths)} vectors successfully.")
except Exception as e:
    print(f"Error opening SVG file: {str(e)}")
    exit(1)

result = {"coordenadas": [], "color": []}

for name, a, b, c, d, e, f in BOUQUET:

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
                    a,
                    b,
                    c,
                    d,
                    e,
                    f
                )

                result["coordenadas"].append(puntos)
                result["color"].append(get_color(attr))

with open("output/data.json", "w") as file:
    json.dump(result, file, indent=2, ensure_ascii=False)

print("Optimized layout JSON file written completely.")