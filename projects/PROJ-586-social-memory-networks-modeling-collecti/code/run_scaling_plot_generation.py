"""Run scaling plot generation.

This script aggregates the metric results produced by the scaling
experiments (typically ``results_full.csv`` and ``results_limited.csv`` or
any ``results_*.csv`` files in the project ``results`` directory) and
generates a PDF containing the scaling curves with fitted power‑law
relationships.  A short explanatory note is added to the figure to make
clear that only three data points are available, limiting the reliability
of the fit.

The script is deliberately lightweight and has no external side‑effects
besides writing the PDF to the expected location:
    projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf
"""

from __future__ import annotations

import pathlib
import sys
from typing import List

import pandas as pd

# Local import – the function that actually creates the figure.
from analysis.scaling_plot_generator import generate_scaling_plot_with_notes


def _collect_result_files(results_dir: pathlib.Path) -> List[pathlib.Path]:
    """Return a list of CSV files that contain scaling metrics.

    The scaling experiments write CSV files with names that contain the
    word ``results``.  We accept any ``*.csv`` file that contains the
    columns ``agent_count``, ``specialization_index`` and
    ``retrieval_efficiency``.
    """
    csv_files = list(results_dir.glob("*.csv"))
    valid_files = []
    required_cols = {"agent_count", "specialization_index", "retrieval_efficiency"}

    for f in csv_files:
        try:
            df = pd.read_csv(f, nrows=0)
            if required_cols.issubset(set(df.columns)):
                valid_files.append(f)
        except Exception:
            # Skip files that cannot be parsed as CSV.
            continue
    return valid_files


def _merge_results(csv_paths: List[pathlib.Path]) -> pd.DataFrame:
    """Concatenate the metric CSVs into a single DataFrame."""
    dfs = [pd.read_csv(p) for p in csv_paths]
    if not dfs:
        raise FileNotFoundError("No valid scaling result CSV files found.")
    merged = pd.concat(dfs, ignore_index=True)
    # Drop possible duplicate rows (e.g., if the same experiment was run twice)
    merged = merged.drop_duplicates(subset=["agent_count", "specialization_index", "retrieval_efficiency"])
    return merged


def main(argv: list[str] | None = None) -> int:
    """Entry point used by the quick‑start validation and CI.

    Returns:
        0 on success, non‑zero on failure.
    """
    if argv is None:
        argv = sys.argv[1:]

    # The results directory is fixed by the project specification.
    project_root = pathlib.Path(__file__).resolve().parents[1]
    results_dir = project_root / "results"

    try:
        csv_paths = _collect_result_files(results_dir)
        merged_df = _merge_results(csv_paths)
    except Exception as e:
        print(f"[run_scaling_plot_generation] Error collecting results: {e}", file=sys.stderr)
        return 1

    # Write a temporary combined CSV – the plotting function expects a CSV path.
    combined_csv_path = results_dir / "scaling_data_combined.csv"
    merged_df.to_csv(combined_csv_path, index=False)

    output_pdf_path = results_dir / "scaling_plot.pdf"

    try:
        generate_scaling_plot_with_notes(
            input_csv_path=str(combined_csv_path),
            output_pdf_path=str(output_pdf_path),
        )
    except Exception as e:
        print(f"[run_scaling_plot_generation] Plot generation failed: {e}", file=sys.stderr)
        return 1

    print(f"Scaling plot written to {output_pdf_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
