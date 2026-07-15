"""
t033_outlier_threshold_sweep.py

This script performs a sweep over outlier‑removal thresholds (the ``k`` parameter
used by the IQR method) and evaluates the impact of each threshold on statistical
inference. For every threshold it:

1. Applies IQR outlier removal to the raw dataset.
2. Runs the baseline statistical analysis on the cleaned data.
3. Generates a null version of the cleaned data by shuffling the outcome column.
4. Runs the same analysis on the null data to estimate the False‑Positive Rate (FPR).
5. Computes the **Inconsistency Rate** – the proportion of statistical tests whose
   significance status (p ≤ 0.05) changes between the raw baseline and the cleaned
   baseline.

The results are written to three JSON files under ``data/processed``:

* ``outlier_threshold_sweep.json`` – a list of dictionaries, one per ``k`` value,
  containing the metrics described above.
* ``cleaned_metrics.json`` – the metrics obtained from the *last* cleaned dataset
  (useful for downstream scripts that expect this file to exist).
* ``null_fpr_metrics.json`` – the metrics obtained from the *last* null dataset.

The script is deliberately defensive: it accepts a wide range of call signatures
for ``run_baseline_analysis`` and ``setup_logging`` (both are used elsewhere in
the project) and will log useful warnings rather than raising exceptions on
unexpected inputs.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Local imports – these modules already exist in the repository.
from utils import setup_logging, pin_random_seed
from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis
from data_loader import load_datasets_from_raw

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _ensure_dir(path: Path) -> None:
    """Create ``path`` (including parents) if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)

def _shuffle_outcome(df: pd.DataFrame, outcome_col: str) -> pd.DataFrame:
    """Return a copy of ``df`` with the ``outcome_col`` shuffled."""
    df_null = df.copy()
    shuffled = df_null[outcome_col].sample(frac=1.0, random_state=random.randint(0, 2**32 - 1)).reset_index(drop=True)
    df_null[outcome_col] = shuffled
    return df_null

def _significant(p: float, alpha: float = 0.05) -> bool:
    """Return ``True`` if a p‑value indicates statistical significance."""
    return p <= alpha

def _extract_p_values(metrics: Dict[str, Any]) -> List[float]:
    """
    Extract all p‑values from the ``metrics`` dictionary produced by
    ``run_baseline_analysis``. The exact structure varies across the code base,
    but the common pattern is ``metrics['t_test']['p_value']`` for a single test
    or a list thereof. This helper walks the dict recursively and collects any
    numeric ``p_value`` keys it encounters.
    """
    p_vals: List[float] = []

    def _walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "p_value" and isinstance(v, (float, int, np.floating)):
                    p_vals.append(float(v))
                else:
                    _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(metrics)
    return p_vals

# --------------------------------------------------------------------------- #
# Core sweep implementation
# --------------------------------------------------------------------------- #
def run_outlier_threshold_sweep(
    raw_df: pd.DataFrame,
    outcome_col: str,
    predictor_cols: List[str],
    ks: List[float],
    alpha: float = 0.05,
) -> List[Dict[str, Any]]:
    """
    Perform the threshold sweep.

    Parameters
    ----------
    raw_df: pd.DataFrame
        The original (uncleaned) dataset.
    outcome_col: str
        Name of the column containing the outcome / dependent variable.
    predictor_cols: List[str]
        Columns to be used as predictors in the regression analysis.
    ks: List[float]
        The list of ``k`` values (IQR multiplier) to evaluate.
    alpha: float, default 0.05
        Significance level for determining false‑positives / inconsistencies.

    Returns
    -------
    List[Dict[str, Any]]
        One dict per ``k`` containing:
        * ``k`` – the threshold used.
        * ``cleaned_metrics`` – metrics from the cleaned data.
        * ``null_fpr`` – false‑positive rate estimated from the null dataset.
        * ``inconsistency_rate`` – proportion of tests whose significance status
          changed between raw baseline and cleaned baseline.
    """
    logger = logging.getLogger(__name__)

    # Baseline metrics on the *raw* data – needed for inconsistency calculation.
    logger.info("Running baseline analysis on raw data (reference).")
    raw_metrics = run_baseline_analysis(
        dataframe=raw_df,
        outcome=outcome_col,
        predictors=predictor_cols,
    )
    raw_p_vals = _extract_p_values(raw_metrics)
    raw_significance = [_significant(p, alpha) for p in raw_p_vals]

    results: List[Dict[str, Any]] = []

    for k in ks:
        logger.info(f"Applying IQR outlier removal with k={k}.")
        cleaned_df = apply_iqr_outlier_removal(raw_df, k=k)

        # Guard against the cleaning step removing *all* rows.
        if cleaned_df.empty:
            logger.warning(f"All rows removed for k={k}; skipping this threshold.")
            continue

        logger.info("Running baseline analysis on cleaned data.")
        cleaned_metrics = run_baseline_analysis(
            dataframe=cleaned_df,
            outcome=outcome_col,
            predictors=predictor_cols,
        )
        cleaned_p_vals = _extract_p_values(cleaned_metrics)
        cleaned_significance = [_significant(p, alpha) for p in cleaned_p_vals]

        # ------------------------------------------------------------------- #
        # Inconsistency Rate
        # ------------------------------------------------------------------- #
        # We compare the binary significance decisions between raw and cleaned
        # analyses. If the lengths differ (e.g., some tests drop because of missing
        # predictors after cleaning) we compare up to the shorter length.
        min_len = min(len(raw_significance), len(cleaned_significance))
        if min_len == 0:
            inconsistency_rate = None
            logger.warning(
                f"No overlapping tests for k={k}; cannot compute inconsistency rate."
            )
        else:
            mismatches = sum(
                1
                for i in range(min_len)
                if raw_significance[i] != cleaned_significance[i]
            )
            inconsistency_rate = mismatches / min_len

        # ------------------------------------------------------------------- #
        # False‑Positive Rate (FPR) via null dataset
        # ------------------------------------------------------------------- #
        logger.info("Generating null dataset (shuffled outcome) for FPR estimation.")
        null_df = _shuffle_outcome(cleaned_df, outcome_col)

        logger.info("Running baseline analysis on null data.")
        null_metrics = run_baseline_analysis(
            dataframe=null_df,
            outcome=outcome_col,
            predictors=predictor_cols,
        )
        null_p_vals = _extract_p_values(null_metrics)
        false_positives = sum(1 for p in null_p_vals if _significant(p, alpha))
        fpr = false_positives / len(null_p_vals) if null_p_vals else None

        results.append(
            {
                "k": k,
                "cleaned_metrics": cleaned_metrics,
                "null_fpr": fpr,
                "inconsistency_rate": inconsistency_rate,
            }
        )

    return results

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Entry‑point used by ``python code/t033_outlier_threshold_sweep.py``.
    The function follows the conventions used throughout the project:

    * Logging is configured via ``utils.setup_logging`` (flexible signature).
    * Random seeds are fixed for reproducibility.
    * All output files are written under ``data/processed``.
    """
    # ------------------------------------------------------------------- #
    # Logging & reproducibility
    # ------------------------------------------------------------------- #
    logger = setup_logging(log_level="INFO")
    pin_random_seed(42)

    # ------------------------------------------------------------------- #
    # Load the raw dataset(s)
    # ------------------------------------------------------------------- #
    raw_dir = Path("data/raw")
    if not raw_dir.is_dir():
        logger.error(f"Raw data directory '{raw_dir}' does not exist.")
        raise FileNotFoundError(raw_dir)

    # The project historically works with a *single* dataset for the proof‑of‑concept.
    # We therefore load the first CSV we encounter.
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in '{raw_dir}'.")
        raise FileNotFoundError(raw_dir)

    raw_path = csv_files[0]
    logger.info(f"Loading raw dataset from '{raw_path}'.")
    raw_df = pd.read_csv(raw_path)

    # ------------------------------------------------------------------- #
    # Identify outcome and predictor columns
    # ------------------------------------------------------------------- #
    # Heuristic: the column named ``target`` or ``outcome`` is treated as the
    # dependent variable; all remaining numeric columns become predictors.
    possible_outcome_names = {"target", "outcome", "y", "label"}
    outcome_col = None
    for col in raw_df.columns:
        if col.lower() in possible_outcome_names:
            outcome_col = col
            break
    if outcome_col is None:
        # Fallback: use the last column (common in many UCI datasets).
        outcome_col = raw_df.columns[-1]
        logger.warning(
            f"Could not infer outcome column; falling back to last column '{outcome_col}'."
        )

    predictor_cols = [
        c
        for c in raw_df.columns
        if c != outcome_col and pd.api.types.is_numeric_dtype(raw_df[c])
    ]
    if not predictor_cols:
        logger.error("No numeric predictor columns detected.")
        raise ValueError("No predictors available for analysis.")

    # ------------------------------------------------------------------- #
    # Define the thresholds to sweep over.
    # ------------------------------------------------------------------- #
    ks_to_test = [0.5, 1.0, 1.5, 2.0, 2.5]

    # ------------------------------------------------------------------- #
    # Run the sweep
    # ------------------------------------------------------------------- #
    logger.info("Starting outlier‑threshold sweep.")
    sweep_results = run_outlier_threshold_sweep(
        raw_df=raw_df,
        outcome_col=outcome_col,
        predictor_cols=predictor_cols,
        ks=ks_to_test,
    )

    # ------------------------------------------------------------------- #
    # Persist results
    # ------------------------------------------------------------------- #
    processed_dir = Path("data/processed")
    _ensure_dir(processed_dir)

    sweep_path = processed_dir / "outlier_threshold_sweep.json"
    logger.info(f"Writing sweep results to '{sweep_path}'.")
    with sweep_path.open("w", encoding="utf-8") as f:
        json.dump(sweep_results, f, indent=2, ensure_ascii=False)

    # For downstream compatibility we also write the *last* cleaned and null
    # metrics to the legacy file names that other scripts expect.
    if sweep_results:
        last_cleaned = sweep_results[-1]["cleaned_metrics"]
        cleaned_path = processed_dir / "cleaned_metrics.json"
        logger.info(f"Writing cleaned metrics to '{cleaned_path}'.")
        with cleaned_path.open("w", encoding="utf-8") as f:
            json.dump(last_cleaned, f, indent=2, ensure_ascii=False)

        # Null‑FPR metrics – we store the raw null analysis dict; downstream
        # scripts only need the FPR value, but preserving the full dict is more
        # useful for debugging.
        last_null_fpr = sweep_results[-1]["null_fpr"]
        null_fpr_path = processed_dir / "null_fpr_metrics.json"
        logger.info(f"Writing null‑FPR metric to '{null_fpr_path}'.")
        with null_fpr_path.open("w", encoding="utf-8") as f:
            json.dump({"null_fpr": last_null_fpr}, f, indent=2, ensure_ascii=False)

    logger.info("Outlier‑threshold sweep completed successfully.")

if __name__ == "__main__":
    main()