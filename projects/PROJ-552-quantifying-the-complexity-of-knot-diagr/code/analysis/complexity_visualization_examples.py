"""
Generate a simple example visualization for knot‑complexity mapping.

The original script was missing or broken, causing the quick‑start run‑book to
fail.  This implementation creates a synthetic scatter plot that maps the
crossing number to the braid index for a small subset of knots and saves the
figure to the declared location ``data/plots/complexity_visualization_examples.png``.
The plot is deliberately simple but fully functional and reproducible.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation
from pathlib import Path

def main() -> None:
    logger = get_logger(__name__)
    log_operation("complexity_visualization_examples_start", parameters={})

    df = load_cleaned_knots()
    # Use a modest subset to keep the plot readable
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

if __name__ == "__main__":
    main()
