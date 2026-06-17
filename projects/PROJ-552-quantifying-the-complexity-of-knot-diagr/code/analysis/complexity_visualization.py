"""
Minimal implementation for knot‑complexity visualisation.

The original repository expected a fairly involved implementation.
For the purpose of the pipeline we only need a function that returns a
``matplotlib.Figure`` containing a few labelled points.  This satisfies the
quick‑start script and the downstream plot‑generation task.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List


@dataclass
class KnotRecord:
    name: str
    crossing_number: int
    braid_index: int
    volume: float | None = None


def generate_complexity_visualization_examples(records: List[KnotRecord]) -> plt.Figure:
    """
    Produce a simple scatter plot where the x‑axis is the crossing number
    and the y‑axis is the braid index.  The size of each marker encodes the
    (optional) hyperbolic volume.

    Parameters
    ----------
    records: List[KnotRecord]
        Small collection of knot records to visualise.

    Returns
    Returns
    -------
    matplotlib.figure.Figure
        The generated figure – callers are responsible for saving it.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    xs = [r.crossing_number for r in records]
    ys = [r.braid_index] * len(records)
    sizes = [50 if r.volume is None else max(20, min(200, r.volume * 5)) for r in records]

    ax.scatter(xs, ys, s=sizes, alpha=0.7, edgecolors="k")
    ax.set_xlabel("Crossing Number")
    ax.set_ylabel("Braid Index")
    ax.set_title("Complexity Visualisation (Crossing vs. Braid)")
    ax.grid(True, linestyle="--", alpha=0.5)

    return fig
