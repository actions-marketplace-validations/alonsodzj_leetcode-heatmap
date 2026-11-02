#!/usr/bin/env python3
"""Genera los heatmaps definidos en config.toml.

    python generate.py                 datos reales
    python generate.py --sample        datos de prueba, sin conexión
    python generate.py -c otro.toml --outdir build
"""
import argparse
import datetime as dt
import os

from heatmap import config, data
from heatmap.render import page, render


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-c", "--config", default="config.toml")
    parser.add_argument("--outdir", default=".")
    parser.add_argument("--sample", action="store_true", help="usar datos aleatorios")
    args = parser.parse_args()

    outputs = config.load(args.config)
    today = dt.datetime.now(dt.timezone.utc).date()
    user = outputs[0]["user"]
    counts = data.sample(today) if args.sample else data.fetch(user, today)

    os.makedirs(args.outdir, exist_ok=True)
    for cfg in outputs:
        path = os.path.join(args.outdir, cfg["file"])
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(cfg, counts, today))
        print(path)

        if cfg["page"]:
            path = os.path.join(args.outdir, cfg["page"])
            with open(path, "w", encoding="utf-8") as f:
                f.write(page(render(cfg, counts, today, interactive=True), cfg))
            print(path)


if __name__ == "__main__":
    main()
