"""Animaciones CSS: entrada, bucles y latidos.

Funcionan también cuando el SVG se muestra como <img> (por ejemplo en un
README de GitHub), porque no dependen de JavaScript ni de eventos.
"""
import math
import random

INTRO = {
    "fade": "from{opacity:0}to{opacity:1}",
    "pop": "0%{opacity:0;transform:scale(0)}70%{opacity:1;transform:scale(1.18)}100%{opacity:1;transform:scale(1)}",
    "rise": "from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}",
    "drop": "from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}",
    "spin": "from{opacity:0;transform:rotate(-90deg) scale(.3)}to{opacity:1;transform:none}",
}
LOOP = {
    "wave": "0%,100%{opacity:1;transform:none}50%{opacity:.35;transform:scale(.8)}",
    "sparkle": "0%,88%,100%{opacity:1;transform:none}94%{opacity:.25;transform:scale(.6)}",
}
TYPES = ("none", *INTRO, *LOOP)
SPARKLE_PERIOD = 6.0

_ORIGIN = "transform-box:fill-box;transform-origin:center;"


def _order(order: str, col: int, row: int, lvl: int, cols: int, rows: int, rnd) -> float:
    """Posición relativa de una celda en la secuencia, en 'pasos de columna'."""
    if order == "row":
        return (row * cols + col) / rows
    if order == "diagonal":
        return col + row
    if order == "random":
        return rnd.random() * cols
    if order == "level":
        return lvl * cols / 4 + col * 0.25
    if order == "center":
        return math.hypot(col - cols / 2, (row - rows / 2) * 1.5)
    return col + row / rows  # column


def delays(cells: list, cfg: dict, cols: int, rows: int) -> list:
    """Retardo de animación (s) para cada celda, o None si no se anima.

    `cells` es una lista de (col, row, level, pulsing).
    """
    kind = cfg["type"]
    if kind == "none":
        return [None] * len(cells)

    rnd = random.Random(1)
    if kind == "sparkle":
        return [rnd.random() * SPARKLE_PERIOD if lvl and not pulsing else None
                for _, _, lvl, pulsing in cells]

    keys = [_order(cfg["order"], c, r, lvl, cols, rows, rnd) for c, r, lvl, _ in cells]
    top = max(keys, default=0)
    per_column = cfg["stagger"] * rows
    out = []
    for key, (_, _, lvl, pulsing) in zip(keys, cells):
        if pulsing or (lvl == 0 and not cfg["empty_cells"]):
            out.append(None)
            continue
        out.append(((top - key) if cfg["reverse"] else key) * per_column)
    return out


def css(cfg: dict) -> str:
    kind = cfg["type"]
    rules = []

    if kind in INTRO:
        if cfg["loop"]:
            total = cfg["duration"] + cfg["loop_pause"]
            p = cfg["duration"] / total * 100
            if kind == "pop":
                frames = (f"0%{{opacity:0;transform:scale(0)}}{p * .7:.1f}%{{opacity:1;transform:scale(1.18)}}"
                          f"{p:.1f}%{{opacity:1;transform:scale(1)}}")
            else:
                frames = INTRO[kind].replace("from", "0%").replace("to{", f"{p:.1f}%{{")
            frames += f"{100 - p * .5:.1f}%{{opacity:1;transform:none}}100%{{opacity:0}}"
            rules.append(f"@keyframes hm{{{frames}}}")
            rules.append(f".an{{{_ORIGIN}animation:hm {total:.2f}s {cfg['easing']} infinite both}}")
        else:
            rules.append(f"@keyframes hm{{{INTRO[kind]}}}")
            rules.append(f".an{{{_ORIGIN}animation:hm {cfg['duration']}s {cfg['easing']} both}}")
    elif kind == "wave":
        rules.append(f"@keyframes hm{{{LOOP['wave']}}}")
        rules.append(f".an{{{_ORIGIN}animation:hm {max(cfg['duration'] * 4, 1.2):.2f}s ease-in-out infinite}}")
    elif kind == "sparkle":
        rules.append(f"@keyframes hm{{{LOOP['sparkle']}}}")
        rules.append(f".an{{{_ORIGIN}animation:hm {SPARKLE_PERIOD}s ease-in-out infinite}}")
    elif kind != "none":
        raise SystemExit(f"config: animación desconocida '{kind}' (opciones: {', '.join(TYPES)})")

    if cfg["pulse_today"] or cfg["pulse_streak"]:
        rules.append("@keyframes pz{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.55;transform:scale(.82)}}")
        rules.append(f".pz{{{_ORIGIN}animation:pz {cfg['pulse_speed']}s ease-in-out infinite}}")
    if cfg["animate_text"]:
        rules.append("@keyframes at{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}")
        rules.append(".at{animation:at .8s ease-out both}")
    if rules and cfg["respect_reduced_motion"]:
        rules.append("@media (prefers-reduced-motion:reduce){.an,.pz,.at{animation:none!important}}")
    return "".join(rules)
