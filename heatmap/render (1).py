"""Construcción del SVG."""
import datetime as dt
import hashlib
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from xml.sax.saxutils import escape

from . import data, fonts, motion, shapes
from .config import merge

WEEK_START = {"monday": 0, "sunday": 6}
HOVER = {
    "none": "",
    "dim": ".c:hover{opacity:.6}",
    "outline": ".c:hover{stroke:var(--accent);stroke-width:1.5}",
    "glow": ".c:hover{filter:drop-shadow(0 0 3px var(--accent))}",
    "grow": ".c:hover{transform:scale(1.25)}",
}
JS_PATH = os.path.join(os.path.dirname(__file__), "interact.js")


@dataclass
class Cell:
    col: int
    row: int
    day: dt.date
    count: int
    level: int
    x: float
    y: float
    pulsing: bool


class _Vars(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def fill(template: str, values: dict) -> str:
    return template.format_map(_Vars(values))


def rich(text: str) -> str:
    """Escapa el texto y pinta con el color de acento lo que va entre **."""
    parts = text.split("**")
    return "".join(f'<tspan class="ac">{escape(p)}</tspan>' if i % 2 else escape(p)
                   for i, p in enumerate(parts))


def text_width(text: str, size: float) -> float:
    """Estimación del ancho; suficiente para reservar espacio y alinear."""
    text = text.replace("**", "")
    wide = sum(1 for ch in text if unicodedata.east_asian_width(ch) in "WF")
    return (len(text) - wide) * size * 0.56 + wide * size


def color_rules(c: dict, levels: int) -> str:
    bg = "none" if c["background"] == "transparent" else c["background"]
    rules = [
        f":root{{--accent:{c['accent']}}}",
        f".bg{{fill:{bg};stroke:{c['card_border']}}}",
        f".l0{{fill:{c['empty']}}}",
        f".ti{{fill:{c['title']}}}",
        f".tx{{fill:{c['text']}}}",
        f".ac{{fill:{c['accent']}}}",
        f".today{{stroke:{c['today']}}}",
        f".cb{{stroke:{c['cell_border']}}}",
    ]
    rules += [f".l{i + 1}{{fill:{col}}}" for i, col in enumerate(c["levels"][:levels])]
    return "".join(rules)


def render(cfg: dict, counts: dict, today: dt.date, interactive: bool | None = None) -> str:
    lay, cel, font, col = cfg["layout"], cfg["cell"], cfg["font"], cfg["colors"]
    anim, ix = cfg["animation"], cfg["interaction"]
    if interactive is None:
        interactive = ix["enabled"]

    size, gap, pad, sgap = lay["cell_size"], lay["cell_gap"], lay["padding"], lay["section_gap"]
    step = size + gap
    weeks = lay["weeks"]
    week_start = WEEK_START.get(lay["week_start"], 0)
    vertical = lay["orientation"] == "vertical"
    n_levels = len(col["levels"])

    first = today - dt.timedelta(days=(today.weekday() - week_start) % 7, weeks=weeks - 1)
    st = data.stats(counts, today, first)
    streak = set(data.current_streak(counts, today))
    window = [counts.get(first + dt.timedelta(days=i), 0) for i in range((today - first).days + 1)]
    limits = data.thresholds(cfg["thresholds"]["mode"], cfg["thresholds"]["values"], window, n_levels)

    values = {"user": cfg["user"], "weeks": weeks,
              "updated": today.strftime(cfg["tooltip"]["date_format"]), **st}

    wd = cfg["weekdays"]["labels"]
    wd = [wd[(week_start + i) % 7] for i in range(7)] if len(wd) == 7 else [""] * 7
    lab = font["label_size"]
    show_months, show_days = cfg["months"]["show"], cfg["weekdays"]["show"] and any(wd)

    cols, rows = (7, weeks) if vertical else (weeks, 7)
    grid_w, grid_h = cols * step - gap, rows * step - gap

    if vertical:
        margin_left = max(text_width(n, lab) for n in cfg["months"]["names"]) + 6 if show_months else 0
        margin_top = lab + 5 if show_days else 0
    else:
        margin_left = max(text_width(n, lab) for n in wd) + 6 if show_days else 0
        margin_top = lab + 5 if show_months else 0

    title = fill(cfg["title"]["text"], values)
    if font["uppercase_title"]:
        title = title.upper()
    subtitle = fill(cfg["subtitle"]["text"], values)
    footer = fill(cfg["footer"]["text"], values)

    content_w = margin_left + grid_w
    if cfg["legend"]["show"]:
        legend_w = (text_width(cfg["legend"]["less"], lab) + text_width(cfg["legend"]["more"], lab)
                    + (n_levels + 1) * step + 12)
        content_w = max(content_w, legend_w)
    if cfg["title"]["show"]:
        content_w = max(content_w, text_width(title, font["title_size"]))
    if cfg["subtitle"]["show"]:
        content_w = max(content_w, text_width(subtitle, font["subtitle_size"]))
    width = content_w + 2 * pad

    def anchor(align: str) -> tuple[float, str]:
        return {"center": (width / 2, "middle"), "right": (width - pad, "end")}.get(align, (pad, "start"))

    text_anim = " at" if anim["animate_text"] else ""
    head, tail = [], []
    y = pad

    if cfg["title"]["show"]:
        y += font["title_size"]
        x, a = anchor(cfg["title"]["align"])
        head.append(f'<text class="ti tt{text_anim}" x="{x:.1f}" y="{y:.1f}" text-anchor="{a}">{rich(title)}</text>')
        y += sgap * 0.6
    if cfg["subtitle"]["show"]:
        y += font["subtitle_size"]
        x, a = anchor(cfg["subtitle"]["align"])
        head.append(f'<text class="tx st{text_anim}" x="{x:.1f}" y="{y:.1f}" text-anchor="{a}">{rich(subtitle)}</text>')
        y += sgap * 0.6
    if head:
        y += sgap * 0.6

    x0, y0 = pad + margin_left, y + margin_top

    # Rejilla
    cells: list[Cell] = []
    month_starts: list[tuple[int, int]] = []
    for w in range(weeks):
        for d in range(7):
            day = first + dt.timedelta(weeks=w, days=d)
            if day > today:
                continue
            if d == 0 and (not month_starts or month_starts[-1][1] != day.month):
                month_starts.append((w, day.month))
            n = counts.get(day, 0)
            lvl = data.level(n, limits)
            if lvl == 0 and cel["hide_empty"]:
                continue
            c, r = (d, w) if vertical else (w, d)
            pulsing = bool((anim["pulse_today"] and day == today and n) or
                           (anim["pulse_streak"] and day in streak))
            cells.append(Cell(c, r, day, n, lvl, x0 + c * step, y0 + r * step, pulsing))

    delays = motion.delays([(c.col, c.row, c.level, c.pulsing) for c in cells], anim, cols, rows)
    tip_cfg = cfg["tooltip"]
    # En la versión interactiva el hover solo anima: sin texto.
    use_title = tip_cfg["show"] and not interactive
    shape_opts = {"radius": cel["radius"], "dot_ratio": cel["dot_ratio"]}

    cell_svg = []
    for c, delay in zip(cells, delays):
        classes = ["c", f"l{c.level}"]
        if cel["border_width"]:
            classes.append("cb")
        if cel["highlight_today"] and c.day == today:
            classes.append("today")
        if c.pulsing:
            classes.append("pz")
        attrs = ""
        if delay is not None:
            classes.append("an")
            attrs += f' style="animation-delay:{delay:.3f}s"'
        if interactive:
            attrs += (f' data-c="{c.col}" data-r="{c.row}" data-l="{c.level}"'
                      f' data-x="{c.x + size / 2:.2f}" data-y="{c.y + size / 2:.2f}"')
        inner = ""
        if use_title:
            tip = fill(tip_cfg["text"], {**values, "count": c.count,
                                         "date": c.day.strftime(tip_cfg["date_format"])})
            inner = f"<title>{escape(tip)}</title>"
        cell_svg.append(shapes.cell(cel["shape"], c.x, c.y, size,
                                    f'class="{" ".join(classes)}"{attrs}', inner=inner, **shape_opts))

    # Etiquetas
    labels = []
    if show_months:
        names = cfg["months"]["names"]
        last = float("-inf")
        for w, m in month_starts:
            name = names[m - 1]
            if vertical:
                pos = y0 + w * step
                if pos - last < lab + 2 or pos + size > y0 + grid_h + 1:
                    continue
                labels.append(f'<text class="tx" x="{x0 - 6:.1f}" y="{pos + size * .8:.1f}" text-anchor="end">{escape(name)}</text>')
            else:
                pos = x0 + w * step
                if pos - last < text_width(name, lab) + 4 or pos + text_width(name, lab) > x0 + grid_w + 2:
                    continue
                labels.append(f'<text class="tx" x="{pos:.1f}" y="{y0 - 5:.1f}">{escape(name)}</text>')
            last = pos
    if show_days:
        for i, name in enumerate(wd):
            if not name:
                continue
            if vertical:
                labels.append(f'<text class="tx" x="{x0 + i * step + size / 2:.1f}" y="{y0 - 5:.1f}" text-anchor="middle">{escape(name)}</text>')
            else:
                labels.append(f'<text class="tx" x="{x0 - 6:.1f}" y="{y0 + i * step + size * .8:.1f}" text-anchor="end">{escape(name)}</text>')

    y = y0 + grid_h

    # Leyenda
    if cfg["legend"]["show"]:
        y += sgap
        less, more = cfg["legend"]["less"], cfg["legend"]["more"]
        wl = text_width(less, lab) + 6 if less else 0
        wm = text_width(more, lab) + 6 if more else 0
        total = wl + (n_levels + 1) * step - gap + wm
        lx = {"left": x0, "center": (width - total) / 2}.get(cfg["legend"]["align"], width - pad - total)
        ty = y + size * .82
        cx = lx + wl
        parts = []
        if less:
            parts.append(f'<text class="tx" x="{cx - 6:.1f}" y="{ty:.1f}" text-anchor="end">{escape(less)}</text>')
        for i in range(n_levels + 1):
            parts.append(shapes.cell(cel["shape"], cx, y, size,
                                     f'class="l{i}{" cb" if cel["border_width"] else ""}"', **shape_opts))
            cx += step
        if more:
            parts.append(f'<text class="tx" x="{cx - gap + 6:.1f}" y="{ty:.1f}">{escape(more)}</text>')
        tail.append(f'<g class="{text_anim.strip()}">' + "".join(parts) + "</g>" if text_anim else "".join(parts))
        y += size

    if cfg["footer"]["show"]:
        y += sgap + lab
        x, a = anchor(cfg["footer"]["align"])
        tail.append(f'<text class="tx" x="{x:.1f}" y="{y:.1f}" text-anchor="{a}">{rich(footer)}</text>')

    height = y + pad

    # Estilos
    face, family, title_family = fonts.setup(font)
    css = [
        face,
        f"text{{font-family:{family};font-size:{lab}px;letter-spacing:{font['letter_spacing']}px}}",
        f".tt{{font-family:{title_family};font-size:{font['title_size']}px;font-weight:{font['title_weight']}}}",
        f".st{{font-size:{font['subtitle_size']}px}}",
        ".ac{font-weight:700}",
        ".c{transform-box:fill-box;transform-origin:center;transition:opacity .15s,filter .15s}",
        color_rules(col, n_levels),
        motion.css(anim),
    ]
    if cel["border_width"]:
        css.append(f".cb{{stroke-width:{cel['border_width']}}}")
    if cel["highlight_today"]:
        css.append(f".today{{stroke-width:{cel['today_width']}}}")
    hover = ix["hover"]
    if hover not in HOVER:
        raise SystemExit(f"config: hover desconocido '{hover}' (opciones: {', '.join(HOVER)})")
    if not (hover == "grow" and interactive and ix["effect"] != "none"):
        css.append(HOVER[hover])
    if col["light"]:
        css.append("@media (prefers-color-scheme:light){" + color_rules(merge(col, col["light"]), n_levels) + "}")

    svg_id = "hm-" + hashlib.sha1(f"{cfg['user']}{cfg['file']}".encode()).hexdigest()[:8]
    script = ""
    if interactive:
        css.append(".live .an,.live .pz{animation:none}.live .c{transition:none}"
                   ".fx .c:not(.on){opacity:.22!important}")
        settings = {
            "id": svg_id, "size": size, "step": step, "gap": gap, "x0": x0, "y0": y0,
            "effect": ix["effect"], "radius": ix["radius"], "strength": ix["strength"],
            "shrink": ix["shrink"], "stiffness": ix["stiffness"], "damping": ix["damping"],
            "spotlight": ix["spotlight"], "spotlightDim": ix["spotlight_dim"],
            "crosshair": ix["crosshair"], "sameLevel": ix["same_level"],
            "ripple": ix["ripple"], "rippleSpeed": ix["ripple_speed"], "rippleScale": ix["ripple_scale"],
            "introAnimation": anim["type"] in motion.INTRO,
        }
        with open(JS_PATH, encoding="utf-8") as f:
            js = f.read().replace("__CONFIG__", json.dumps(settings))
        js = re.sub(r"^\s*//.*\n", "", js, flags=re.M)
        script = f"<script><![CDATA[\n{js}]]></script>"

    scale = lay["scale"]
    background = (f'<rect class="bg" x="0.5" y="0.5" width="{width - 1:.1f}" height="{height - 1:.1f}" '
                  f'rx="{col["card_radius"]}" stroke-width="{col["card_border_width"]}"/>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" id="{svg_id}" width="{width * scale:.0f}" '
        f'height="{height * scale:.0f}" viewBox="0 0 {width:.1f} {height:.1f}" role="img" '
        f'aria-label="{escape(fill(cfg["label"], values))}">',
        f"<style>{''.join(css)}</style>",
        background, *head, "".join(labels), "".join(cell_svg), *tail, script,
        "</svg>", "",
    ])


def page(svg: str, cfg: dict) -> str:
    """Página HTML mínima con el SVG en línea (para GitHub Pages)."""
    return f"""<!doctype html>
<html lang="{cfg["lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LeetCode · {escape(cfg["user"])}</title>
<style>
  html,body{{margin:0;height:100%}}
  body{{display:grid;place-items:center;background:{cfg["colors"]["page_background"]};padding:16px;box-sizing:border-box}}
  svg{{max-width:100%;height:auto}}
</style>
</head>
<body>
{svg}
</body>
</html>
"""
