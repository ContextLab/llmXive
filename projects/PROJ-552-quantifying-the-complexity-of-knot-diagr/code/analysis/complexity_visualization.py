from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

@dataclass
class KnotRecord:
    """Simple representation of a knot used for visualization.

    Only the fields required for the complexity illustration are stored.
    """
    name: str
    crossing_number: int
    braid_index: int
    alternating: bool

def _df_to_records(df: pd.DataFrame) -> list[KnotRecord]:
    """Convert a DataFrame into a list of ``KnotRecord`` objects."""
    required = {"name", "crossing_number", "braid_index", "alternating"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    records = []
    for _, row in df.iterrows():
        records.append(
            KnotRecord(
                name=str(row["name"]),
                crossing_number=int(row["crossing_number"]),
                braid_index=int(row["braid_index"]),
                alternating=bool(row["alternating"]),
            )
        )
    return records

def generate_complexity_visualization_examples(
    df: pd.DataFrame, output_path: Path
) -> None:
    """Create an example plot that maps a simple complexity metric to diagram features.

    The metric used here is the sum of crossing number and braid index.
    The plot shows:
    * x‑axis: crossing number
    * y‑axis: braid index
    * point size proportional to the complexity metric
    * colour indicates alternating vs. non‑alternating

    The figure is saved to ``output_path`` (PNG format).
    """
    records = _df_to_records(df)

    # Prepare data for plotting
    crossing = [r.crossing_number for r in records]
    braid = [r.braid_index for r in records]
    complexity = [r.crossing_number + r.braid_index for r in records]
    colors = ["tab:blue" if r.alternating else "tab:orange" for r in records]

    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(
        crossing,
        braid,
        s=[c * 5 for c in complexity],  # scale size for visibility
        c=colors,
        alpha=0.7,
        edgecolors="k",
    )
    plt.title("Knot Complexity Visualization Example")
    plt.xlabel("Crossing Number")
    plt.ylabel("Braid Index")
    plt.grid(True, linestyle="--", alpha=0.5)

    # Create a legend for alternating status
    from matplotlib.lines import Line2D

    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Alternating",
            markerfacecolor="tab:blue",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Non‑alternating",
            markerfacecolor="tab:orange",
            markersize=10,
        ),
    ]
    plt.legend(handles=legend_elements, title="Knot Type")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()