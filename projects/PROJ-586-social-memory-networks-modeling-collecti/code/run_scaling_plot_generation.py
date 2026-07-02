"""Aggregate scaling experiment results and generate a PDF plot."""
from __future__ import annotations

import argparse
import pathlib
from pathlib import Path
from typing import List

import pandas as pd

from analysis.scaling import generate_scaling_plot

# Directory where individual experiment CSVs are stored.
RESULTS_DIR = Path(
    "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
)
AGGREGATED_CSV = RESULTS_DIR / "aggregated_scaling_data.csv"
OUTPUT_PDF = RESULTS_DIR / "scaling_plot.pdf"


def _find_result_files() -> List[Path]:
    """Return a list of CSV result files matching the expected naming scheme."""
    pattern = "results_*.csv"
    return sorted(RESULTS_DIR.glob(pattern))


def aggregate_scaling_data() -> pd.DataFrame:
    """
    Read all per‑condition CSV files, concatenate them, and compute mean metrics
    for each ``agent_count`` value.

    The aggregated DataFrame is written to ``AGGREGATED_CSV`` for reproducibility.
    """
    csv_files = _find_result_files()
    if not csv_files:
        raise FileNotFoundError(f"No result CSVs found in {RESULTS_DIR}")

    dfs = []
    for fp in csv_files:
        df = pd.read_csv(fp)
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)

    # Expected columns (as produced by run_experiment.py):
    #   game_id, specialization_index, retrieval_efficiency,
    #   context_condition, agent_count
    required = {
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    }
    missing = required - set(combined.columns)
    if missing:
        raise ValueError(f"Missing required columns in combined data: {missing}")

    # Compute mean values per agent count (and optionally per context)
    agg = (
        combined.groupby(["agent_count", "context_condition"])
        .agg(
            {
                "specialization_index": "mean",
                "retrieval_efficiency": "mean",
            }
        )
        .reset_index()
    )

    AGGREGATED_CSV.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(AGGREGATED_CSV, index=False)
    return agg


def main(argv: List[str] | None = None) -> int:
    """CLI entry point used by the quickstart script."""
    parser = argparse.ArgumentParser(
        description="Aggregate scaling results and produce a PDF plot."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing aggregated CSV and PDF if they exist.",
    )
    args = parser.parse_args(argv)

    if AGGREGATED_CSV.is_file() and not args.force:
        agg_df = pd.read_csv(AGGREGATED_CSV)
    else:
        agg_df = aggregate_scaling_data()

    # Generate the plot – the function handles saving to OUTPUT_PDF.
    generate_scaling_plot(agg_df, output_path=OUTPUT_PDF)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
