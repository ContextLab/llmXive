"""Correlation analysis utilities.

This module loads the three metric CSV files produced by the earlier
pipeline stages, computes Spearman rank correlations between:
  * clone_density ↔ perplexity
  * clone_density ↔ pass_at_1 (bug‑detection accuracy)

The results are written to ``data/analysis/correlation_results.csv`` and
also returned as a list of dictionaries for programmatic use.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helper loaders
# --------------------------------------------------------------------------- #
def _load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    Returns an empty DataFrame if the file does not exist or is empty.
    """
    if not path.is_file():
        logger.warning("CSV file %s does not exist – returning empty DataFrame", path)
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        if df.empty:
            logger.warning("CSV file %s is empty", path)
        return df
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to read %s: %s", path, exc)
        return pd.DataFrame()

def load_clone_metrics() -> pd.DataFrame:
    """Load ``clone_metrics.csv`` from the processed data directory."""
    return _load_csv(Path("data/processed/clone_metrics.csv"))

def load_perplexity_scores() -> pd.DataFrame:
    """Load ``perplexity_scores.csv`` from the processed data directory."""
    return _load_csv(Path("data/processed/perplexity_scores.csv"))

def load_bug_detection_results() -> pd.DataFrame:
    """Load ``bug_detection_results.csv`` from the processed data directory."""
    return _load_csv(Path("data/processed/bug_detection_results.csv"))

# --------------------------------------------------------------------------- #
# Core correlation logic
# --------------------------------------------------------------------------- #
def _compute_spearman(
    x: pd.Series, y: pd.Series
) -> Tuple[float, float, int]:
    """Compute Spearman rank correlation between two Series.

    Returns ``(rho, p_value, n)`` where ``n`` is the number of
    non‑NaN paired observations.
    """
    # Drop NaNs pairwise
    valid = pd.concat([x, y], axis=1).dropna()
    n = len(valid)
    if n == 0:
        logger.warning("No overlapping data for correlation computation")
        return float("nan"), float("nan"), 0
    rho, p = spearmanr(valid.iloc[:, 0], valid.iloc[:, 1])
    return float(rho), float(p), n

def compute_correlations() -> List[Dict[str, Any]]:
    """Compute the required Spearman correlations.

    Returns a list of dictionaries, each containing:
        * metric_x
        * metric_y
        * spearman_rho
        * p_value
        * n
    """
    clone_df = load_clone_metrics()
    perp_df = load_perplexity_scores()
    bug_df = load_bug_detection_results()

    results: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------- #
    # clone_density ↔ perplexity
    # ------------------------------------------------------------------- #
    if not clone_df.empty and not perp_df.empty:
        merged = pd.merge(
            clone_df[["file_path", "clone_density"]],
            perp_df[["file_path", "perplexity"]],
            on="file_path",
            how="inner",
        )
        if not merged.empty:
            rho, p, n = _compute_spearman(
                merged["clone_density"], merged["perplexity"]
            )
            results.append(
                {
                    "metric_x": "clone_density",
                    "metric_y": "perplexity",
                    "spearman_rho": rho,
                    "p_value": p,
                    "n": n,
                }
            )
        else:
            logger.info("No overlapping rows for clone ↔ perplexity correlation.")
    else:
        logger.info("Missing clone or perplexity data – skipping that correlation.")

    # ------------------------------------------------------------------- #
    # clone_density ↔ pass_at_1
    # ------------------------------------------------------------------- #
    if not clone_df.empty and not bug_df.empty:
        # ``bug_detection_results`` uses ``problem_id`` as the identifier.
        merged = pd.merge(
            clone_df[["file_path", "clone_density"]],
            bug_df[["problem_id", "pass_at_1"]],
            left_on="file_path",
            right_on="problem_id",
            how="inner",
        )
        if not merged.empty:
            rho, p, n = _compute_spearman(
                merged["clone_density"], merged["pass_at_1"]
            )
            results.append(
                {
                    "metric_x": "clone_density",
                    "metric_y": "pass_at_1",
                    "spearman_rho": rho,
                    "p_value": p,
                    "n": n,
                }
            )
        else:
            logger.info("No overlapping rows for clone ↔ pass_at_1 correlation.")
    else:
        logger.info("Missing clone or bug‑detection data – skipping that correlation.")

    return results

# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def save_correlation_results(correlations: List[Dict[str, Any]]) -> None:
    """Write the correlation results to ``data/analysis/correlation_results.csv``.

    The output CSV has the columns:
    ``metric_x, metric_y, spearman_rho, p_value, n``.
    """
    out_path = Path("data/analysis/correlation_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "metric_x",
        "metric_y",
        "spearman_rho",
        "p_value",
        "n",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in correlations:
            # Ensure values are serialisable as strings
            writer.writerow(
                {
                    "metric_x": row["metric_x"],
                    "metric_y": row["metric_y"],
                    "spearman_rho": f"{row['spearman_rho']}",
                    "p_value": f"{row['p_value']}",
                    "n": f"{row['n']}",
                }
            )
    logger.info("Correlation results written to %s", out_path)

# --------------------------------------------------------------------------- #
# Orchestration helpers
# --------------------------------------------------------------------------- #
def run_correlation_analysis() -> List[Dict[str, Any]]:
    """Convenience wrapper that computes and persists correlation results."""
    correlations = compute_correlations()
    save_correlation_results(correlations)
    return correlations

def main() -> None:  # pragma: no cover
    """Entry‑point used by the quick‑start scripts."""
    logging.basicConfig(level=logging.INFO)
    run_correlation_analysis()

if __name__ == "__main__":  # pragma: no cover
    main()