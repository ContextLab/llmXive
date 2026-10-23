"""Save a figure together with a record of what was plotted.

A reviewer that reads files cannot look at a PNG. Tasks that asked for "a plot
with two series on a log axis" were rejected over and over for "no evidence the
image shows that" (2026-10-11: every one of nine attempts at one such task).
``save_figure`` writes the image and, next to it, ``<name>.figure.json``: the
titles, axis labels and scales, legend entries and each plotted series with
its number of points and its x and y ranges, read from the figure object that
was drawn. Nothing in the record is typed by hand.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

RECORD_SUFFIX = ".figure.json"


def record_path(image: str | os.PathLike[str]) -> Path:
    """Where the record for ``image`` lives: ``plot.png`` -> ``plot.figure.json``."""
    image = Path(image)
    return image.with_name(image.stem + RECORD_SUFFIX)


def _number(value: object) -> float | None:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _extent(values: object) -> tuple[float | None, float | None, int]:
    numbers = [n for n in (_number(v) for v in list(values)) if n is not None]  # type: ignore[call-overload]
    return (min(numbers), max(numbers), len(numbers)) if numbers else (None, None, 0)


def _series(kind: str, label: object, xs: object, ys: object) -> dict:
    x_min, x_max, _ = _extent(xs)
    y_min, y_max, count = _extent(ys)
    text = str(label or "")
    return {"kind": kind, "label": "" if text.startswith("_") else text, "points": count,
            "x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}


def describe(fig: object) -> dict:
    """What ``fig`` (a matplotlib Figure) shows, as plain data."""
    axes_out = []
    for ax in fig.get_axes():  # type: ignore[attr-defined]
        series = [_series("line", line.get_label(), line.get_xdata(), line.get_ydata())
                  for line in ax.get_lines()]
        for collection in ax.collections:
            offsets = getattr(collection, "get_offsets", lambda: [])()
            if len(offsets):
                series.append(_series("points", collection.get_label(),
                                      [p[0] for p in offsets], [p[1] for p in offsets]))
        for container in getattr(ax, "containers", []):
            patches = [p for p in getattr(container, "patches", [])]
            if patches:
                series.append(_series("bars", container.get_label(),
                                      [p.get_x() + p.get_width() / 2 for p in patches],
                                      [p.get_height() for p in patches]))
        legend = ax.get_legend()
        axes_out.append({
            "title": ax.get_title(), "xlabel": ax.get_xlabel(), "ylabel": ax.get_ylabel(),
            "xscale": ax.get_xscale(), "yscale": ax.get_yscale(),
            "legend": [text.get_text() for text in legend.get_texts()] if legend else [],
            "series": series,
        })
    title = getattr(fig, "_suptitle", None)
    return {"written_by": "llmxive_toolkit.save_figure",
            "suptitle": title.get_text() if title is not None else "", "axes": axes_out}


def save_figure(*args: object, **options: object) -> Path:
    """``save_figure(fig, path)`` or ``save_figure(path)`` (the current figure).

    Saves the image and its ``.figure.json`` record; returns the image path.
    A relative path is taken from the project directory. Other keyword
    arguments (``dpi``, ``bbox_inches``, ...) go to ``Figure.savefig``.
    """
    from llmxive_toolkit import project_root

    fig = next((a for a in args if hasattr(a, "savefig") and hasattr(a, "get_axes")), None)
    target = next((a for a in args if isinstance(a, (str, os.PathLike))), None) or options.pop("path", None)
    if target is None:
        raise TypeError("save_figure needs the path to write the image to")
    if fig is None:
        import matplotlib.pyplot as plt

        fig = plt.gcf()
    path = Path(str(target))
    if not path.is_absolute():
        path = project_root() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, **options)  # type: ignore[attr-defined]
    record = {"image": path.name, **describe(fig)}
    record_path(path).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


__all__ = ["RECORD_SUFFIX", "describe", "record_path", "save_figure"]
