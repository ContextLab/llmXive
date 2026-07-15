"""
Permutation Null FPR Generation Script
-------------------------------------

This script generates null datasets by shuffling the outcome variable while keeping
predictor columns fixed. For each permutation it computes Pearson correlation
p‑values between the shuffled outcome and each predictor. The false‑positive rate
(FPR) is estimated as the proportion of tests that yield a p‑value ≤ 0.05 across
all permutations.

The resulting metrics are written to ``data/processed/null_fpr_metrics.json``.
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

# Import the flexible logging helper from utils
from utils import setup_logging

logger = setup_logging(log_level="INFO")


def _prepare_outcome(series: pd.Series) -> pd.Series:
    """
    Ensure the outcome column is numeric. If it is categorical, factorize it.
    """
    if pd.api.types.is_numeric_dtype(series):
        return series
    # Factorize returns (labels, uniques); we keep labels as numeric codes
    codes, _ = pd.factorize(series, sort=True)
    return pd.Series(codes, index=series.index, name=series.name)


def generate_null_fpr_metrics(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
    n_permutations: int = 1000,
    significance_level: float = 0.05,
) -> Dict[str, float]:
    """
    Generate false‑positive‑rate metrics by permuting the outcome.

    Parameters
    ----------
    df : pd.DataFrame
        The original dataset.
    outcome : str
        Column name of the outcome/target variable.
    predictors : List[str]
        List of predictor column names.
    n_permutations : int, optional
        Number of permutation repetitions (default 1000).
    significance_level : float, optional
        Threshold for counting a test as significant (default 0.05).

    Returns
    -------
    dict
        Dictionary containing:
          - false_positive_rate
          - total_tests
          - significant_tests
          - n_permutations
          - n_predictors
    """
    if outcome not in df.columns:
        raise ValueError(f"Outcome column '{outcome}' not found in dataframe.")
    missing_preds = [p for p in predictors if p not in df.columns]
    if missing_preds:
        raise ValueError(f"Predictor columns not found: {missing_preds}")

    # Prepare outcome as numeric
    y_original = _prepare_outcome(df[outcome])

    # Extract predictor data once (no need to copy each loop)
    X = df[predictors]

    total_tests = n_permutations * len(predictors)
    significant_tests = 0

    logger.info(
        "Starting permutation FPR estimation: %d permutations, %d predictors",
        n_permutations,
        len(predictors),
    )

    for perm_idx in range(n_permutations):
        # Shuffle outcome while preserving index alignment
        y_shuffled = y_original.sample(frac=1, replace=False, random_state=None).reset_index(drop=True)
        # Align shuffled outcome with predictor rows
        y_shuffled.index = X.index

        for pred in predictors:
            x = X[pred].values
            y = y_shuffled.values

            # If predictor is constant, correlation is undefined; skip
            if np.allclose(x, x[0]):
                continue

            try:
                _, p_val = pearsonr(x, y)
            except Exception as exc:
                logger.debug(
                    "Pearson correlation failed for predictor '%s' on permutation %d: %s",
                    pred,
                    perm_idx,
                    exc,
                )
                continue

            if np.isnan(p_val):
                continue

            if p_val <= significance_level:
                significant_tests += 1

    false_positive_rate = significant_tests / total_tests if total_tests > 0 else float("nan")

    logger.info(
        "Permutation FPR completed: %d significant / %d total tests => FPR = %.4f",
        significant_tests,
        total_tests,
        false_positive_rate,
    )

    return {
        "false_positive_rate": false_positive_rate,
        "total_tests": total_tests,
        "significant_tests": significant_tests,
        "n_permutations": n_permutations,
        "n_predictors": len(predictors),
    }


def _write_metrics(metrics: Dict[str, float], output_path: Path) -> None:
    """Write the metrics dictionary as pretty‑printed JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Null‑FPR metrics written to %s", output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate permutation‑based false‑positive‑rate metrics."
    )
    parser.add_argument(
        "--data_path",
        type=str,
        required=True,
        help="Path to the CSV file containing the dataset.",
    )
    parser.add_argument(
        "--outcome",
        type=str,
        required=True,
        help="Name of the outcome/target column.",
    )
    parser.add_argument(
        "--predictors",
        type=str,
        required=True,
        help="Comma‑separated list of predictor column names.",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="data/processed/null_fpr_metrics.json",
        help="File path where the JSON metrics will be saved.",
    )
    parser.add_argument(
        "--n_permutations",
        type=int,
        default=1000,
        help="Number of permutations to perform (default 1000).",
    )
    parser.add_argument(
        "--significance_level",
        type=float,
        default=0.05,
        help="p‑value threshold for counting a test as significant (default 0.05).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data_path)
    output_path = Path(args.output_path)

    logger.info("Loading dataset from %s", data_path)
    df = pd.read_csv(data_path)

    predictors = [p.strip() for p in args.predictors.split(",") if p.strip()]

    metrics = generate_null_fpr_metrics(
        df=df,
        outcome=args.outcome,
        predictors=predictors,
        n_permutations=args.n_permutations,
        significance_level=args.significance_level,
    )

    _write_metrics(metrics, output_path)


if __name__ == "__main__":
    main()
