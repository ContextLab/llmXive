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

def load_cleared_data(input_path: Path) -> pd.DataFrame:
    """Load the normalized data from the previous step."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['subject_id', 'titer_baseline', 'titer_post']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    return df

def apply_lod_imputation_and_log_transform(
    df: pd.DataFrame, 
    lod_value: float
) -> pd.DataFrame:
    """
    Impute missing/ND titers as 0.5 * LOD and apply log10 transformation.
    
    Steps:
    1. Ensure titer columns are numeric.
    2. Impute 'ND', '', or NaN values with 0.5 * LOD.
    3. Apply log10 transformation to create titer_pre_log and titer_post_log.
    4. Handle any resulting -inf (if 0 was imputed and lod was 0, though unlikely)
       by setting to a small epsilon or keeping as NaN if strictly required.
    """
    if lod_value is None or lod_value <= 0:
        raise ConfigurationError("LOD_VALUE must be a positive number.")

    df = df.copy()
    
    # Ensure columns are numeric
    for col in ['titer_baseline', 'titer_post']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Imputation logic: 0.5 * LOD
    impute_val = 0.5 * lod_value
    logger.info(f"Imputing missing/ND titers with 0.5 * LOD = {impute_val}")
    
    # Replace 'ND' strings if they survived previous steps, or handle NaN
    # The ingestion step (T011d) should have handled string 'ND', 
    # but we ensure numeric NaNs are handled here.
    df['titer_baseline'] = df['titer_baseline'].fillna(impute_val)
    df['titer_post'] = df['titer_post'].fillna(impute_val)
    
    # Check for any remaining zeros or negatives before log (safety)
    if (df['titer_baseline'] <= 0).any() or (df['titer_post'] <= 0).any():
        logger.warning("Found non-positive titer values after imputation. "
                     "These will result in -inf or NaN after log10. "
                     "This may indicate an LOD of 0 or data issue.")
    
    # Log Transform
    df['titer_pre_log'] = np.log10(df['titer_baseline'])
    df['titer_post_log'] = np.log10(df['titer_post'])
    
    # Handle -inf (from log10(0)) if it occurred (shouldn't with 0.5*LOD > 0)
    # If LOD was > 0, 0.5*LOD > 0, so log10 is finite.
    # We keep -inf/NaN as is for downstream handling if necessary, 
    # but typically this shouldn't happen with valid LOD.
    
    return df

def write_updated_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Write the processed dataframe to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote updated dataset to {output_path}")

def run_log_titer_pipeline() -> None:
    """Main entry point for the log titer transformation task."""
    # Paths
    input_file = Path("data/processed/cleared_norm.csv")
    output_file = Path("data/processed/cleared_log.csv")
    
    # Configuration
    lod_value = get_lod_value()
    
    logger.info("Starting Log-Transform Titers & LOD Handling (T021)")
    
    if lod_value is None:
        logger.error("LOD_VALUE is not set in configuration. Aborting.")
        raise ConfigurationError("LOD_VALUE must be explicitly set in config. No default allowed.")
    
    try:
        # 1. Load
        df = load_cleared_data(input_file)
        
        # 2. Transform
        df_transformed = apply_lod_imputation_and_log_transform(df, lod_value)
        
        # 3. Write
        write_updated_dataset(df_transformed, output_file)
        
        # Log success
        logger.info(f"Pipeline completed. Output: {output_file}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pipeline: {e}")
        sys.exit(1)

def main():
    run_log_titer_pipeline()

if __name__ == "__main__":
    main()
