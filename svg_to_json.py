from svgpathtools import svg2paths
import numpy as np
import json
import math

SAMPLES_PER_SEGMENT = 6
MIN_POINT_SPACING = 2.5


def hex_to_rgb(color):
    """
    Convierte #RRGGBB o RRGGBB a valores 0-1 rounded to 3 decimals
    """
    if not color:
        return [1.0, 1.0, 1.0]

    color = color.strip().replace("#", "")

    if len(color) == 6:
        try:
            r = round(int(color[0:2], 16) / 255, 3)
            g = round(int(color[2:4], 16) / 255, 3)
            b = round(int(color[4:6], 16) / 255, 3)
            return [r, g, b]
        except ValueError:
            return [1.0, 1.0, 1.0]

    return [1.0, 1.0, 1.0]


def get_color(attr):
    """
    Intenta sacar el color del SVG
    """
    if attr.get("fill"):
        fill_val = attr["fill"].strip()
        if fill_val.lower() != "none":
            return hex_to_rgb(fill_val)

    if attr.get("style"):
        styles = attr["style"].split(";")
        for style in styles:
            style = style.strip()
            if style.startswith("fill:"):
                color = style.replace("fill:", "").strip()
                if color.lower() != "none":
                    return hex_to_rgb(color)

    return [0.1, 0.1, 0.1]


def clean_and_round_data(obj):
    """
    Recorre recursivamente el objeto eliminando valores incompatibles
    y redondeando floats a un formato amigable para Brython.
    """
    if isinstance(obj, dict):
        return {k: clean_and_round_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_and_round_data(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return round(obj, 2)  # 👈 Restringe la precisión a 2 decimales
    return obj


# Leer SVG
try:
    paths, attributes = svg2paths("input/flower.svg")
    print(f"Encontré {len(paths)} paths")
except Exception as e:
    print(f"Error al abrir el archivo SVG: {str(e)}")
    exit(1)

result = {
    "paths": [],
    "coordenadas": [],
    "color": []
}

for i, (path, attr) in enumerate(zip(paths, attributes)):
    puntos = []

    for segment in path:
        for t in np.linspace(0, 1, SAMPLES_PER_SEGMENT):
            try:
                point = segment.point(t)
                # Redondeamos aquí para evitar valores absurdamente pequeños o grandes
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
            distancia = (dx * dx + dy * dy) ** 0.5

            if distancia >= MIN_POINT_SPACING:
                puntos.append(punto)

    if puntos:
        color = get_color(attr)
        result["paths"].append(puntos)
        result["coordenadas"].append(puntos)
        result["color"].append(color)

# Sanitizar y redondear la estructura final
cleaned_result = clean_and_round_data(result)

# Guardar con formato limpio
with open("output/data.json", "w") as file:
    json.dump(
        cleaned_result,
        file,
        indent=2,
        ensure_ascii=False
    )

print("\n¡JSON recreado con éxito y optimizado para Brython!")