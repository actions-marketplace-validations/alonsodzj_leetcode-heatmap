"""Formas de celda como elementos SVG."""
import math

SHAPES = ("square", "rounded", "squircle", "circle", "dot", "diamond", "hexagon")


def cell(kind: str, x: float, y: float, size: float, attrs: str, *,
         radius: float = 2, dot_ratio: float = 0.55, inner: str = "") -> str:
    cx, cy = x + size / 2, y + size / 2
    if kind in ("square", "rounded", "squircle"):
        rx = {"square": 0, "rounded": min(radius, size / 2), "squircle": size * 0.32}[kind]
        tag = "rect"
        geo = f'x="{x:.2f}" y="{y:.2f}" width="{size}" height="{size}"' + (f' rx="{rx:.2f}"' if rx else "")
    elif kind in ("circle", "dot"):
        r = size / 2 * (dot_ratio if kind == "dot" else 1)
        tag = "circle"
        geo = f'cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}"'
    elif kind == "diamond":
        h = size / 2
        tag = "polygon"
        geo = f'points="{cx:.2f},{cy - h:.2f} {cx + h:.2f},{cy:.2f} {cx:.2f},{cy + h:.2f} {cx - h:.2f},{cy:.2f}"'
    elif kind == "hexagon":
        r = size / 2
        pts = " ".join(f"{cx + r * math.cos(math.radians(60 * i - 30)):.2f},"
                       f"{cy + r * math.sin(math.radians(60 * i - 30)):.2f}" for i in range(6))
        tag = "polygon"
        geo = f'points="{pts}"'
    else:
        raise SystemExit(f"config: forma de celda desconocida '{kind}' (opciones: {', '.join(SHAPES)})")
    if inner:
        return f"<{tag} {attrs} {geo}>{inner}</{tag}>"
    return f"<{tag} {attrs} {geo}/>"
