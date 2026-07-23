from svgpathtools import svg2paths
import numpy as np
import json
import math

SAMPLES_PER_SEGMENT = 8
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
    style_dict = {}

    # Extract properties from inline CSS style="fill:#ffffff; stroke:#000000"
    if attr.get("style"):
        for item in attr["style"].split(";"):
            if ":" in item:
                k, v = item.split(":", 1)
                style_dict[k.strip().lower()] = v.strip().lower()

    # 1. Check direct attribute fill or inline style fill
    fill = attr.get("fill") or style_dict.get("fill")
    if fill and fill != "none" and not fill.startswith("url"):
        return hex_to_rgb(fill)

    # 2. Check direct attribute stroke or inline style stroke (if fill is none/missing)
    stroke = attr.get("stroke") or style_dict.get("stroke")
    if stroke and stroke != "none" and not stroke.startswith("url"):
        return hex_to_rgb(stroke)

    # 3. Default fallback if neither fill nor stroke is specified
    return [0.9, 0.9, 0.9]  # Light gray default instead of dark/black


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


##########################################################
# OBJETOS DEL RAMO
##########################################################

OBJECTS = [
    ("flower", "g25846", 1.000000, 0.000000, 0.000000, 1.000000, 39.532, -11.889),
    ("flower", "g8649", 1.000887, -0.111368, 0.113896, 0.981345, 2.348, 14.207),
    ("flower", "g17298", -1.000887, -0.111368, -0.113896, 0.981345, 297.705, 16.607),
    ("flower", "g34596", 0.950514, -0.332717, 0.330803, 0.930902, -45.646, 75.153),
    ("flower", "g43245", -0.950514, -0.332717, -0.330803, 0.930902, 347.600, 70.953),
    ("flower", "g51894", 0.987515, 0.157522, -0.157522, 0.987515, 88.451, 26.810),
    ("flower", "g60543", 0.985696, -0.168536, 0.168536, 0.985696, 4.977, 73.946),
    ("wrapper", "g1", 1.252009, 0.000000, 0.000000, 1.000000, 20.635, 29.232),
]

##########################################################
# CARGAR SVGS
##########################################################

flower_paths, flower_attr = svg2paths("input/flower.svg")
wrapper_paths, wrapper_attr = svg2paths("input/wrapper.svg")

print(f"Flower paths : {len(flower_paths)}")
print(f"Wrapper paths: {len(wrapper_paths)}")

##########################################################

result = {
    "coordenadas": [],
    "color": []
}

##########################################################

for obj_type, name, a, b, c, d, e, f in OBJECTS:

    if obj_type == "flower":

        paths = flower_paths
        attributes = flower_attr

    elif obj_type == "wrapper":

        paths = wrapper_paths
        attributes = wrapper_attr

    else:
        continue

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

                        punto = [
                            float(point.real),
                            float(point.imag)
                        ]

                    except Exception:
                        continue

                    if not puntos:

                        puntos.append(punto)
                        continue

                    dx = punto[0] - puntos[-1][0]
                    dy = punto[1] - puntos[-1][1]

                    if math.hypot(dx, dy) >= MIN_POINT_SPACING:
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

##########################################################

with open("output/data.json", "w") as file:
    json.dump(
        result,
        file,
        indent=2,
        ensure_ascii=False
    )

print("JSON exportado correctamente.")