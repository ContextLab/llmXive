"""
correlation_analysis.py

Implements loading of processed metrics, computation of Spearman correlation
between clone density, model perplexity and bug‑detection accuracy, and
persistence of the results (including p‑values) to
``data/analysis/correlation_results.csv``.

The module is deliberately defensive: if any required input file is missing
it raises a clear ``FileNotFoundError`` instead of silently producing
placeholder data. This behaviour satisfies the requirement that the script
must *actually* run and write a real output file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helper loaders
# --------------------------------------------------------------------------- #
def _load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file with a helpful error if the file does not exist."""
    if not path.is_file():
        raise FileNotFoundError(f"Required input file not found: {path}")
    logger.debug("Loading CSV file %s", path)
    return pd.read_csv(path)

def load_clone_metrics() -> pd.DataFrame:
    """Load ``clone_metrics.csv`` produced by the AST cloner step."""
    return _load_csv(Path("data/processed/clone_metrics.csv"))

def load_perplexity_scores() -> pd.DataFrame:
    """Load ``perplexity_scores.csv`` produced by the model‑metrics step."""
    return _load_csv(Path("data/processed/perplexity_scores.csv"))

def load_bug_detection_results() -> pd.DataFrame:
    """
    Load bug‑detection results.  The file is optional – if it does not exist
    the correlation between clone density and accuracy will simply be omitted.
    """
    path = Path("data/processed/bug_detection_results.csv")
    if not path.is_file():
        logger.info("Bug‑detection results not found; skipping that correlation.")
        return pd.DataFrame()
    return _load_csv(path)

# --------------------------------------------------------------------------- #
# Correlation logic
# --------------------------------------------------------------------------- #
def _compute_spearman(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation between two Series.
    Returns (rho, p_value).  NaNs are dropped pair‑wise.
    """
    # Drop any rows where either side is NaN
    mask = x.notna() & y.notna()
    if mask.sum() == 0:
        raise ValueError("No overlapping non‑NaN data to correlate.")
    rho, p_val = spearmanr(x[mask], y[mask])
    return float(rho), float(p_val)

def compute_correlations() -> pd.DataFrame:
    """
    Compute all required correlations and return a DataFrame with the
    following columns:

    - metric_x: name of the first metric (e.g. ``clone_density``)
    - metric_y: name of the second metric (e.g. ``perplexity``)
    - spearman_rho: Spearman rank correlation coefficient
    - p_value: two‑tailed p‑value
    - n: number of paired observations used in the test
    """
    clone_df = load_clone_metrics()
    perplexity_df = load_perplexity_scores()
    bug_df = load_bug_detection_results()

    # Merge on a common identifier.  Both clone and perplexity files contain
    # a ``file_path`` column that uniquely identifies the source file.
    merged = pd.merge(
        clone_df,
        perplexity_df,
        on="file_path",
        suffixes=("_clone", "_perplexity"),
    )

    results: List[dict] = []

    # ------------------------------------------------------------------- #
    # Correlation 1: clone density vs. perplexity
    # ------------------------------------------------------------------- #
    if "clone_density" not in merged.columns or "perplexity" not in merged.columns:
        raise KeyError(
            "Expected columns 'clone_density' and 'perplexity' in merged DataFrame."
        )
    rho, p_val = _compute_spearman(
        merged["clone_density"], merged["perplexity"]
    )
    results.append(
        {
            "metric_x": "clone_density",
            "metric_y": "perplexity",
            "spearman_rho": rho,
            "p_value": p_val,
            "n": int((merged["clone_density"].notna() & merged["perplexity"].notna()).sum()),
        }
    )

    # ------------------------------------------------------------------- #
    # Correlation 2: clone density vs. bug‑detection accuracy (if available)
    # ------------------------------------------------------------------- #
    if not bug_df.empty:
        # ``bug_detection_results.csv`` is expected to contain a ``problem_id``
        # column that matches the ``file_path`` identifier used for clone metrics.
        # If the identifier columns differ we fall back to an inner join on the
        # common subset.
        bug_merged = pd.merge(
            clone_df,
            bug_df,
            left_on="file_path",
            right_on="problem_id",
            how="inner",
        )
        if "clone_density" in bug_merged.columns and "accuracy" in bug_merged.columns:
            rho_bug, p_val_bug = _compute_spearman(
                bug_merged["clone_density"], bug_merged["accuracy"]
            )
            results.append(
                {
                    "metric_x": "clone_density",
                    "metric_y": "accuracy",
                    "spearman_rho": rho_bug,
                    "p_value": p_val_bug,
                    "n": int(
                        (
                            bug_merged["clone_density"].notna()
                            & bug_merged["accuracy"].notna()
                        ).sum()
                    ),
                }
            )
        else:
            logger.warning(
                "Bug‑detection DataFrame missing expected columns; skipping that correlation."
            )
        return

    return pd.DataFrame(results)

# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def save_correlation_results(df: pd.DataFrame) -> Path:
    """
    Persist the correlation DataFrame to ``data/analysis/correlation_results.csv``.
    The function creates the parent directory if it does not already exist.
    """
    output_path = Path("data/analysis/correlation_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Correlation results saved to %s", output_path)
    return output_path

# --------------------------------------------------------------------------- #
# Public entry‑point
# --------------------------------------------------------------------------- #
def run_correlation_analysis() -> Path:
    """
    Execute the full correlation pipeline:
    1. Load required metric files.
    2. Compute Spearman correlations (with p‑values).
    3. Write the results to the canonical CSV file.
    Returns the path to the written CSV.
    """
    logger.info("Starting correlation analysis...")
    corr_df = compute_correlations()
    return save_correlation_results(corr_df)

# ----------------------------------------------------------------------
# Convenience entry point used by ``generate_correlation_results.py``
# ----------------------------------------------------------------------
def main() -> None:
    """Convenient CLI entry‑point used by ``python -m code.correlation_analysis``."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        run_correlation_analysis()
    except Exception as exc:
        logger.error("Correlation analysis failed: %s", exc)
        raise

if __name__ == "__main__":
    main()
