"""
Preprocessing module for the Social Comparison study.
Handles missing data imputation (MICE) and data normalization.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import pandas as pd
import numpy as np

from data.config import get_config
from utils.logger import get_logger, log_execution_start, log_execution_end
from utils.validators import validate_dataframe_schema

# Try to import miceforest, fallback to sklearn if unavailable
try:
    import miceforest as mf
    MICEFOREST_AVAILABLE = True
except ImportError:
    MICEFOREST_AVAILABLE = False
    try:
        from sklearn.experimental import enable_iterative_imputer  # noqa
        from sklearn.impute import IterativeImputer
        SKLEARN_IMPUTER_AVAILABLE = True
    except ImportError:
        SKLEARN_IMPUTER_AVAILABLE = False

logger = get_logger(__name__)


def calculate_missing_ratio(df: pd.DataFrame, key_vars: list) -> float:
    """
    Calculate the percentage of missing values across key variables.

    Args:
        df: Input DataFrame.
        key_vars: List of column names to check.

    Returns:
        float: Percentage of missing values (0.0 to 100.0).
    """
    if not key_vars:
        return 0.0
    missing_count = df[key_vars].isna().sum().sum()
    total_cells = len(df) * len(key_vars)
    if total_cells == 0:
        return 0.0
    return (missing_count / total_cells) * 100


def preprocess_data(
    df: pd.DataFrame,
    key_vars: Optional[list] = None,
    max_missing_ratio: float = 20.0
) -> Tuple[pd.DataFrame, dict]:
    """
    Preprocess the data: check missingness, impute if necessary, normalize.

    Args:
        df: Input DataFrame.
        key_vars: List of columns to consider for missingness check.
        max_missing_ratio: Maximum allowed missingness percentage (FR-002).

    Returns:
        Tuple of (processed DataFrame, stats dict).
    """
    if key_vars is None:
        key_vars = [
            'avatar_condition',
            'pre_self_esteem',
            'post_self_esteem',
            'comparison_tendency'
        ]

    # Ensure columns exist
    missing_cols = [col for col in key_vars if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    stats = {
        'total_rows': len(df),
        'rows_excluded': 0,
        'missingness_pct': 0.0,
        'imputation_method': None,
        'imputation_success': False
    }

    # 1. Check and exclude rows with > 20% missingness (FR-002)
    # Calculate row-wise missingness
    row_missingness = df[key_vars].isna().sum(axis=1) / len(key_vars)
    exclude_mask = row_missingness > (max_missing_ratio / 100.0)
    rows_excluded = exclude_mask.sum()

    if rows_excluded > 0:
        logger.warning(f"Excluding {rows_excluded} rows with >{max_missing_ratio}% missingness.")
        df_clean = df[~exclude_mask].copy()
        stats['rows_excluded'] = int(rows_excluded)
    else:
        df_clean = df.copy()

    stats['total_rows_after_exclusion'] = len(df_clean)

    # 2. Check overall missingness on remaining data
    overall_missing_pct = calculate_missing_ratio(df_clean, key_vars)
    stats['missingness_pct'] = overall_missing_pct

    # 3. Imputation if missingness > 0 and < threshold
    if overall_missing_pct > 0:
        logger.info(f"Starting imputation. Missingness: {overall_missing_pct:.2f}%")
        imputed_df = impute_data(df_clean, key_vars)
        if imputed_df is not None:
            df_clean = imputed_df
            stats['imputation_success'] = True
        else:
            logger.error("Imputation failed. Proceeding with unimputed data (may cause downstream errors).")
    else:
        logger.info("No missing data found in key variables.")

    # 4. Normalize avatar_condition to 0/1 if binary
    if 'avatar_condition' in df_clean.columns:
        if df_clean['avatar_condition'].dtype in ['int64', 'float64']:
            # Check if it's binary (0/1 or similar)
            unique_vals = df_clean['avatar_condition'].unique()
            if set(unique_vals) <= {0, 1}:
                df_clean['avatar_condition'] = df_clean['avatar_condition'].astype(int)
                logger.info("Normalized avatar_condition to 0/1.")
            else:
                # Attempt to map if it's 1/2 or similar
                min_val = df_clean['avatar_condition'].min()
                max_val = df_clean['avatar_condition'].max()
                if max_val - min_val == 1 and set([min_val, max_val]).issubset({0, 1, 2}):
                    # Map 1->0, 2->1 or 0->0, 1->1 (assuming 0/1 or 1/2)
                    # Standardize to 0/1
                    df_clean['avatar_condition'] = df_clean['avatar_condition'] - min_val
                    logger.info(f"Shifted avatar_condition from [{min_val}, {max_val}] to [0, 1].")
                else:
                    logger.warning(f"avatar_condition has unexpected values: {unique_vals}. Skipping normalization.")

    # 5. Compute change score for LOGGING ONLY (FR-017)
    if 'post_self_esteem' in df_clean.columns and 'pre_self_esteem' in df_clean.columns:
        change_score = df_clean['post_self_esteem'] - df_clean['pre_self_esteem']
        logger.warning("Computed change score (post - pre) for descriptive logging ONLY. "
                     "This is NOT used as the model outcome (ANCOVA used instead).")
        # Do NOT save to disk or return in final df to avoid accidental usage

    return df_clean, stats


def impute_data(df: pd.DataFrame, key_vars: list) -> Optional[pd.DataFrame]:
    """
    Perform Multiple Imputation by Chained Equations (MICE).
    Primary: miceforest. Fallback: sklearn IterativeImputer.

    Args:
        df: DataFrame with missing values.
        key_vars: Columns to impute.

    Returns:
        Imputed DataFrame or None if failure.
    """
    if MICEFOREST_AVAILABLE:
        logger.info("Using miceforest for imputation.")
        try:
            kernel = mf.ImputationKernel(df, datasets=1)
            kernel.mice()
            imputed_df = kernel.complete_data(dataset=0)
            logger.info("miceforest imputation completed successfully.")
            return imputed_df
        except Exception as e:
            logger.error(f"miceforest failed: {e}. Attempting sklearn fallback.")
    elif SKLEARN_IMPUTER_AVAILABLE:
        logger.info("miceforest unavailable. Using sklearn IterativeImputer.")
        try:
            imp = IterativeImputer(random_state=42, max_iter=10, tol=0.01)
            # Only impute key_vars, keep others as is
            data_to_impute = df[key_vars].copy()
            imputed_values = imp.fit_transform(data_to_impute)
            df_imputed = df.copy()
            df_imputed[key_vars] = imputed_values
            logger.info("sklearn IterativeImputer completed successfully.")
            return df_imputed
        except Exception as e:
            logger.error(f"sklearn IterativeImputer failed: {e}.")
    else:
        logger.error("No imputation library available (miceforest or sklearn).")
        return None

    return None


def run_preprocess(input_path: str, output_path: str) -> dict:
    """
    Run the full preprocessing pipeline: load, check, impute, save.

    Args:
        input_path: Path to input CSV (raw or validated).
        output_path: Path to save imputed CSV.

    Returns:
        Stats dictionary.
    """
    log_execution_start(logger, "run_preprocess")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    # Define key variables based on schema
    key_vars = [
        'avatar_condition',
        'pre_self_esteem',
        'post_self_esteem',
        'comparison_tendency'
    ]

    # Run preprocessing
    df_processed, stats = preprocess_data(df, key_vars)

    # Ensure output directory exists
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # CRITICAL OUTPUT: Save to disk (T016a requirement)
    logger.info(f"Saving imputed data to {output_path}")
    df_processed.to_csv(output_path, index=False)
    logger.info("Imputed data saved successfully.")

    log_execution_end(logger, "run_preprocess")
    return stats


def main():
    """
    Entry point for preprocessing script.
    Expects input from data/raw or data/processed (pre-imputation).
    """
    config = get_config()
    input_file = config.get('paths', {}).get('raw_data', 'data/raw/synthetic_data.csv')
    # If raw doesn't exist, check if there's a validated file
    if not os.path.exists(input_file):
        # Fallback to a generic input if specific raw is missing,
        # but in a real pipeline, this should be the output of T012/T013a
        # For T016a, we assume the input is the raw data file.
        # Let's check common paths
        possible_inputs = [
            'data/raw/synthetic_data.csv',
            'data/raw/downloaded_data.csv',
            'data/validated_data.csv'
        ]
        found = False
        for p in possible_inputs:
            if os.path.exists(p):
                input_file = p
                found = True
                break
        if not found:
            # If no input found, we might be in a test environment or need to generate
            # But T016a depends on T012/T013a which should have produced input.
            # We raise an error to fail loudly.
            raise FileNotFoundError("No input data file found for preprocessing.")

    output_file = config.get('paths', {}).get('imputed_data', 'data/processed/imputed_data.csv')

    try:
        stats = run_preprocess(input_file, output_file)
        logger.info(f"Preprocessing stats: {stats}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise


if __name__ == "__main__":
    main()