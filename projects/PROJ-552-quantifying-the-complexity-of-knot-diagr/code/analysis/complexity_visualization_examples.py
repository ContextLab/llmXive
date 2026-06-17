"""Generate example visualizations that map a simple knot complexity metric
to basic diagram features.

This script is part of task **T068**. It reads the cleaned knot dataset,
computes a rudimentary complexity score (crossing number multiplied by braid
index), and produces a scatter‑plot visualisation saved to
``data/plots/complexity_visualization_examples.png``.

The implementation is deliberately self‑contained and does **not** rely on
the project's global ``reproducibility.logs`` utilities, which were
identified as a source of failures in earlier pipeline runs.  Standard
library logging is used instead.
"""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

__all__ = [
    "generate_complexity_visualization_examples",
    "main",
]


def _setup_logger() -> logging.Logger:
    """Create a simple console logger.

    The project’s ``reproducibility.logs`` module currently has an
    incompatible signature; using the standard library avoids that issue.
    """
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def generate_complexity_visualization_examples(
    cleaned_csv: Path,
    output_png: Path,
) -> None:
    """
    Create a figure that visualises a simple complexity metric against
    diagram features.

    Parameters
    ----------
    cleaned_csv: Path
        Path to ``data/processed/knots_cleaned.csv`` containing at least the
        columns ``crossing_number`` and ``braid_index``.
    output_png: Path
        Destination path for the generated PNG image. Parent directories are
        created automatically.

    The function computes the metric::

        complexity = crossing_number * braid_index

    and produces a two‑panel scatter plot:
    * Panel 1 – complexity vs. crossing number
    * Panel 2 – complexity vs. braid index

    The figure size is 12 × 8 inches (1200 × 800 px at 100 dpi) to satisfy the
    specification.
    """
    logger = _setup_logger()
    logger.info("Loading cleaned knot data from %s", cleaned_csv)

    if not cleaned_csv.is_file():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_csv}")

    df = pd.read_csv(cleaned_csv)

    required_cols = {"crossing_number", "braid_index"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in cleaned data: {missing}")

    # Ensure numeric types
    df["crossing_number"] = pd.to_numeric(df["crossing_number"], errors="coerce")
    df["braid_index"] = pd.to_numeric(df["braid_index"], errors="coerce")

    # Drop rows where either field is missing
    before = len(df)
    df = df.dropna(subset=["crossing_number", "braid_index"])
    after = len(df)
    logger.info("Dropped %d rows with missing invariants", before - after)

    # Compute a simple complexity metric
    df["complexity"] = df["crossing_number"] * df["braid_index"]

    logger.info("Generating scatter plot")
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), constrained_layout=True)

    # Complexity vs. crossing number
    axes[0].scatter(df["crossing_number"], df["complexity"], alpha=0.6, s=20, c="steelblue")
    axes[0].set_xlabel("Crossing Number")
    axes[0].set_ylabel("Complexity (crossing × braid)")
    axes[0].set_title("Complexity vs. Crossing Number")

    # Complexity vs. braid index
    axes[1].scatter(df["braid_index"], df["complexity"], alpha=0.6, s=20, c="darkorange")
    axes[1].set_xlabel("Braid Index")
    axes[1].set_ylabel("Complexity (crossing × braid)")
    axes[1].set_title("Complexity vs. Braid Index")

    # Save the figure
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=100)
    plt.close(fig)
    logger.info("Complexity visualisation saved to %s", output_png)


def main() -> None:
    """Entry‑point for ``python -m code.analysis.complexity_visualization_examples``."""
    project_root = Path(__file__).resolve().parents[3]  # repository root
    cleaned_csv = project_root / "data" / "processed" / "knots_cleaned.csv"
    output_png = project_root / "data" / "plots" / "complexity_visualization_examples.png"

    generate_complexity_visualization_examples(cleaned_csv, output_png)


if __name__ == "__main__":
    main()
