import os
import sys
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from utils.logging_config import get_logger
from utils.config import get_lod_value, get_raw_path, get_processed_path

logger = get_logger(__name__)

def load_cleared_data(input_path: Path) -> pd.DataFrame:
    """Load the Shannon diversity calculated dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    required_cols = ['subject_id', 'titer_baseline', 'titer_post', 'shannon_diversity']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")
    return df

def apply_lod_imputation_and_log_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute LOD values and apply log-transform to titers.
    
    Logic:
    1. Read LOD_VALUE from config.
    2. Identify values below LOD (or 'ND'/'') and impute as 0.5 * LOD.
    3. Apply log10 transform to baseline and post titers.
    4. Add columns 'titer_pre_log' and 'titer_post_log'.
    """
    lod_value = get_lod_value()
    
    if lod_value is None:
        raise RuntimeError("LOD_VALUE is not set in config. Cannot proceed with LOD handling.")
    
    logger.info(f"Using LOD value: {lod_value}")
    logger.info(f"Imputing values < {lod_value} as {0.5 * lod_value}")
    
    # Ensure numeric types, coercing errors to NaN
    df['titer_baseline'] = pd.to_numeric(df['titer_baseline'], errors='coerce')
    df['titer_post'] = pd.to_numeric(df['titer_post'], errors='coerce')
    
    # Imputation: Replace NaN (from 'ND', '', or explicit missing) with 0.5 * LOD
    # Also replace values strictly less than LOD with 0.5 * LOD if they are not already NaN
    # The task description says "impute LOD (0.5 * LOD) for values below detection".
    # Typically, 'ND' is read as NaN. If the raw data has 'ND' as string, to_numeric makes it NaN.
    # We treat NaN as below detection limit.
    
    lod_impute_val = 0.5 * lod_value
    
    # Mask for values that are NaN (missing/ND)
    mask_baseline_na = df['titer_baseline'].isna()
    mask_post_na = df['titer_post'].isna()
    
    # Mask for values < LOD (but not NaN)
    mask_baseline_low = (df['titer_baseline'] < lod_value) & (~df['titer_baseline'].isna())
    mask_post_low = (df['titer_post'] < lod_value) & (~df['titer_post'].isna())
    
    # Log the counts
    logger.info(f"Baseline NA/ND count: {mask_baseline_na.sum()}")
    logger.info(f"Post NA/ND count: {mask_post_na.sum()}")
    logger.info(f"Baseline < LOD count: {mask_baseline_low.sum()}")
    logger.info(f"Post < LOD count: {mask_post_low.sum()}")
    
    # Apply imputation
    # For NA/ND, we set to 0.5 * LOD
    df.loc[mask_baseline_na, 'titer_baseline'] = lod_impute_val
    df.loc[mask_post_na, 'titer_post'] = lod_impute_val
    
    # For values < LOD, we also set to 0.5 * LOD
    df.loc[mask_baseline_low, 'titer_baseline'] = lod_impute_val
    df.loc[mask_post_low, 'titer_post'] = lod_impute_val
    
    # Verify no NaNs remain in titer columns before log
    if df['titer_baseline'].isna().any() or df['titer_post'].isna().any():
        raise ValueError("Still have NaN values in titer columns after imputation.")
        
    # Apply Log10 Transform
    # Add small epsilon if there are exact zeros to avoid log(0), though imputation should handle it
    # If imputation set everything to 0.5*Lod, and Lod > 0, then log is safe.
    # Just in case Lod was 0 (unlikely), handle it.
    if lod_value <= 0:
        logger.warning("LOD value is <= 0. Adding small epsilon for log transform.")
        epsilon = 1e-9
        df['titer_pre_log'] = np.log10(df['titer_baseline'] + epsilon)
        df['titer_post_log'] = np.log10(df['titer_post'] + epsilon)
    else:
        df['titer_pre_log'] = np.log10(df['titer_baseline'])
        df['titer_post_log'] = np.log10(df['titer_post'])
        
    logger.info("Log transform completed.")
    return df

def write_updated_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Write the processed dataframe to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Written updated dataset to {output_path}")

def run_log_titer_pipeline(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
    """
    Main pipeline function to load, transform, and save.
    """
    if input_path is None:
        input_path = get_processed_path() / "cleared_shannon.csv"
    if output_path is None:
        output_path = get_processed_path() / "cleared_shannon_log.csv"
        
    logger.info(f"Starting log titer pipeline. Input: {input_path}, Output: {output_path}")
    
    df = load_cleared_data(input_path)
    df_transformed = apply_lod_imputation_and_log_transform(df)
    write_updated_dataset(df_transformed, output_path)
    
    return output_path

def main():
    """Entry point for the script."""
    # Ensure logging is configured
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        output_file = run_log_titer_pipeline()
        logger.info(f"Pipeline completed successfully. Output: {output_file}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
