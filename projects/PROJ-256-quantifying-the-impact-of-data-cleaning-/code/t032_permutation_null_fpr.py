"""
T032 – Permutation Null Dataset Generation

This script creates null datasets by shuffling the outcome variable while keeping
predictor variables fixed. For each dataset it estimates the false‑positive rate
(FPR) as the proportion of statistical tests that return a p‑value ≤ 0.05 on the
permuted data.

Output:
    data/processed/null_fpr_metrics.json
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import scipy.stats

from utils import setup_logging, pin_random_seed

LOGGER = setup_logging(log_level="INFO")


def _detect_outcome_column(df: pd.DataFrame) -> str:
    """
    Heuristically pick an outcome column. Preference order:
    1. Column named exactly 'outcome' (case‑insensitive)
    2. Column named exactly 'target'
    3. The first column in the DataFrame
    """
    for candidate in ["outcome", "target"]:
        matches = [c for c in df.columns if c.lower() == candidate]
        if matches:
            return matches[0]
    return df.columns[0]


def _compute_fpr_for_dataframe(
    df: pd.DataFrame,
    outcome_col: str,
    n_permutations: int = 1000,
    alpha: float = 0.05,
) -> float:
    """
    Estimate the false‑positive rate for a single DataFrame.

    For each permutation the outcome column is shuffled, then a Pearson correlation
    test is performed between the shuffled outcome and each numeric predictor.
    The proportion of resulting p‑values ≤ ``alpha`` across all permutations and
    predictors is returned as the FPR.
    """
    predictors = [c for c in df.columns if c != outcome_col]
    numeric_predictors = [
        c
        for c in predictors
        if pd.api.types.is_numeric_dtype(df[c]) and pd.api.types.is_numeric_dtype(df[outcome_col])
    ]

    if not numeric_predictors:
        LOGGER.warning(
            f"No numeric predictors found in dataset with outcome column '{outcome_col}'. "
            "Returning FPR = 0.0."
        )
        return 0.0

    pvals: List[float] = []

    for _ in range(n_permutations):
        shuffled_outcome = df[outcome_col].sample(frac=1, replace=False).reset_index(drop=True)
        df_shuffled = df.copy()
        df_shuffled[outcome_col] = shuffled_outcome

        for pred in numeric_predictors:
            # Pearson correlation returns a correlation coefficient and a two‑tailed p‑value
            _, p = scipy.stats.pearsonr(df_shuffled[pred], df_shuffled[outcome_col])
            pvals.append(p)

    pvals_arr = np.array(pvals)
    fpr = float(np.mean(pvals_arr <= alpha))
    return fpr


def generate_null_fpr_metrics(
    raw_dir: Path = Path("data/raw"),
    output_file: Path = Path("data/processed/null_fpr_metrics.json"),
    n_permutations: int = 1000,
) -> Dict[str, Any]:
    """
    Generate null‑dataset FPR metrics for every CSV file found in ``raw_dir``.

    Parameters
    ----------
    raw_dir: Path
        Directory containing raw CSV datasets.
    output_file: Path
        Destination JSON file for the aggregated metrics.
    n_permutations: int
        Number of outcome shuffles per dataset.

    Returns
    -------
    dict
        Mapping from dataset filename to its estimated FPR.
    """
    LOGGER.info(f"Scanning raw data directory: {raw_dir}")
    if not raw_dir.exists():
        LOGGER.error(f"Raw data directory does not exist: {raw_dir}")
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    metrics: Dict[str, Any] = {}

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        LOGGER.warning(f"No CSV files found in {raw_dir}. Empty metrics will be written.")

    for csv_path in csv_files:
        LOGGER.info(f"Processing raw dataset: {csv_path.name}")
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            LOGGER.error(f"Failed to read {csv_path}: {e}")
            continue

        outcome_col = _detect_outcome_column(df)
        LOGGER.debug(f"Detected outcome column '{outcome_col}' for {csv_path.name}")

        fpr = _compute_fpr_for_dataframe(
            df, outcome_col, n_permutations=n_permutations, alpha=0.05
        )
        metrics[csv_path.name] = {
            "outcome_column": outcome_col,
            "false_positive_rate": round(fpr, 5),
            "permutations": n_permutations,
        }
        LOGGER.info(
            f"Finished {csv_path.name}: FPR = {metrics[csv_path.name]['false_positive_rate']}"
        )

    # Ensure the output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    LOGGER.info(f"Null‑FPR metrics written to {output_file}")
    return metrics

# ----------------------------------------------------------------------
# Core generation logic
# ----------------------------------------------------------------------
def generate_null_fpr_metrics(
    processed_dir: Path = PROCESSED_DATA_DIR,
    output_path: Path = NULL_FPR_OUTPUT,
) -> None:
    """
    Entry point for the script. Seeds RNG for reproducibility and runs the
    null‑FPR generation with defaults (or values overridden via environment
    variables).
    """
    # Allow optional overrides via environment variables
    raw_dir = Path(os.getenv("RAW_DATA_PATH", "data/raw"))
    output_path = Path(os.getenv("NULL_FPR_OUTPUT_PATH", "data/processed/null_fpr_metrics.json"))
    n_perm = int(os.getenv("NULL_FPR_PERMUTATIONS", "1000"))

    # Seed for reproducibility
    seed = int(os.getenv("RANDOM_SEED", "42"))
    pin_random_seed(seed)

    generate_null_fpr_metrics(
        raw_dir=raw_dir,
        output_file=output_path,
        n_permutations=n_perm,
    )

# ----------------------------------------------------------------------
# Script entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for ``python code/t032_permutation_null_fpr.py``.
    Sets up logging and triggers the null‑FPR generation.
    """
    # The project's ``setup_logging`` utility tolerates any signature.
    logger = setup_logging(LOG_LEVEL)
    if isinstance(logger, logging.Logger):
        logging.getLogger().setLevel(logger.level)
    generate_null_fpr_metrics()

if __name__ == "__main__":
    main()