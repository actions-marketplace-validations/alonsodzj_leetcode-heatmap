"""Incrustación de fuentes en el SVG.

Un SVG mostrado como <img> no puede cargar recursos externos, así que las
fuentes se incrustan en base64 dentro de @font-face.
"""
import base64
import os
import re
import sys
import urllib.request

MIME = {".ttf": "font/ttf", ".otf": "font/otf", ".woff": "font/woff", ".woff2": "font/woff2"}

# Con un User-Agent moderno Google Fonts devuelve woff2.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read()


def google(family: str, weights: list[int]) -> str:
    name = family.replace(" ", "+")
    w = ";".join(str(x) for x in sorted(set(weights)))
    try:
        css = _get(f"https://fonts.googleapis.com/css2?family={name}:wght@{w}").decode()
    except Exception:
        # Fuentes con un único peso rechazan la lista de pesos.
        try:
            css = _get(f"https://fonts.googleapis.com/css2?family={name}").decode()
        except Exception as e:
            print(f"aviso: no se pudo descargar '{family}' de Google Fonts ({e})", file=sys.stderr)
            return ""

    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*{[^}]*})", css)
    faces = [b for subset, b in blocks if subset == "latin"] or [b for _, b in blocks]
    faces = faces or re.findall(r"@font-face\s*{[^}]*}", css)

    out = []
    for face in faces:
        m = re.search(r"url\((https://[^)]+)\)", face)
        if not m:
            continue
        data = base64.b64encode(_get(m.group(1))).decode()
        out.append(re.sub(r"src:[^;]+;",
                          f"src:url(data:font/woff2;base64,{data}) format('woff2');", face))
    return "".join(out)


def local(path: str, family: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:{MIME.get(ext, 'font/ttf')};base64,{data});}}"


def setup(cfg: dict) -> tuple[str, str, str]:
    """Devuelve (reglas @font-face, familia del texto, familia del título)."""
    css = []
    family = cfg["family"]
    if cfg["file"]:
        css.append(local(cfg["file"], "HeatmapFont"))
        family = f"'HeatmapFont', {family}"
    elif cfg["google"]:
        css.append(google(cfg["google"], cfg["google_weights"]))
        family = f"'{cfg['google']}', {family}"

    title = family
    if cfg["title_google"]:
        css.append(google(cfg["title_google"], [cfg["title_weight"]]))
        title = f"'{cfg['title_google']}', {family}"
    elif cfg["title_family"]:
        title = f"{cfg['title_family']}, {family}"
    return "".join(css), family, title
