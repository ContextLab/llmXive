"""
Consolidated visualization module.

This module merges the functionality previously spread across:
  - complexity_visualization.py
  - complexity_visualization_examples.py
  - complexity_visualization_runner.py

It provides:
  * ``KnotRecord`` – a lightweight data container.
  * ``generate_complexity_visualization_examples`` – creates a scatter plot
    of crossing number vs. braid index for a given iterable of ``KnotRecord``.
  * ``run_examples`` – loads a real dataset, draws a simple scatter plot,
    and writes the figure to ``data/plots/complexity_visualization_examples.png``.
  * ``main`` – entry‑point used by the original runner; it samples the full
    cleaned dataset, converts rows to ``KnotRecord`` objects, and calls the
    generator above.

All functions use the tolerant logging utilities from ``code.reproducibility.logs``.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation


@dataclass
class KnotRecord:
    """Simple container for a knot record used in visualizations."""
    identifier: str
    crossing_number: int
    braid_index: int
    hyperbolic_volume: float
    alternating: bool


def generate_complexity_visualization_examples(
    knots: Iterable[KnotRecord],
    output_dir: Path | str = "data/plots",
) -> None:
    """
    Produce a minimal illustrative plot showing crossing number vs. braid index.

    Parameters
    ----------
    knots: Iterable[KnotRecord]
        Collection of knot records to visualise.
    output_dir: Path | str, optional
        Destination directory for the generated PNG (default: ``data/plots``).
    """
    logger = get_logger(__name__)
    log_operation("generate_complexity_visualization_start", parameters={"count": len(list(knots))})

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build a DataFrame from the KnotRecord objects.
    df = pd.DataFrame(
        [
            {
                "identifier": k.identifier,
                "crossing_number": k.crossing_number,
                "braid_index": k.braid_index,
            }
            for k in knots
        ]
    )

    plt.figure(figsize=(6, 4))
    plt.scatter(df["crossing_number"], df["braid_index"], alpha=0.6)
    plt.title("Crossing Number vs. Braid Index (examples)")
    plt.xlabel("Crossing Number")
    plt.ylabel("Braid Index")
    plt.grid(True)
    plt.tight_layout()

    out_file = output_path / "example.png"
    plt.savefig(out_file)
    plt.close()

    log_operation(
        "generate_complexity_visualization_complete",
        output_file=str(out_file),
        status="completed",
    )
    logger.info("Complexity visualization saved to %s", out_file)


def run_examples() -> None:
    """
    Load a modest subset of the real cleaned dataset and generate a
    scatter plot saved as ``complexity_visualization_examples.png``.

    This mirrors the behavior of the original ``complexity_visualization_examples.py`` script.
    """
    logger = get_logger(__name__)
    log_operation("complexity_visualization_examples_start", parameters={})

    df = load_cleaned_knots()
    # Use a modest subset to keep the plot readable.
    sample = df[["crossing_number", "braid_index"]].dropna().head(200)

    plt.figure(figsize=(8, 6))
    plt.scatter(
        sample["crossing_number"],
        sample["braid_index"],
        alpha=0.6,
        edgecolor="k",
        linewidth=0.5,
    )
    plt.title("Crossing Number vs. Braid Index (sample)")
    plt.xlabel("Crossing Number")
    plt.ylabel("Braid Index")
    plt.grid(True, linestyle="--", alpha=0.5)

    out_path = Path("data/plots/complexity_visualization_examples.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()

    log_operation(
        "complexity_visualization_examples_complete",
        output_file=str(out_path),
        status="completed",
    )
    logger.info("Example visualization saved to %s", out_path)


def main() -> None:
    """
    Entry‑point used by the original ``complexity_visualization_runner.py``.

    It loads the full cleaned dataset, takes a small random sample,
    converts rows to ``KnotRecord`` objects, and delegates to
    ``generate_complexity_visualization_examples``.
    """
    logger = get_logger(__name__)
    log_operation("complexity_visualization_main_start", parameters={})

    df = load_cleaned_knots()
    sample = df.sample(n=min(20, len(df)), random_state=42)

    knots = [
        KnotRecord(
            identifier=row["knot_name"],
            crossing_number=row["crossing_number"],
            braid_index=row["braid_index"],
            hyperbolic_volume=row["hyperbolic_volume"],
            alternating=row["alternating"],
        )
        for _, row in sample.iterrows()
    ]

    generate_complexity_visualization_examples(knots)
    log_operation("complexity_visualization_main_complete", status="completed")
    logger.info("Visualization pipeline completed.")

if __name__ == "__main__":
    main()