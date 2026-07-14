"""Correlation analysis for code duplication study.

This module loads processed metrics (clone density, perplexity scores,
bug‑detection results), computes Spearman rank correlations between relevant
pairs of metrics, and saves the results (including p‑values and sample size)
to ``data/analysis/correlation_results.csv``.

The implementation is defensive: it works even if some input files are
missing or columns have unexpected names. It logs informative messages and
only writes rows for which a valid correlation could be computed.
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
# Helper functions to load the three processed artefacts                        #
# --------------------------------------------------------------------------- #
def _load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    If the file does not exist or is empty, returns an empty DataFrame.
    """
    if not path.is_file():
        logger.warning("Expected CSV %s does not exist – returning empty DataFrame.", path)
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        if df.empty:
            logger.warning("CSV %s is empty.", path)
        return df
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to read %s: %s", path, exc)
        return pd.DataFrame()

def load_clone_metrics() -> pd.DataFrame:
    """Load ``clone_metrics.csv`` produced by the AST cloner."""
    return _load_csv(Path("data/processed/clone_metrics.csv"))

def load_perplexity_scores() -> pd.DataFrame:
    """Load ``perplexity_scores.csv`` produced by the model‑metrics step."""
    return _load_csv(Path("data/processed/perplexity_scores.csv"))

def load_bug_detection_results() -> pd.DataFrame:
    """Load ``bug_detection_results.csv`` produced by the bug‑detection step."""
    return _load_csv(Path("data/processed/bug_detection_results.csv"))

# --------------------------------------------------------------------------- #
# Core correlation logic                                                       #
# --------------------------------------------------------------------------- #
def _compute_spearman(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
    """Return (rho, p_value, n) for the Spearman correlation of two series.

    Missing values are dropped pair‑wise.
    """
    # Align the two series and drop NaNs
    df = pd.concat([x, y], axis=1).dropna()
    n = len(df)
    if n < 2:
        raise ValueError("Not enough data points to compute correlation (n < 2).")
    rho, p_val = spearmanr(df.iloc[:, 0], df.iloc[:, 1])
    return float(rho), float(p_val), n

def compute_correlations() -> List[Dict[str, Any]]:
    """Compute all required correlations.

    Returns a list of dictionaries, each describing one correlation pair.
    """
    results: List[Dict[str, Any]] = []

    # 1. Clone density ↔ Perplexity
    df_clone = load_clone_metrics()
    df_ppl = load_perplexity_scores()
    if not df_clone.empty and not df_ppl.empty:
        # Attempt to merge on a common identifier.  The most reliable column is
        # ``file_path`` if present; otherwise fall back to the first column that
        # exists in both frames.
        merge_key = None
        for candidate in ["file_path", "id", "filename"]:
            if candidate in df_clone.columns and candidate in df_ppl.columns:
                merge_key = candidate
                break
        if merge_key:
            merged = pd.merge(df_clone, df_ppl, on=merge_key, how="inner")
            if "clone_density" in merged.columns and "perplexity" in merged.columns:
                try:
                    rho, p_val, n = _compute_spearman(
                        merged["clone_density"], merged["perplexity"]
                    )
                    results.append(
                        {
                            "metric_x": "clone_density",
                            "metric_y": "perplexity",
                            "spearman_rho": rho,
                            "p_value": p_val,
                            "n": n,
                        }
                    )
                except Exception as exc:  # pragma: no cover
                    logger.error("Failed Spearman for clone↔perplexity: %s", exc)
            else:
                logger.warning(
                    "Expected columns 'clone_density' and 'perplexity' not found after merge."
                )
        else:
            logger.warning(
                "No common merge key found between clone_metrics and perplexity_scores."
            )
    else:
        logger.info("One of clone_metrics or perplexity_scores is empty – skipping that correlation.")

    # 2. Clone density ↔ Bug‑detection accuracy (pass@1)
    df_bug = load_bug_detection_results()
    if not df_clone.empty and not df_bug.empty:
        # Expected identifier columns: ``problem_id`` or ``id``.
        merge_key = None
        for candidate in ["problem_id", "id"]:
            if candidate in df_clone.columns and candidate in df_bug.columns:
                merge_key = candidate
                break
        if merge_key:
            merged = pd.merge(df_clone, df_bug, on=merge_key, how="inner")
            # The bug‑detection result column is usually called ``pass_at_1`` or ``accuracy``.
            accuracy_col = (
                "pass_at_1"
                if "pass_at_1" in merged.columns
                else ("accuracy" if "accuracy" in merged.columns else None)
            )
            if "clone_density" in merged.columns and accuracy_col:
                try:
                    rho, p_val, n = _compute_spearman(
                        merged["clone_density"], merged[accuracy_col]
                    )
                    results.append(
                        {
                            "metric_x": "clone_density",
                            "metric_y": accuracy_col,
                            "spearman_rho": rho,
                            "p_value": p_val,
                            "n": n,
                        }
                    )
                except Exception as exc:  # pragma: no cover
                    logger.error("Failed Spearman for clone↔accuracy: %s", exc)
            else:
                logger.warning(
                    "Required columns for clone↔accuracy not present after merge."
                )
        else:
            logger.warning(
                "No common merge key found between clone_metrics and bug_detection_results."
            )
    else:
        logger.info("One of clone_metrics or bug_detection_results is empty – skipping that correlation.")

    return results

# --------------------------------------------------------------------------- #
# Persistence                                                                   #
# --------------------------------------------------------------------------- #
def save_correlation_results(
    correlations: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
) -> None:
    """Write correlation results to CSV.

    The CSV has columns:
    ``metric_x,metric_y,spearman_rho,p_value,n``

    If ``correlations`` is empty, a file containing only the header is still
    written (so downstream validation knows the script ran).
    """
    out_path = output_path or Path("data/analysis/correlation_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["metric_x", "metric_y", "spearman_rho", "p_value", "n"]
    try:
        with out_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in correlations:
                # Ensure all required keys exist; missing keys are written as empty strings.
                writer.writerow(
                    {
                        key: row.get(key, "")
                        for key in fieldnames
                    }
                )
        logger.info("Correlation results saved to %s (%d rows).", out_path, len(correlations))
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to write correlation results to %s: %s", out_path, exc)
        raise

# --------------------------------------------------------------------------- #
# High‑level orchestration                                                       #
# --------------------------------------------------------------------------- #
def run_correlation_analysis() -> List[Dict[str, Any]]:
    """Compute correlations and persist them.

    Returns the list of correlation dictionaries for possible downstream use.
    """
    correlations = compute_correlations()
    save_correlation_results(correlations)
    return correlations

def main() -> None:
    """Entry‑point for ``python -m code.correlation_analysis``."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run_correlation_analysis()

if __name__ == "__main__":  # pragma: no cover
    main()
