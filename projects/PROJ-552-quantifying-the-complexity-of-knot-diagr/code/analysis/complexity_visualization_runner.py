"""Run-book entry: produce the declared complexity-visualization example plot.

Loads the cleaned knot census, drops non-data rows (the raw KnotInfo export
carries a human-label header row and knots with missing invariants), normalizes
the alternating flag, and renders the example figure to the path declared in
tasks.md (``data/plots/complexity_visualization_examples.png``).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from analysis.complexity_visualization import generate_complexity_visualization_examples
from reproducibility.logs import get_logger


def main() -> None:
    logger = get_logger()
    logger.info("Generating complexity visualization examples")

    df = pd.read_csv("data/processed/knots_cleaned.csv")
    # Coerce numerics and drop rows that aren't real knot data (the label row
    # and any knot missing crossing number / braid index).
    df["crossing_number"] = pd.to_numeric(df["crossing_number"], errors="coerce")
    df["braid_index"] = pd.to_numeric(df["braid_index"], errors="coerce")
    df = df.dropna(subset=["crossing_number", "braid_index"]).copy()
    df["crossing_number"] = df["crossing_number"].astype(int)
    df["braid_index"] = df["braid_index"].astype(int)
    # Normalize the alternating flag (KnotInfo encodes it as "Y"/"N") to bool.
    df["alternating"] = (
        df["alternating"].astype(str).str.strip().str.upper().isin(["Y", "YES", "TRUE", "1"])
    )

    output_path = Path("data/plots/complexity_visualization_examples.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_complexity_visualization_examples(df, output_path)
    logger.info(f"Saved plot to {output_path} ({len(df)} knots)")


if __name__ == "__main__":
    main()
