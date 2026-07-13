"""Correlation analysis module.

This module provides utilities to compute Spearman correlation between
different metrics produced by the pipeline (e.g., clone density vs.
perplexity, clone density vs. bug‑detection accuracy) and to persist the
results to ``data/analysis/correlation_results.csv``.

The implementation is defensive: if any of the expected input files are
missing, the functions fall back to empty DataFrames and still write a CSV
with the appropriate header so downstream validation does not crash.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helper functions to load the various metric CSVs produced by earlier stages #
# --------------------------------------------------------------------------- #

def _load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file safely.

    Returns an empty DataFrame if the file does not exist or cannot be read.
    """
    if not path.is_file():
        logger.warning("Expected CSV %s not found – returning empty DataFrame", path)
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to read %s: %s", path, exc)
        return pd.DataFrame()

def load_clone_metrics() -> pd.DataFrame:
    """Load ``clone_metrics.csv`` produced by ``ast_cloner``."""
    return _load_csv(Path("data/processed/clone_metrics.csv"))

def load_perplexity_scores() -> pd.DataFrame:
    """Load ``perplexity_scores.csv`` produced by ``model_metrics``."""
    return _load_csv(Path("data/processed/perplexity_scores.csv"))

def load_bug_detection_results() -> pd.DataFrame:
    """Load bug‑detection results (pass@1 accuracy) if they exist."""
    return _load_csv(Path("data/processed/bug_detection_results.csv"))

# --------------------------------------------------------------------------- #
# Core correlation logic                                                       #
# --------------------------------------------------------------------------- #

def compute_spearman_correlation(
    x: pd.Series, y: pd.Series
) -> Tuple[float, float]:
    """Compute Spearman rank correlation between two series.

    Returns a tuple ``(correlation, p_value)``. If either series is empty,
    ``(float('nan'), float('nan'))`` is returned.
    """
    if x.empty or y.empty:
        logger.warning("Empty series supplied to compute_spearman_correlation")
        return float("nan"), float("nan")
    # Drop NaNs pair‑wise to avoid scipy warnings
    valid = pd.concat([x, y], axis=1).dropna()
    if valid.empty:
        logger.warning("All values are NaN after dropping – returning NaNs")
        return float("nan"), float("nan")
    corr, pval = spearmanr(valid.iloc[:, 0], valid.iloc[:, 1])
    return float(corr), float(pval)

# --------------------------------------------------------------------------- #
# Persisting results                                                          #
# --------------------------------------------------------------------------- #

def save_correlation_results(
    results: List[Tuple[str, str, float, float, int]],
    output_path: Path = Path("data/analysis/correlation_results.csv"),
) -> None:
    """Write correlation results to ``output_path``.

    ``results`` is a list of tuples:
    ``(metric_x, metric_y, spearman, p_value, n_samples)``.

    The CSV will contain the following columns:
    ``metric_x, metric_y, spearman, p_value, n_samples``.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(
            ["metric_x", "metric_y", "spearman", "p_value", "n_samples"]
        )
        for row in results:
            writer.writerow(row)
    logger.info("Correlation results saved to %s", output_path)

# --------------------------------------------------------------------------- #
# End‑to‑end pipeline entry point                                            #
# --------------------------------------------------------------------------- #

def run_correlation_analysis() -> None:
    """Run the full correlation analysis pipeline.

    1. Load clone density, perplexity, and bug‑detection results.
    2. Merge on a common identifier (``file_id`` or ``problem_id``).  The
       merge strategy is tolerant: rows missing in any source are dropped.
    3. Compute two correlations:
         * clone density vs. perplexity
         * clone density vs. pass@1 accuracy
    4. Persist the results to ``data/analysis/correlation_results.csv``.
    """
    clone_df = load_clone_metrics()
    perp_df = load_perplexity_scores()
    bug_df = load_bug_detection_results()

    if clone_df.empty:
        logger.error("Clone metrics are missing – aborting correlation analysis")
        return

    # Determine join key(s).  The original pipeline used ``file_id`` for clone
    # and perplexity and ``problem_id`` for bug detection.  We attempt both.
    join_key_candidates = ["file_id", "problem_id"]
    merged = None
    for key in join_key_candidates:
        if key in clone_df.columns and key in perp_df.columns:
            merged = clone_df.merge(perp_df, on=key, suffixes=("_clone", "_perp"))
            break
    if merged is None:
        logger.error(
            "Could not find a common join key between clone and perplexity data."
        )
        return

    # If bug detection data is available, merge it as well.
    if not bug_df.empty:
        # Prefer the same key if present; otherwise use ``problem_id``.
        bug_key = "problem_id" if "problem_id" in bug_df.columns else None
        if bug_key and bug_key in merged.columns:
            merged = merged.merge(bug_df, on=bug_key, suffixes=("", "_bug"))
        else:
            logger.warning(
                "Bug detection data could not be merged – skipping that correlation."
            )

    results: List[Tuple[str, str, float, float, int]] = []

    # Correlation 1: clone density vs. perplexity
    if "clone_density" in merged.columns and "perplexity" in merged.columns:
        corr, pval = compute_spearman_correlation(
            merged["clone_density"], merged["perplexity"]
        )
        n = int(merged[["clone_density", "perplexity"]].dropna().shape[0])
        results.append(("clone_density", "perplexity", corr, pval, n))
    else:
        logger.warning(
            "Required columns for clone‑perplexity correlation not found."
        )

    # Correlation 2: clone density vs. pass@1 accuracy (if available)
    if "clone_density" in merged.columns and "pass@1_accuracy" in merged.columns:
        corr, pval = compute_spearman_correlation(
            merged["clone_density"], merged["pass@1_accuracy"]
        )
        n = int(
            merged[["clone_density", "pass@1_accuracy"]].dropna().shape[0]
        )
        results.append(
            ("clone_density", "pass@1_accuracy", corr, pval, n)
        )
    else:
        logger.info(
            "Bug‑detection accuracy column not present – only clone‑perplexity correlation saved."
        )

    save_correlation_results(results)

# --------------------------------------------------------------------------- #
# Convenience entry point for ``python -m code.correlation_analysis``          #
# --------------------------------------------------------------------------- #

def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_correlation_analysis()

if __name__ == "__main__":  # pragma: no cover
    main()
