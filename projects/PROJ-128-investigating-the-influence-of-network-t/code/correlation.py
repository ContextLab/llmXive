"""
correlation.py
----------------
Skeleton module for performing statistical correlation analysis between structural
graph metrics and dynamic functional metrics.

This module provides a high‑level ``main`` function that can be invoked from the
command line (``python -m code.correlation``) or imported by other pipeline scripts.
It leverages the existing implementations in ``analysis.correlation`` for the
actual statistical calculations (normality testing, Pearson/Spearman correlation,
and Benjamini‑Hochberg FDR correction).

The script follows the project conventions:
  * Input files are read from ``data/processed``.
  * Output file ``correlation_results.csv`` is written to ``data/processed``.
  * Paths are constructed using the ``llmxive_toolkit.paths`` helpers, which
    automatically create parent directories when needed.
"""

import sys
import json
from pathlib import Path

import pandas as pd

# Project‑wide path helpers
from llmxive_toolkit import paths, get_logger

# Re‑use the analysis utilities that implement the core statistical logic
from analysis.correlation import run_correlation_analysis

log = get_logger(__name__)

def _load_metrics(structural_path: Path, dynamic_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the structural and dynamic metric CSV files.

    Parameters
    ----------
    structural_path : Path
        Path to ``structural_metrics.csv``.
    dynamic_path : Path
        Path to ``dynamic_metrics.csv``.

    Returns
    -------
    tuple[DataFrame, DataFrame]
        (structural_metrics, dynamic_metrics) dataframes indexed by ``subject_id``.
    """
    if not structural_path.is_file():
        raise FileNotFoundError(f"Structural metrics file not found: {structural_path}")
    if not dynamic_path.is_file():
        raise FileNotFoundError(f"Dynamic metrics file not found: {dynamic_path}")

    structural_df = pd.read_csv(structural_path)
    dynamic_df = pd.read_csv(dynamic_path)

    # Ensure ``subject_id`` exists and set it as the index for easier merging later
    if "subject_id" not in structural_df.columns:
        raise KeyError("Column 'subject_id' missing from structural metrics CSV")
    if "subject_id" not in dynamic_df.columns:
        raise KeyError("Column 'subject_id' missing from dynamic metrics CSV")

    structural_df = structural_df.set_index("subject_id")
    dynamic_df = dynamic_df.set_index("subject_id")
    return structural_df, dynamic_df

def _save_results(results_df: pd.DataFrame, output_path: Path) -> None:
    """
    Persist the correlation results to CSV.

    Parameters
    ----------
    results_df : DataFrame
        Dataframe produced by ``run_correlation_analysis``.
    output_path : Path
        Destination CSV file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    log.info(f"Correlation results saved to {output_path}")

def main() -> None:
    """
    Entry point for the correlation analysis step.

    The function performs the following actions:
      1. Resolve input and output paths using ``llmxive_toolkit.paths``.
      2. Load structural and dynamic metrics.
      3. Run the correlation analysis (normality → method selection → correlation → FDR).
      4. Write the resulting table to ``data/processed/correlation_results.csv``.
    """
    # Resolve standard locations
    structural_path = paths.data("processed", "structural_metrics.csv")
    dynamic_path = paths.data("processed", "dynamic_metrics.csv")
    output_path = paths.data("processed", "correlation_results.csv")

    log.info("Starting correlation analysis")
    log.debug(f"Structural metrics path: {structural_path}")
    log.debug(f"Dynamic metrics path: {dynamic_path}")

    try:
        structural_df, dynamic_df = _load_metrics(structural_path, dynamic_path)
    except Exception as e:
        log.error(f"Failed to load input metrics: {e}")
        raise

    # Perform the statistical analysis
    try:
        results_df = run_correlation_analysis(
            structural_metrics=structural_df,
            dynamic_metrics=dynamic_df,
            alpha=0.05,
            fdr_q=0.05,
        )
    except Exception as e:
        log.error(f"Correlation analysis failed: {e}")
        raise

    # Save the results
    _save_results(results_df, output_path)

    log.info("Correlation analysis completed successfully")

if __name__ == "__main__":
    # When executed as a script ``python -m code.correlation`` we simply call main()
    sys.exit(main())