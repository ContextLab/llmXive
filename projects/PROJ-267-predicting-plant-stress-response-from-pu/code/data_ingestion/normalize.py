"""
Data Normalization Pipeline for Plant Stress Response Proteomics.

This module implements:
1. Filtering of low-abundance proteins (detection rate < 50%).
2. Left-Censored Missing (LCM) imputation using the MinProb algorithm.

Dependencies:
- imp3 (preferred)
- code/utils/lcm.py (fallback MinProb implementation if imp3 unavailable)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, List

import pandas as pd
import numpy as np

# Import project utilities
from utils.config import DATA_RAW_PATH, DATA_PROCESSED_PATH, LOG_PATH
from utils.logging_config import get_logger, log_warning

# Configure logging
logger = get_logger(__name__)

# Constants
DETECTION_THRESHOLD = 0.5  # 50% detection rate
LCM_LOG_FILE = "docs/deviation_log.md"


def calculate_detection_rate(df: pd.DataFrame, protein_column: str = "ProteinID") -> pd.Series:
    """
    Calculate the detection rate for each protein across all samples.

    Args:
        df: DataFrame containing protein abundance data.
        protein_column: Name of the column containing protein identifiers.

    Returns:
        Series of detection rates (floats between 0.0 and 1.0).
    """
    if protein_column not in df.columns:
        raise ValueError(f"Column '{protein_column}' not found in DataFrame.")

    # Identify sample columns (exclude metadata columns like ProteinID, Species, etc.)
    sample_cols = [col for col in df.columns if col != protein_column]

    if len(sample_cols) == 0:
        raise ValueError("No sample columns found in DataFrame.")

    # Count non-null entries per protein
    detection_counts = df[sample_cols].notna().sum(axis=1)
    total_samples = len(sample_cols)

    detection_rates = detection_counts / total_samples
    return detection_rates


def filter_low_abundance_proteins(df: pd.DataFrame, threshold: float = DETECTION_THRESHOLD) -> Tuple[pd.DataFrame, int]:
    """
    Filter out proteins with detection rates below the specified threshold.

    Args:
        df: Input DataFrame.
        threshold: Minimum detection rate required (default 0.5).

    Returns:
        Tuple of (filtered DataFrame, count of removed proteins).
    """
    rates = calculate_detection_rate(df)
    mask = rates >= threshold
    filtered_df = df[mask]
    removed_count = len(df) - len(filtered_df)

    if removed_count > 0:
        logger.info(f"Filtered out {removed_count} proteins with detection rate < {threshold*100}%")

    return filtered_df, removed_count


def _get_minprob_imputer():
    """
    Attempt to import imp3. If unavailable, fall back to custom MinProb implementation.

    Returns:
        A callable imputer function or class instance compatible with the workflow.
    """
    try:
        # Attempt to use the preferred 'imp3' package
        from imp3 import MinProb
        logger.info("Using 'imp3' package for LCM imputation.")
        return MinProb()
    except ImportError:
        logger.warning("imp3 package not found. Falling back to custom MinProb implementation in code/utils/lcm.py.")
        log_deviation("LCM Imputation: Using custom MinProb implementation instead of imp3.")
        
        # Import the custom fallback
        # Assuming lcm.py exposes a function or class named MinProbImputer
        try:
            from utils.lcm import MinProbImputer
            return MinProbImputer()
        except ImportError:
            raise ImportError(
                "Neither 'imp3' nor 'utils.lcm.MinProbImputer' is available. "
                "Cannot perform LCM imputation. Please install 'imp3' or fix 'code/utils/lcm.py'."
            )


def apply_lcm_imputation(df: pd.DataFrame, protein_column: str = "ProteinID") -> pd.DataFrame:
    """
    Apply Left-Censored Missing (LCM) imputation using the MinProb algorithm.

    This function:
    1. Identifies numeric sample columns.
    2. Separates the data into observed and missing values.
    3. Imputes missing values using the MinProb algorithm.
    4. Returns the fully imputed DataFrame.

    Args:
        df: DataFrame with protein abundances (NaNs represent missing values).
        protein_column: Column name for protein IDs.

    Returns:
        DataFrame with imputed values.
    """
    logger.info("Applying LCM (MinProb) imputation...")
    
    imputer = _get_minprob_imputer()

    # Identify sample columns (exclude metadata)
    sample_cols = [col for col in df.columns if col != protein_column]
    
    if len(sample_cols) == 0:
        raise ValueError("No numeric sample columns found for imputation.")

    # Extract the data matrix for imputation
    data_matrix = df[sample_cols].values

    # Perform imputation
    # The imputer must handle the matrix and return imputed values
    # We assume the imputer has a .fit_transform() method or similar
    if hasattr(imputer, 'fit_transform'):
        imputed_matrix = imputer.fit_transform(data_matrix)
    elif hasattr(imputer, 'impute'):
        # Fallback for function-based API
        imputed_matrix = imputer.impute(data_matrix)
    else:
        raise RuntimeError(f"Imputer {type(imputer)} does not have a recognized imputation method.")

    # Replace the original data with imputed values
    df_imputed = df.copy()
    df_imputed[sample_cols] = imputed_matrix

    # Verify no NaNs remain in sample columns
    remaining_na = df_imputed[sample_cols].isna().sum().sum()
    if remaining_na > 0:
        log_warning(f"Warning: {remaining_na} missing values remain after imputation.")
    else:
        logger.info("LCM imputation complete. No missing values remaining in sample columns.")

    return df_imputed


def log_deviation(message: str):
    """
    Log a deviation to the deviation log file.
    
    Args:
        message: The deviation message to append.
    """
    log_path = Path(LCM_LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- [{timestamp}] {message}\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(entry)
    logger.info(f"Deviation logged: {message}")


def run_normalization_pipeline(input_path: str, output_path: str) -> Dict[str, any]:
    """
    Execute the full normalization pipeline:
    1. Load data.
    2. Filter low-abundance proteins.
    3. Apply LCM imputation.
    4. Save results.

    Args:
        input_path: Path to input CSV/Parquet file.
        output_path: Path to save the normalized output.

    Returns:
        Dictionary with pipeline statistics.
    """
    logger.info(f"Starting normalization pipeline for {input_path}")
    
    # Load data
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    elif input_path.endswith('.parquet'):
        df = pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path}")
    
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} proteins.")

    # Filter low abundance
    df_filtered, removed_count = filter_low_abundance_proteins(df)
    filtered_count = len(df_filtered)
    
    # Apply LCM Imputation
    df_imputed = apply_lcm_imputation(df_filtered)
    
    # Save results
    if output_path.endswith('.csv'):
        df_imputed.to_csv(output_path, index=False)
    elif output_path.endswith('.parquet'):
        df_imputed.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_path}")
    
    logger.info(f"Saved normalized data to {output_path}")
    
    return {
        "input_rows": initial_count,
        "removed_rows": removed_count,
        "output_rows": filtered_count,
        "output_path": output_path
    }


def main():
    """
    Entry point for the normalization script when run directly.
    Expects input and output paths via command line arguments or defaults.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Normalize proteomic data (Filter + LCM Imputation)")
    parser.add_argument("--input", type=str, default=str(DATA_RAW_PATH / "merged_proteomics.csv"),
                        help="Path to input merged dataset")
    parser.add_argument("--output", type=str, default=str(DATA_PROCESSED_PATH / "normalized_proteomics.csv"),
                        help="Path to save normalized dataset")
    
    args = parser.parse_args()
    
    try:
        stats = run_normalization_pipeline(args.input, args.output)
        print(f"Pipeline completed successfully.")
        print(f"Stats: {stats}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()