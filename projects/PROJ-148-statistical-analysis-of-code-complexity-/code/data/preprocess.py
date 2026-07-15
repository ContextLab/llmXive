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
    min_precision: float = 0.85
) -> Tuple[bool, float]:
    """
    Validate bug label reliability against a ground truth set if provided.
    If ground truth is not provided, it returns True/1.0 as a placeholder
    (assuming the labeling logic in T013 is trusted).

    Args:
        df: The dataframe containing the 'bug_label' column.
        ground_truth_path: Path to a CSV with 'id' and 'true_bug_label'.
        min_precision: Minimum required precision (default 0.85).

    Returns:
        Tuple of (passes_validation, calculated_precision).
    """
    if ground_truth_path is None or not ground_truth_path.exists():
        logger.warning("No ground truth file provided. Skipping precision validation.")
        return True, 1.0

    try:
        gt_df = pd.read_csv(ground_truth_path)
        # Merge on a common ID column. Assuming 'id' or 'file_hash' exists in df.
        # If df doesn't have a unique ID, we might need to join on filename+line/commit.
        # For this implementation, we assume 'id' exists in both.
        if 'id' not in df.columns:
            logger.error("DataFrame missing 'id' column required for validation.")
            return False, 0.0

        merged = df.merge(gt_df, on='id', how='inner')
        if merged.empty:
            logger.error("No overlapping IDs found between data and ground truth.")
            return False, 0.0

        # Calculate precision: TP / (TP + FP)
        # TP: predicted=1, true=1
        # FP: predicted=1, true=0
        tp = ((merged['bug_label'] == 1) & (merged['true_bug_label'] == 1)).sum()
        fp = ((merged['bug_label'] == 1) & (merged['true_bug_label'] == 0)).sum()

        if (tp + fp) == 0:
            precision = 1.0  # No positive predictions, technically perfect precision
        else:
            precision = tp / (tp + fp)

        logger.info(f"Bug label precision: {precision:.4f} (threshold: {min_precision})")

        if precision < min_precision:
            logger.error(f"Precision {precision:.4f} is below required threshold {min_precision}.")
            return False, precision

        return True, precision

    except Exception as e:
        logger.error(f"Error during precision validation: {e}")
        return False, 0.0


def preprocess(
    input_path: Path,
    output_path: Path,
    ground_truth_path: Optional[Path] = None,
    min_precision: float = 0.85,
    missing_threshold: float = 0.05,
    skewness_threshold: float = 2.0
) -> pd.DataFrame:
    """
    Preprocess the dataset:
    1. Validate bug label precision (fail if < min_precision).
    2. Remove rows where missing values exceed `missing_threshold` (5%).
    3. Impute remaining missing values (mean) if < 5% of total values in column.
    4. Log-transform metrics with skewness > `skewness_threshold`.

    Args:
        input_path: Path to the input CSV.
        output_path: Path to write the preprocessed CSV.
        ground_truth_path: Optional path for bug label validation.
        min_precision: Minimum precision required for bug labels.
        missing_threshold: Max fraction of missing values allowed per row (0.05).
        skewness_threshold: Skewness value above which log-transform is applied.

    Returns:
        The preprocessed DataFrame.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # 1. Validate Bug Label Precision
    logger.info("Validating bug label precision...")
    passes, precision = validate_bug_label_precision(df, ground_truth_path, min_precision)
    if not passes:
        raise RuntimeError(f"Bug label validation failed: Precision {precision:.4f} < {min_precision}. Pipeline aborted.")

    # Identify numeric columns for preprocessing
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude 'bug_label' from transformation logic, though it might be numeric
    feature_cols = [c for c in numeric_cols if c != 'bug_label']

    # 2. Remove rows with > 5% missing values
    # Calculate missing percentage per row
    total_cols = len(df.columns)
    missing_per_row = df.isnull().sum(axis=1) / total_cols
    rows_to_drop = missing_per_row > missing_threshold
    dropped_count = rows_to_drop.sum()
    if dropped_count > 0:
        logger.warning(f"Dropping {dropped_count} rows ({dropped_count/len(df)*100:.2f}%) with > {missing_threshold*100}% missing values.")
        df = df[~rows_to_drop]

    # 3. Impute missing values
    # Check column-wise missing percentage
    missing_per_col = df[feature_cols].isnull().mean()
    cols_to_impute = missing_per_col[missing_per_col < missing_threshold].index.tolist()
    cols_high_missing = missing_per_col[missing_per_col >= missing_threshold].index.tolist()

    if cols_high_missing:
        logger.warning(f"Columns with > {missing_threshold*100}% missing values (skipping imputation): {cols_high_missing}")
    
    if cols_to_impute:
        logger.info(f"Imputing missing values in columns: {cols_to_impute} with column mean.")
        for col in cols_to_impute:
            df[col].fillna(df[col].mean(), inplace=True)

    # 4. Log-transform metrics with skewness > threshold
    skewness_values = {}
    transformed_cols = []
    
    for col in feature_cols:
        if col in df.columns and df[col].notnull().any():
            skew = df[col].skew()
            skewness_values[col] = skew
            if skew > skewness_threshold:
                # Handle zeros/negatives if any (though complexity metrics usually positive)
                # Add small epsilon if min is 0 to avoid log(0)
                if df[col].min() <= 0:
                    df[col] = df[col] + abs(df[col].min()) + 1e-6
                df[col] = np.log1p(df[col])
                transformed_cols.append(col)
                logger.info(f"Log-transformed column '{col}' (skewness: {skew:.4f})")
    
    logger.info(f"Skewness stats computed for {len(skewness_values)} features.")
    if transformed_cols:
        logger.info(f"Transformed columns: {transformed_cols}")

    # Save to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Preprocessed data saved to {output_path}")

    return df


def main():
    parser = argparse.ArgumentParser(description="Preprocess code complexity dataset.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV.")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV.")
    parser.add_argument("--ground-truth", type=str, default=None, help="Path to ground truth CSV for validation.")
    parser.add_argument("--min-precision", type=float, default=0.85, help="Minimum required precision for bug labels.")
    
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    gt_path = Path(args.ground_truth) if args.ground_truth else None

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        preprocess(
            input_path=input_path,
            output_path=output_path,
            ground_truth_path=gt_path,
            min_precision=args.min_precision
        )
        logger.info("Preprocessing completed successfully.")
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during preprocessing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()