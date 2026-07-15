from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd

from utils.logging import get_logger
from utils.config import get_seed

logger = get_logger(__name__)


def validate_bug_label_precision(
    df: pd.DataFrame,
    ground_truth_path: Optional[Path] = None,
    min_precision: float = 0.85,
) -> Tuple[bool, float]:
    """
    Validate the reliability of the bug_label column against a ground truth file.

    If ground_truth_path is provided:
        - Loads the ground truth CSV.
        - Merges on 'file_path' and 'commit_hash' (or similar unique keys).
        - Calculates precision: TP / (TP + FP).
        - Returns (True, precision) if precision >= min_precision.
        - Returns (False, precision) if precision < min_precision.
        - Raises ValueError if the calculated precision is below the threshold,
          effectively failing the pipeline as required by T049.

    If ground_truth_path is NOT provided:
        - This function cannot validate reliability.
        - Per T049 requirements, we must fail loudly rather than assume 100% precision.
        - Raises ValueError indicating that ground truth is required for validation.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe containing the 'bug_label' column to validate.
    ground_truth_path : Optional[Path]
        Path to a CSV file containing ground truth labels.
    min_precision : float
        Minimum required precision (default 0.85).

    Returns
    -------
    Tuple[bool, float]
        (success, precision_score)

    Raises
    ------
    ValueError
        If precision is below min_precision or if ground truth is missing.
    """
    if ground_truth_path is None or not ground_truth_path.exists():
        raise ValueError(
            "Bug-label reliability validation failed: Ground truth file not provided or not found at "
            f"{ground_truth_path}. T049 requires this validation to pass before proceeding. "
            "Cannot default to synthetic precision."
        )

    try:
        gt_df = pd.read_csv(ground_truth_path)
    except Exception as e:
        raise ValueError(f"Failed to load ground truth file: {e}")

    # Determine common keys for merging.
    # Assuming standard keys based on project context: file_path, commit_hash
    common_keys = list(set(df.columns) & set(gt_df.columns))
    if not common_keys:
        raise ValueError(
            f"No common keys found between data and ground truth to calculate precision. "
            f"Data cols: {df.columns[:5]}..., GT cols: {gt_df.columns[:5]}..."
        )

    # Merge
    merged = pd.merge(
        df, gt_df, on=common_keys, how='inner', suffixes=('_pred', '_true')
    )

    if merged.empty:
        raise ValueError(
            "No matching records found between data and ground truth to calculate precision."
        )

    # Identify columns for labels.
    # Heuristic: look for 'bug_label' or 'label' in both
    pred_col = None
    true_col = None
    for col in merged.columns:
        if 'pred' in col.lower() and 'label' in col.lower():
            pred_col = col
        elif 'true' in col.lower() and 'label' in col.lower():
            true_col = col

    # Fallback to exact name match if heuristic fails
    if not pred_col and 'bug_label' in merged.columns:
        pred_col = 'bug_label'
    if not true_col and 'bug_label_true' in merged.columns:
        true_col = 'bug_label_true'
    elif not true_col and 'bug_label' in merged.columns and pred_col != 'bug_label':
         # If both are just 'bug_label' from merge, one might be suffixed or we need to rename
         # In a strict merge with suffixes, one is _pred, one is _true.
         # If the ground truth column was named 'bug_label', it becomes 'bug_label_true'.
         pass

    if not pred_col or not true_col:
        # Last resort: assume the last two columns are the labels if named similarly
        # Or raise error
        raise ValueError(
            f"Could not identify prediction and ground truth label columns. "
            f"Available: {merged.columns.tolist()}"
        )

    # Calculate Precision: TP / (TP + FP)
    # TP: predicted bug (1) and actually bug (1)
    # FP: predicted bug (1) but actually not bug (0)
    # We assume binary 0/1 labels.
    pred_labels = merged[pred_col].astype(int)
    true_labels = merged[true_col].astype(int)

    tp = ((pred_labels == 1) & (true_labels == 1)).sum()
    fp = ((pred_labels == 1) & (true_labels == 0)).sum()

    if (tp + fp) == 0:
        # No positive predictions defined as precision = 1.0 by convention in some contexts,
        # but strictly speaking undefined. Let's treat as 0.0 to fail validation if we expect bugs.
        # However, if the model predicts NO bugs, precision is technically undefined.
        # For safety in this pipeline, we fail if we can't calculate.
        logger.warning("No positive predictions found. Precision is undefined.")
        precision = 0.0
    else:
        precision = tp / (tp + fp)

    logger.info(f"Bug label validation precision: {precision:.4f} (threshold: {min_precision})")

    if precision < min_precision:
        raise ValueError(
            f"Bug-label reliability validation FAILED. Precision {precision:.4f} < {min_precision}. "
            "Pipeline aborted as per T049 requirements."
        )

    return True, precision


def preprocess(
    input_path: Path,
    output_path: Path,
    ground_truth_path: Optional[Path] = None,
    min_precision: float = 0.85,
) -> pd.DataFrame:
    """
    Preprocess the dataset:
    1. Validate bug label precision (T049).
    2. Impute missing values (< 5% missing) with median.
    3. Log-transform metrics with skewness > 2.
    4. Remove rows with > 5% missing values.
    5. Save to output_path.

    Parameters
    ----------
    input_path : Path
        Path to input CSV.
    output_path : Path
        Path to save processed CSV.
    ground_truth_path : Optional[Path]
        Path to ground truth for validation.
    min_precision : float
        Minimum precision threshold.

    Returns
    -------
    pd.DataFrame
        The processed dataframe.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # T049: Validate bug label precision
    logger.info("Validating bug label precision...")
    try:
        validate_bug_label_precision(df, ground_truth_path, min_precision)
        logger.info("Bug label precision validation PASSED.")
    except ValueError as e:
        logger.error(str(e))
        raise

    # T015: Handle missing values
    missing_ratio = df.isnull().mean()
    logger.info(f"Missing value ratio per column:\n{missing_ratio}")

    # Remove rows with > 5% missing values
    threshold = 0.05
    rows_to_drop = df.isnull().sum(axis=1) > (df.shape[1] * threshold)
    if rows_to_drop.any():
        logger.warning(f"Dropping {rows_to_drop.sum()} rows with > {threshold*100}% missing values.")
        df = df[~rows_to_drop]

    # Impute missing values (< 5% missing) with median
    # We only impute columns where missing ratio < 5%
    cols_to_impute = missing_ratio[missing_ratio < threshold].index
    logger.info(f"Imputing missing values for columns: {list(cols_to_impute)}")
    for col in cols_to_impute:
        median_val = df[col].median()
        if np.isnan(median_val):
            logger.warning(f"Median for {col} is NaN, skipping imputation.")
            continue
        df[col] = df[col].fillna(median_val)

    # T015: Log-transform metrics with skewness > 2
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    skewness_threshold = 2.0
    log_cols = []
    for col in numeric_cols:
        if col == 'bug_label':
            continue
        skew = df[col].skew()
        if skew > skewness_threshold:
            log_cols.append(col)
            logger.info(f"Log-transforming {col} (skewness={skew:.2f})")
            # Add small epsilon to avoid log(0)
            df[col] = np.log1p(df[col])

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save
    logger.info(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)

    logger.info("Preprocessing complete.")
    return df


def main():
    parser = argparse.ArgumentParser(description="Preprocess data pipeline step.")
    parser.add_argument("--input", type=Path, required=True, help="Input CSV file path.")
    parser.add_argument("--output", type=Path, required=True, help="Output CSV file path.")
    parser.add_argument("--ground-truth", type=Path, default=None, help="Ground truth CSV for validation (T049).")
    parser.add_argument("--min-precision", type=float, default=0.85, help="Minimum precision threshold.")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        preprocess(
            args.input,
            args.output,
            args.ground_truth,
            args.min_precision
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()