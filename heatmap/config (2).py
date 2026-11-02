"""Valores por defecto y carga de config.toml.

Orden de prioridad, de menor a mayor: DEFAULTS, textos del idioma,
configuración base del TOML y cada bloque [[output]].
"""
import copy
import tomllib

from .locales import LOCALES, as_config

DEFAULTS: dict = {
    "user": "",
    "lang": "es",
    "label": "",
    "file": "heatmap.svg",
    "page": "",
    "layout": {
        "weeks": 53,
        "week_start": "monday",
        "orientation": "horizontal",
        "padding": 16,
        "cell_size": 11,
        "cell_gap": 3,
        "section_gap": 10,
        "scale": 1.0,
    },
    "cell": {
        "shape": "rounded",
        "radius": 2,
        "dot_ratio": 0.55,
        "border_width": 0,
        "hide_empty": False,
        "highlight_today": False,
        "today_width": 1.5,
    },
    "colors": {
        "background": "transparent",
        "card_border": "none",
        "card_border_width": 1,
        "card_radius": 8,
        "empty": "#161b22",
        "levels": ["#0e4429", "#006d32", "#26a641", "#39d353"],
        "cell_border": "#00000022",
        "today": "#ffffff",
        "title": "#e6edf3",
        "text": "#8b949e",
        "accent": "#39d353",
        "page_background": "#0d1117",
        "light": {},
    },
    "thresholds": {
        "mode": "fixed",
        "values": [1, 3, 6, 10],
    },
    "font": {
        "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
        "google": "",
        "google_weights": [400, 600, 700],
        "file": "",
        "title_family": "",
        "title_google": "",
        "title_size": 14,
        "title_weight": 600,
        "subtitle_size": 11,
        "label_size": 9,
        "letter_spacing": 0,
        "uppercase_title": False,
    },
    "title": {"show": True, "text": "LeetCode · {user}", "align": "left"},
    "subtitle": {"show": True, "text": "", "align": "left"},
    "months": {"show": True, "names": []},
    "weekdays": {"show": True, "labels": []},
    "legend": {"show": True, "less": "", "more": "", "align": "right"},
    "footer": {"show": False, "text": "", "align": "right"},
    "tooltip": {"show": False, "text": "", "date_format": ""},
    "animation": {
        "type": "none",
        "order": "column",
        "reverse": False,
        "duration": 0.45,
        "stagger": 0.012,
        "easing": "cubic-bezier(.2,.8,.2,1.2)",
        "loop": False,
        "loop_pause": 4,
        "empty_cells": True,
        "pulse_today": False,
        "pulse_streak": False,
        "pulse_speed": 1.6,
        "animate_text": False,
        "respect_reduced_motion": True,
    },
    "interaction": {
        "enabled": False,
        "hover": "dim",
        "effect": "gravity",
        "radius": 60,
        "strength": 1.0,
        "shrink": 0.2,
        "stiffness": 0.16,
        "damping": 0.74,
        "spotlight": False,
        "spotlight_dim": 0.3,
        "crosshair": False,
        "same_level": False,
        "ripple": True,
        "ripple_speed": 320,
        "ripple_scale": 0.35,
    },
}


def merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load(path: str) -> list[dict]:
    """Devuelve una configuración completa por cada salida."""
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    outputs = raw.pop("output", None) or [{}]
    locales = merge(LOCALES, raw.pop("locales", {}))
    if not raw.get("user"):
        raise SystemExit("config: falta 'user'")

    result = []
    for out in outputs:
        lang = out.get("lang", raw.get("lang", DEFAULTS["lang"]))
        if lang not in locales:
            raise SystemExit(f"config: idioma '{lang}' no disponible (opciones: {', '.join(locales)}); "
                             f"puedes añadirlo con una sección [locales.{lang}]")
        texts = merge(locales["es"], locales[lang])  # un idioma incompleto hereda del español
        cfg = merge(merge(merge(DEFAULTS, as_config(texts)), raw), out)
        result.append(cfg)
    return result
