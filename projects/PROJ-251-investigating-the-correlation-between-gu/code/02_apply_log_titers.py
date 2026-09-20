import os
import sys
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from utils.config import get_lod_value, get_env_var
from utils.logging_config import get_logger

logger = get_logger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""
    pass

def load_cleared_data(input_path: str) -> pd.DataFrame:
    """
    Load the cleared dataset from the specified path.
    
    Args:
        input_path: Path to the input CSV file (data/processed/cleared.csv).
        
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    
    required_cols = ['subject_id', 'titer_baseline', 'titer_post']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def apply_lod_imputation_and_log_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute LOD values and apply log-transform to titer columns.
    
    Logic:
    1. Retrieve LOD_VALUE from config. Raise ConfigurationError if not set.
    2. Impute missing/ND values in titer_baseline and titer_post as 0.5 * LOD_VALUE.
    3. Ensure all titer columns are numeric.
    4. Apply log10 transform to create titer_pre_log and titer_post_log.
    
    Args:
        df: The cleared dataset.
        
    Returns:
        pd.DataFrame: The dataset with new log-transformed columns.
        
    Raises:
        ConfigurationError: If LOD_VALUE is not set in config.
    """
    lod_value = get_lod_value()
    
    if lod_value is None:
        raise ConfigurationError("LOD_VALUE must be explicitly set in config. No default allowed.")
    
    logger.info(f"Using LOD_VALUE: {lod_value} for imputation")
    
    # Create a copy to avoid SettingWithCopyWarning
    result_df = df.copy()
    
    # Identify titer columns
    titer_cols = ['titer_baseline', 'titer_post']
    
    # Ensure numeric, coercing errors to NaN
    for col in titer_cols:
        result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
    
    # Impute missing/ND values (NaN after to_numeric)
    impute_value = 0.5 * lod_value
    for col in titer_cols:
        null_count = result_df[col].isna().sum()
        if null_count > 0:
            logger.info(f"Imputing {null_count} missing values in {col} with {impute_value}")
            result_df[col] = result_df[col].fillna(impute_value)
    
    # Apply log10 transform
    # Add a small epsilon if there's a risk of log(0), though imputation should handle it
    # Given LOD is positive, 0.5 * LOD is positive.
    result_df['titer_pre_log'] = np.log10(result_df['titer_baseline'])
    result_df['titer_post_log'] = np.log10(result_df['titer_post'])
    
    logger.info("Log-transform applied successfully")
    return result_df

def write_updated_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Write the updated dataset to the specified CSV path.
    
    Args:
        df: The DataFrame to write.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Written {len(df)} rows to {output_path}")

def run_log_titer_pipeline(input_path: str, output_path: str) -> None:
    """
    Orchestrate the log-transform pipeline.
    
    Args:
        input_path: Path to input CSV (cleared.csv).
        output_path: Path to output CSV (cleared_log.csv).
    """
    try:
        df = load_cleared_data(input_path)
        df_transformed = apply_lod_imputation_and_log_transform(df)
        write_updated_dataset(df_transformed, output_path)
        logger.info("Pipeline completed successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    """Main entry point for the script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "processed" / "cleared.csv"
    output_path = project_root / "data" / "processed" / "cleared_log.csv"
    
    logger.info(f"Starting log-titer pipeline. Input: {input_path}, Output: {output_path}")
    run_log_titer_pipeline(str(input_path), str(output_path))

if __name__ == "__main__":
    main()
