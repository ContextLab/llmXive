import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, List

import pandas as pd

# Added import for project-wide logger
from utils.logging_config import get_logger

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
    detection_rates = df.notna().mean()
    logger.info(f"Calculated detection rates for {len(detection_rates)} proteins.")
    return detection_rates

def filter_low_abundance_proteins(df: pd.DataFrame, min_detection_rate: float = 0.5) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out proteins with low detection rates.

    Args:
        df: Input DataFrame.
        min_detection_rate: Minimum fraction of non-NA values required.

    Returns:
        Tuple of (filtered DataFrame, list of dropped column names).
    """
    detection_rates = calculate_detection_rate(df)
    keep_cols = detection_rates[detection_rates >= min_detection_rate].index.tolist()
    dropped_cols = [col for col in df.columns if col not in keep_cols]

    logger.info(f"Filtering low-abundance proteins: keeping {len(keep_cols)} columns, dropping {len(dropped_cols)} columns.")
    if dropped_cols:
        logger.warning(f"Dropped low-abundance protein columns: {dropped_cols}")

    filtered_df = df[keep_cols]
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
    logger.info("Starting LCM imputation.")
    try:
        from imp3 import impute_minprob
        imputed_df = impute_minprob(df)
        logger.info("LCM imputation completed using imp3.")
    except ImportError:
        # Simple MinProb fallback
        logger.warning("imp3 not available; using custom MinProb implementation.")
        imputed_df = df.copy()
        for col in imputed_df.columns:
            if imputed_df[col].isna().any():
                min_val = imputed_df[col].min(skipna=True)
                imputed_df[col].fillna(min_val * 0.5, inplace=True)
        logger.info("LCM imputation completed using custom implementation.")
    return imputed_df

def log_deviation(method: str, reason: str):
    """
    Log a deviation from the standard protocol to the deviation log.

    Args:
        method: The method used.
        reason: Reason for the deviation.
    """
    logger.warning(f"Deviation in method '{method}': {reason}")

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
    logger.info("Starting normalization pipeline.")
    if input_path is None:
        input_path = Path('data') / 'processed' / 'merged_matrix.csv'
    if output_path is None:
        output_path = Path('data') / 'processed' / 'normalized_matrix.csv'

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    filtered_df, dropped_cols = filter_low_abundance_proteins(df, min_detection_rate)
    imputed_df = apply_lcm_imputation(filtered_df)

    logger.info(f"Saving normalized data to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    imputed_df.to_csv(output_path, index=False)

    stats = {
        'initial_columns': df.shape[1],
        'dropped_columns': len(dropped_cols),
        'final_columns': imputed_df.shape[1]
    }
    logger.info(f"Normalization pipeline completed. Stats: {stats}")
    return imputed_df, stats

def main() -> int:
    """
    Main entry point for the normalization script.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        run_normalization_pipeline()
        logger.info("Normalization script executed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Normalization pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
