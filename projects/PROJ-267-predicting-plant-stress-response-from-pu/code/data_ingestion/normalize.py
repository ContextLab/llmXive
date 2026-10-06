import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np

from utils.logging_config import get_logger, log_warning
from utils.config import get_data_path, get_project_root
from utils.data_utils import load_csv, save_csv

logger = get_logger(__name__)


def calculate_detection_rate(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Calculate the detection rate for each protein (column).

    Args:
        df: DataFrame with proteins as columns.
        threshold: Minimum detection rate to keep a protein.

    Returns:
        DataFrame with detection rates.
    """
    # Assuming non-NaN values are detected
    detection_rates = df.notna().mean()
    return detection_rates


def filter_low_abundance_proteins(
    df: pd.DataFrame,
    min_detection_rate: float = 0.5
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out proteins with low detection rates.

    Args:
        df: Input DataFrame.
        min_detection_rate: Minimum fraction of non-NA values required.

    Returns:
        Tuple of (filtered DataFrame, list of dropped column names).
    """
    rates = calculate_detection_rate(df)
    dropped_cols = rates[rates < min_detection_rate].index.tolist()
    filtered_df = df.drop(columns=dropped_cols)

    logger.info(f"Filtered {len(dropped_cols)} low-abundance proteins")
    return filtered_df, dropped_cols


def apply_lcm_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Left-Censored Missing (LCM) imputation using MinProb algorithm.

    This implementation attempts to use 'imp3' if available, otherwise
    falls back to a custom MinProb implementation.

    Args:
        df: DataFrame with missing values.

    Returns:
        DataFrame with imputed values.
    """
    # Try to import imp3
    try:
        from imp3 import MinProb
        logger.info("Using imp3 MinProb for LCM imputation")
        imputer = MinProb()
        imputed_df = imputer.fit_transform(df)
        return pd.DataFrame(imputed_df, columns=df.columns, index=df.index)
    except ImportError:
        logger.warning("imp3 not found. Using custom MinProb implementation.")
        # Custom MinProb implementation
        # MinProb: impute with value = min(observed) - delta * sigma
        # where delta is typically 1.8 or similar for proteomics
        delta = 1.8
        result_df = df.copy()

        for col in result_df.columns:
            series = result_df[col]
            valid_values = series.dropna()
            if len(valid_values) == 0:
                # If all missing, fill with 0 or mean of row? Log and skip
                log_warning(f"Column {col} has no valid values for imputation")
                result_df[col] = 0
                continue

            min_val = valid_values.min()
            std_val = valid_values.std()
            if std_val == 0:
                impute_val = min_val
            else:
                impute_val = min_val - delta * std_val

            result_df[col] = result_df[col].fillna(impute_val)

        return result_df


def log_deviation(method: str, reason: str):
    """
    Log a deviation from the standard protocol to the deviation log.

    Args:
        method: The method used.
        reason: Reason for the deviation.
    """
    project_root = get_project_root()
    deviation_log_path = project_root / "docs" / "deviation_log.md"

    deviation_log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- [{timestamp}] Method: {method}, Reason: {reason}\n"

    with open(deviation_log_path, 'a', encoding='utf-8') as f:
        f.write(entry)

    logger.info(f"Logged deviation: {method} - {reason}")


def run_normalization_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    min_detection_rate: float = 0.5
) -> Tuple[pd.DataFrame, dict]:
    """
    Run the full normalization pipeline: filter low abundance + LCM imputation.

    Args:
        input_path: Path to input CSV. Defaults to data/processed/merged_matrix.csv.
        output_path: Path to output CSV. Defaults to data/processed/normalized_matrix.csv.
        min_detection_rate: Minimum detection rate for filtering.

    Returns:
        Tuple of (normalized DataFrame, stats dict).
    """
    if input_path is None:
        data_path = get_data_path()
        input_path = data_path / "processed" / "merged_matrix.csv"

    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "processed" / "normalized_matrix.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = load_csv(input_path)

    stats = {
        'initial_shape': df.shape,
        'filtered_columns': [],
        'imputation_method': 'unknown'
    }

    # Filter low abundance
    df_filtered, dropped_cols = filter_low_abundance_proteins(df, min_detection_rate)
    stats['filtered_columns'] = dropped_cols
    stats['after_filter_shape'] = df_filtered.shape

    # Check for imp3 availability
    try:
        import imp3
        stats['imputation_method'] = 'imp3 MinProb'
    except ImportError:
        stats['imputation_method'] = 'Custom MinProb'
        log_deviation("Custom MinProb", "imp3 package not available")

    # Apply LCM imputation
    df_imputed = apply_lcm_imputation(df_filtered)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save result
    save_csv(df_imputed, output_path)
    logger.info(f"Normalized data saved to {output_path}")

    stats['final_shape'] = df_imputed.shape
    stats['output_path'] = str(output_path)

    return df_imputed, stats


def main() -> int:
    """
    Main entry point for the normalization script.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        logger.info("Starting normalization pipeline...")
        df, stats = run_normalization_pipeline()
        logger.info(f"Normalization complete. Final shape: {stats['final_shape']}")
        return 0
    except Exception as e:
        logger.error(f"Normalization pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
