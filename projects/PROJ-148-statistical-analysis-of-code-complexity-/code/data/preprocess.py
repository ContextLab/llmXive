"""
Data preprocessing pipeline.

This script reads a raw dataset CSV, performs basic cleaning steps
(numeric imputation, log‑transformation of highly skewed metrics),
validates the reliability of bug‑fix labels, and writes the processed
dataset to the specified output location.

The bug‑label validation is performed via the ``validate_bug_labels``
function defined in ``code/data/validate_bug_labels.py``.  The pipeline
enforces a minimum precision of 85 % for the bug‑label predictions; if
the measured precision is lower, a ``RuntimeError`` is raised and the
pipeline aborts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

# Local imports – these names are defined in the project API surface
from data.validate_bug_labels import validate_bug_labels

__all__ = ["preprocess", "main"]


def _impute_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing numeric values with the column median.
    Non‑numeric columns are left untouched.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isna().any():
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
    return df


def _log_transform_skewed(df: pd.DataFrame, skew_threshold: float = 2.0) -> pd.DataFrame:
    """
    Apply a natural‑log (plus one) transformation to numeric columns whose
    absolute skewness exceeds ``skew_threshold``.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        skew = df[col].skew()
        if pd.notna(skew) and abs(skew) > skew_threshold:
            # Adding 1 to avoid log(0)
            df[col] = np.log1p(df[col])
    return df


def _enforce_bug_label_precision(df: pd.DataFrame, threshold: float = 0.85) -> None:
    """
    Validate bug‑label reliability and raise an error if precision is
    below ``threshold``.
    """
    metrics = validate_bug_labels(df)
    precision = metrics.get("precision")
    if precision is None:
        raise RuntimeError(
            "Bug‑label validation did not return a 'precision' metric."
        )
    if precision < threshold:
        raise RuntimeError(
            f"Bug‑label precision {precision:.2%} is below the required "
            f"{threshold:.2%} threshold. Pipeline aborted."
        )


def preprocess(
    input_path: Path,
    output_path: Path,
) -> Tuple[Path, pd.DataFrame]:
    """
    Execute the preprocessing steps.

    Parameters
    ----------
    input_path: Path
        Path to the raw CSV dataset.
    output_path: Path
        Destination path for the cleaned CSV dataset.

    Returns
    -------
    Tuple[Path, pd.DataFrame]
        The path to the written CSV file and the processed DataFrame.
    """
    # ------------------------------------------------------------------
    # Load raw data
    # ------------------------------------------------------------------
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)

    # ------------------------------------------------------------------
    # Cleaning steps
    # ------------------------------------------------------------------
    df = _impute_numeric(df)
    df = _log_transform_skewed(df)

    # ------------------------------------------------------------------
    # Bug‑label reliability validation
    # ------------------------------------------------------------------
    _enforce_bug_label_precision(df, threshold=0.85)

    # ------------------------------------------------------------------
    # Persist processed data
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    return output_path, df


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess raw dataset and enforce bug‑label precision."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the raw input CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path where the processed CSV will be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """
    Command‑line entry point.
    """
    args = _parse_args(argv)
    try:
        preprocess(args.input, args.output)
    except Exception as exc:
        # Log the error to stderr and exit with a non‑zero status code
        print(f"Error during preprocessing: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
