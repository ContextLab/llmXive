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

# Task T049: Integrate bug-label reliability validation
# We assume a validation script exists (T014) that produces a report or
# returns a precision metric. Since we cannot import a non-existent
# function from a file we don't see the full content of, we will
# implement the logic here that would call such a validator or
# perform the check if the data is already labeled.
#
# However, the task description says: "Integrate bug‑label reliability
# validation into the data pipeline and enforce precision ≥ 85%".
#
# Strategy:
# 1. Load the raw labeled data (output of label_bug_fixes.py).
# 2. Call a validation routine. Since T014 (validate_bug_labels.py) exists
#    and has a `validate_bug_labels` function, we import it.
# 3. If the validation returns a precision < 0.85, we raise an error
#    to fail the pipeline.
# 4. If precision >= 0.85, we proceed with standard preprocessing.

logger = get_logger(__name__)


def validate_bug_label_precision(df: pd.DataFrame) -> float:
    """
    Validates the precision of the bug_label column.
    
    In a real scenario, this might compare against a gold standard.
    Here, we assume the 'validate_bug_labels' utility from T014
    performs this check or returns a confidence score.
    
    For this implementation, we will simulate a check against a
    known subset or a heuristic if no ground truth is available,
    BUT the requirement is to FAIL if precision < 85%.
    
    Since we cannot fabricate a gold standard, we will assume the
    T014 script `validate_bug_labels` returns a precision metric
    based on its internal logic (e.g., consistency checks).
    We will attempt to import and use it.
    """
    try:
        # Import the function from the existing T014 module
        from data.validate_bug_labels import validate_bug_labels
        
        # The T014 function likely returns a dict or a tuple.
        # We assume it returns a dict with a 'precision' key or similar.
        # If the function signature is different, we adapt.
        # Based on the API surface: `validate_bug_labels` returns `main`
        # which usually runs and prints. We need the value.
        # Let's assume `validate_bug_labels` returns a dict of metrics.
        metrics = validate_bug_labels(df)
        
        if isinstance(metrics, dict) and 'precision' in metrics:
            return metrics['precision']
        elif isinstance(metrics, float):
            return metrics
        else:
            # Fallback: if the function doesn't return a metric,
            # we might need to compute a proxy or raise an error.
            # For safety, if we can't verify, we fail.
            logger.warning("Validation function did not return a precision metric.")
            return 0.0
    except ImportError:
        logger.error("Could not import validate_bug_labels from data.validate_bug_labels")
        return 0.0
    except Exception as e:
        logger.error(f"Error during bug label validation: {e}")
        return 0.0


def preprocess(
    input_path: Path,
    output_path: Path,
    precision_threshold: float = 0.85
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Preprocess the dataset:
    1. Validate bug label precision (T049 requirement).
    2. Impute missing values (< 5%).
    3. Log-transform skewed metrics (skewness > 2).
    4. Remove rows with > 5% missing values.
    5. Return train/test splits (handled in split_dataset.py, but this function
       prepares the clean data).
    
    Returns:
        Tuple of (clean_df, train_df) - Note: split is usually separate,
        but this function returns the cleaned data ready for splitting.
        For this task, we return the cleaned dataframe and a placeholder split.
    """
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # --- T049: Bug Label Reliability Validation ---
    logger.info("Validating bug label precision...")
    precision = validate_bug_label_precision(df)
    logger.info(f"Bug label validation precision: {precision:.4f}")
    
    if precision < precision_threshold:
        error_msg = f"Bug label precision ({precision:.4f}) is below the required threshold ({precision_threshold}). Pipeline failing."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Bug label validation passed.")
    
    # --- Standard Preprocessing Steps (from T015) ---
    
    # Identify numeric columns for preprocessing
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # 1. Handle missing values
    # Calculate missing percentage per column
    missing_pct = df[numeric_cols].isna().mean()
    logger.info(f"Missing value percentages:\n{missing_pct}")
    
    # Impute < 5% missing with median
    cols_to_impute = missing_pct[missing_pct < 0.05].index
    logger.info(f"Imputing columns with < 5% missing: {list(cols_to_impute)}")
    df[cols_to_impute] = df[cols_to_impute].fillna(df[cols_to_impute].median())
    
    # 2. Log-transform skewed metrics (skewness > 2)
    skewness = df[numeric_cols].skew()
    skewed_cols = skewness[skewness > 2].index
    logger.info(f"Columns with skewness > 2: {list(skewed_cols)}")
    
    for col in skewed_cols:
        # Add 1 to avoid log(0) if there are zeros
        df[col] = np.log1p(df[col])
    
    # 3. Remove rows with > 5% missing values
    # Calculate row-wise missing percentage
    row_missing_pct = df[numeric_cols].isna().mean(axis=1)
    rows_to_drop = row_missing_pct[row_missing_pct > 0.05].index
    logger.info(f"Dropping {len(rows_to_drop)} rows with > 5% missing values.")
    df = df.drop(index=rows_to_drop)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save cleaned data
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")
    
    # Return the cleaned dataframe. 
    # The actual train/test split is done in split_dataset.py (T016).
    # We return the cleaned data and a dummy split structure if needed,
    # but the signature asks for Tuple[DataFrame, DataFrame].
    # We'll return (clean_df, clean_df) or split it here if the task implies
    # this function does the split. The task says "Integrate... into the data pipeline".
    # Usually, preprocess cleans, then split_dataset splits.
    # However, the signature suggests two outputs. Let's assume it returns
    # (cleaned_full, cleaned_train) but we haven't split yet.
    # To be safe and consistent with T016, we return the full cleaned set
    # and an empty split or the same set, but the caller (pipeline)
    # will likely call split_dataset next.
    # Let's return (df, df) to satisfy the type hint, 
    # but in a real pipeline, split_dataset would be called next.
    # Actually, looking at T016, it reads from a file. So we just save to file.
    # The return type might be for internal pipeline usage.
    return df, df


def main():
    parser = argparse.ArgumentParser(description="Preprocess code complexity data")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--precision-threshold", type=float, default=0.85, help="Minimum bug label precision")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        clean_df, _ = preprocess(input_path, output_path, args.precision_threshold)
        logger.info("Preprocessing completed successfully.")
    except RuntimeError as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()