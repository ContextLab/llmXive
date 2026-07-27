"""
t032_permutation_null_fpr.py
--------------------------------
Implements Task T032: generate permutation (null) datasets by shuffling the
outcome variable while keeping predictor variables fixed, and estimate the
false‑positive rate (FPR) of the statistical tests used in the pipeline.

The script is intentionally self‑contained and does **not** depend on the
`run_baseline_analysis` helper (which has a volatile signature across the
codebase).  Instead it directly performs a linear‑regression based t‑test
for each predictor on each permuted outcome and records the proportion of
p‑values ≤ 0.05.  The final estimate is written to
``data/processed/null_fpr_metrics.json`` as required by the specification.

Usage (as invoked from the quick‑start run‑book):
    python code/t032_permutation_null_fpr.py \
        --raw-dir data/raw \
        --outcome outcome_column_name \
        --predictors predictor1 predictor2 predictor3 \
        --permutations 1000 \
        --output data/processed/null_fpr_metrics.json

All arguments are optional; reasonable defaults are provided for a typical
dataset where the outcome column is named ``target`` and all other numeric
columns are treated as predictors.
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import statsmodels.api as sm

# --------------------------------------------------------------------------- #
# Logging utilities – we accept the flexible signatures used throughout the
# project (positional, keyword, name+level, etc.) by delegating to the central
# ``setup_logging`` if it exists, otherwise falling back to a basic config.
# --------------------------------------------------------------------------- #
try:
    # ``setup_logging`` lives in ``code/utils.py`` and may have a flexible
    # signature.  Import lazily to avoid circular imports.
    from utils import setup_logging  # type: ignore
except Exception:  # pragma: no cover
    def setup_logging(*args, **kwargs):
        """Fallback logger configuration used only when the project utility
        cannot be imported (e.g., during isolated test runs)."""
        level = kwargs.get("log_level", "INFO")
        if args:
            # first positional arg may be a logger name or a level string
            possible_level = args[0]
            if possible_level.upper() in logging._nameToLevel:
                level = possible_level
        logging.basicConfig(level=logging.getLevelName(level))
        return logging.getLogger(__name__)

logger = setup_logging(log_level="INFO")

# --------------------------------------------------------------------------- #
# Core functionality
# --------------------------------------------------------------------------- #
def _load_dataset(csv_path: Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    Parameters
    ----------
    csv_path: Path
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Loaded data.
    """
    logger.info("Loading dataset from %s", csv_path)
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"The dataset at {csv_path} is empty.")
    return df

def _run_regression(df: pd.DataFrame, outcome: str, predictors: List[str]) -> List[float]:
    """Fit separate OLS models (one per predictor) and return the p‑values
    for the predictor coefficients.

    Parameters
    ----------
    df: pd.DataFrame
        Data containing outcome and predictors.
    outcome: str
        Name of the outcome column.
    predictors: List[str]
        List of predictor column names.

    Returns
    -------
    List[float]
        List of p‑values, one per predictor.
    """
    p_values = []
    y = df[outcome].values
    for pred in predictors:
        X = df[[pred]].astype(float)
        X = sm.add_constant(X)  # adds intercept
        model = sm.OLS(y, X, missing='drop')
        results = model.fit()
        # statsmodels stores p‑values in results.pvalues; the predictor is the
        # second entry because the first is the intercept.
        p_val = results.pvalues.iloc[1]
        p_values.append(float(p_val))
    return p_values

def generate_null_fpr_metrics(
    raw_dir: str,
    outcome: str,
    predictors: List[str],
    permutations: int = 1000,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Generate permutation‑based null datasets, run the same statistical tests
    as the baseline analysis, and estimate the false‑positive rate (FPR).

    Parameters
    ----------
    raw_dir: str
        Directory containing raw CSV datasets.
    outcome: str
        Name of the outcome/target column.
    predictors: List[str]
        List of predictor column names to be used in the regression/t‑test.
    permutations: int, default 1000
        Number of random permutations to generate.
    alpha: float, default 0.05
        Significance threshold for counting a false positive.

    Returns
    -------
    dict
        Dictionary with the estimated FPR and auxiliary information.
    """
    raw_path = Path(raw_dir)
    if not raw_path.is_dir():
        raise NotADirectoryError(f"Raw data directory '{raw_dir}' does not exist.")
    csv_files = list(raw_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in raw data directory '{raw_dir}'.")

    logger.info("Found %d dataset(s) for null‑FPR estimation.", len(csv_files))

    # Accumulate counts across all datasets and permutations
    total_tests = 0
    false_positives = 0

    for csv_file in csv_files:
        df_original = _load_dataset(csv_file)

        # Verify required columns exist
        missing_cols = [col for col in [outcome] + predictors if col not in df_original.columns]
        if missing_cols:
            raise KeyError(
                f"Columns {missing_cols} missing in dataset {csv_file.name}. "
                f"Available columns: {list(df_original.columns)}"
            )

        # Baseline (non‑permuted) p‑values are *not* counted toward FPR.
        # We only look at permutations where the relationship is broken.
        for i in range(permutations):
            df_permuted = df_original.copy()
            df_permuted[outcome] = np.random.permutation(df_permuted[outcome].values)
            p_vals = _run_regression(df_permuted, outcome, predictors)
            total_tests += len(p_vals)
            false_positives += sum(p <= alpha for p in p_vals)

            if (i + 1) % max(1, permutations // 10) == 0:
                logger.debug(
                    "Dataset %s – permutation %d/%d completed.",
                    csv_file.name,
                    i + 1,
                    permutations,
                )

    fpr_estimate = false_positives / total_tests if total_tests > 0 else float("nan")
    logger.info(
        "Null‑FPR estimation completed: %d false positives out of %d tests (FPR = %.4f)",
        false_positives,
        total_tests,
        fpr_estimate,
    )

    return {
        "fpr_estimate": round(fpr_estimate, 4),
        "total_tests": total_tests,
        "false_positives": false_positives,
        "num_permutations": permutations,
        "outcome_column": outcome,
        "predictor_columns": predictors,
    }

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate permutation‑based null datasets and estimate the false‑positive rate."
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default="data/raw",
        help="Directory containing raw CSV files (default: data/raw).",
    )
    parser.add_argument(
        "--outcome",
        type=str,
        default="target",
        help="Name of the outcome/target column (default: target).",
    )
    parser.add_argument(
        "--predictors",
        nargs="+",
        type=str,
        default=[],
        help="List of predictor column names. If omitted, all numeric columns "
             "except the outcome are used.",
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=1000,
        help="Number of permutations to generate (default: 1000).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/null_fpr_metrics.json",
        help="Path to write the resulting JSON metrics file.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (e.g., DEBUG, INFO, WARNING).",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    # Adjust logging level as requested by the user
    logger.setLevel(logging.getLevelName(args.log_level.upper()))

    # If the user did not supply predictors, infer them from the first dataset
    raw_path = Path(args.raw_dir)
    csv_files = list(raw_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in '{args.raw_dir}'.")

    sample_df = _load_dataset(csv_files[0])
    if not args.predictors:
        # Use all numeric columns except the outcome as predictors
        inferred_predictors = [
            col
            for col, dtype in sample_df.dtypes.items()
            if np.issubdtype(dtype, np.number) and col != args.outcome
        ]
        if not inferred_predictors:
            raise ValueError(
                f"Could not infer predictor columns from {csv_files[0].name}. "
                "Please specify them explicitly via '--predictors'."
            )
        predictors = inferred_predictors
    else:
        predictors = args.predictors

    metrics = generate_null_fpr_metrics(
        raw_dir=args.raw_dir,
        outcome=args.outcome,
        predictors=predictors,
        permutations=args.permutations,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Null‑FPR metrics written to %s", output_path)

if __name__ == "__main__":
    main()