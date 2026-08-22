import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

from download import get_file_hash
from logging_config import (
    setup_logging,
    get_module_logger,
    log_operation_start,
    log_operation_complete,
    log_data_filter_step,
    log_skipped_row,
)
from power_calc import calculate_power_cohen_d

# Ensure the logger is configured with the project's specific setup
logger = get_module_logger(__name__)

class DataFetchError(Exception):
    """Raised when the raw data file is missing or fetch fails."""
    pass

def load_raw_data(raw_data_path: Path) -> pd.DataFrame:
    """
    Load raw data from the specified path.
    
    Args:
        raw_data_path: Path to the raw data CSV file.
        
    Returns:
        DataFrame containing the raw data.
        
    Raises:
        DataFetchError: If the file does not exist.
    """
    if not raw_data_path.exists():
        log_operation_start(logger, "load_raw_data", f"Checking path: {raw_data_path}")
        raise DataFetchError(f"Raw data file not found at {raw_data_path}. "
                             "Please run code/download.py first to fetch data.")
    
    log_operation_start(logger, "load_raw_data", f"Loading raw data from: {raw_data_path}")
    try:
        df = pd.read_csv(raw_data_path)
        log_operation_complete(logger, "load_raw_data", f"Loaded {len(df)} rows.")
        return df
    except Exception as e:
        log_operation_start(logger, "load_raw_data", f"Error loading data: {e}")
        raise

def filter_missing_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows where critical columns are missing or NaN.
    Logs each skipped row as per FR-008.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Filtered DataFrame.
    """
    log_operation_start(logger, "filter_missing_rows", "Starting missing row filtering.")
    
    critical_cols = ['year', 'effect_size', 'sample_size']
    missing_mask = df[critical_cols].isna().any(axis=1)
    rows_to_drop = df[missing_mask].index.tolist()
    
    if len(rows_to_drop) > 0:
        log_data_filter_step(logger, "filter_missing_rows", 
                             reason="Missing critical columns (year, effect_size, sample_size)",
                             rows_affected=len(rows_to_drop))
        for idx in rows_to_drop:
            row_data = df.loc[idx]
            missing_cols = [col for col in critical_cols if pd.isna(row_data[col])]
            log_skipped_row(logger, idx, missing_cols)
    
    filtered_df = df.dropna(subset=critical_cols)
    log_operation_complete(logger, "filter_missing_rows", 
                           f"Filtered {len(rows_to_drop)} rows. Remaining: {len(filtered_df)}.")
    return filtered_df

def compute_power_estimates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate power estimates for the cleaned data using Cohen's d.
    
    Args:
        df: Filtered DataFrame.
        
    Returns:
        DataFrame with added 'power_estimate' column.
    """
    log_operation_start(logger, "compute_power_estimates", "Calculating power estimates.")
    
    # Apply power calculation row-wise
    # Assuming effect_size is Cohen's d or convertible. 
    # If effect_size is d, n1=n2=n/2 for two-sample t-test logic usually, 
    # but here we assume sample_size is the total N and we use the helper.
    # The helper calculate_power_cohen_d expects d, n1, n2. 
    # For a two-group design, n1 = n2 = sample_size / 2.
    
    def calc_row_power(row):
        try:
            n_total = row['sample_size']
            if n_total < 2:
                return np.nan
            n1 = n_total / 2
            n2 = n_total / 2
            d = row['effect_size']
            return calculate_power_cohen_d(d, n1, n2, alpha=0.05)
        except Exception as e:
            logger.warning(f"Could not calculate power for row {row.name}: {e}")
            return np.nan

    df['power_estimate'] = df.apply(calc_row_power, axis=1)
    
    # Log any resulting NaNs in power estimate
    nan_power_count = df['power_estimate'].isna().sum()
    if nan_power_count > 0:
        log_data_filter_step(logger, "compute_power_estimates", 
                             reason="Power calculation resulted in NaN",
                             rows_affected=nan_power_count)
    
    log_operation_complete(logger, "compute_power_estimates", 
                           f"Computed power estimates for {len(df)} rows.")
    return df

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the cleaned and processed DataFrame to CSV.
    
    Args:
        df: The processed DataFrame.
        output_path: Path to save the CSV file.
    """
    log_operation_start(logger, "save_cleaned_data", f"Saving cleaned data to: {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    
    log_operation_complete(logger, "save_cleaned_data", 
                           f"Saved {len(df)} rows to {output_path}")
    logger.info(f"Artifact written: {output_path}")

def main():
    """Main entry point for the preprocessing script."""
    setup_logging()
    project_root = Path(__file__).parent.parent
    raw_data_path = project_root / "data" / "raw" / "data.csv"
    output_path = project_root / "data" / "derived" / "cleaned_data.csv"
    
    log_operation_start(logger, "preprocess_pipeline", "Starting preprocessing pipeline.")
    
    try:
        # 1. Load Raw Data
        df = load_raw_data(raw_data_path)
        
        # 2. Filter Missing Rows
        df_clean = filter_missing_rows(df)
        
        # 3. Compute Power Estimates
        df_final = compute_power_estimates(df_clean)
        
        # 4. Save Output
        save_cleaned_data(df_final, output_path)
        
        log_operation_complete(logger, "preprocess_pipeline", "Pipeline completed successfully.")
        
    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()