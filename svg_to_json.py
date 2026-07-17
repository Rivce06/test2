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


try:
    paths, attributes = svg2paths("input/flower.svg")
    print(f"Loaded {len(paths)} vectors successfully.")
except Exception as e:
    print(f"Error opening SVG file: {str(e)}")
    exit(1)

result = {"coordenadas": [], "color": []}

for i, (path, attr) in enumerate(zip(paths, attributes)):
    # Break discontinuous paths into continuous pieces to prevent distortion
    subpaths = path.continuous_subpaths() if hasattr(path, "continuous_subpaths") else [path]

    for subpath in subpaths:
        puntos = []
        for segment in subpath:
            for t in np.linspace(0, 1, SAMPLES_PER_SEGMENT):
                try:
                    point = segment.point(t)
                    x = round(float(point.real), 2)
                    y = round(float(point.imag), 2)
                    punto = [x, y]
                except Exception:
                    continue

                if not puntos:
                    puntos.append(punto)
                    continue

                dx = punto[0] - puntos[-1][0]
                dy = punto[1] - puntos[-1][1]
                if (dx * dx + dy * dy) ** 0.5 >= MIN_POINT_SPACING:
                    puntos.append(punto)

        if len(puntos) > 2:  # Safe minimum for rendering a real shape polygon
            result["coordenadas"].append(puntos)
            result["color"].append(get_color(attr))

with open("output/data.json", "w") as file:
    json.dump(result, file, indent=2, ensure_ascii=False)

print("Optimized layout JSON file written completely.")