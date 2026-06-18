"""
Complexity‑visualization utilities.

The original module provided data structures and a function to generate
example visualizations.  For the reproducibility pipeline a ``main``
entry‑point is required (it is imported as ``viz_main`` in several
scripts).  The implementation below adds a lightweight ``main`` that
delegates to ``generate_complexity_visualization_examples``.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

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
    Produce a few illustrative plots showing how the chosen invariants
    relate to each other.

    The function is deliberately minimal – it creates a scatter plot of
    crossing number vs. braid index and saves it as ``example.png``.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

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
    plt.savefig(output_path / "example.png")
    plt.close()

# ----------------------------------------------------------------------
# Main entry‑point required by ``code/analysis/complexity_visualization_runner.py``
# ----------------------------------------------------------------------
def main() -> None:
    """
    Load a small sample of knots and generate the example visualizations.

    This entry‑point is deliberately lightweight – it re‑uses the
    ``load_cleaned_knots`` helper from ``analysis._utils`` to obtain the
    dataset, samples a few rows, and calls the generator.
    """
    from analysis._utils import load_cleaned_knots

    # Load the full cleaned dataset and take a modest sample.
    df = load_cleaned_knots()
    sample = df.sample(n=min(20, len(df)), random_state=42)

    # Convert rows to ``KnotRecord`` instances.
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

if __name__ == "__main__":
    main()
