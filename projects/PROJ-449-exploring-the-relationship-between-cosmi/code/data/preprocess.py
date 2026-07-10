"""
Preprocessing module for cosmic ray data.
Calculates composition ratios (He/p, Fe/p, CNO/p) from aligned flux data.
Handles missing/zero proton flux by logging and excluding from ratio calculation.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.align_data import load_flux_data, load_solar_data, merge_datasets
from code.utils.logging import setup_logger, log_missing_flux

def calculate_composition_ratios(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Calculate composition ratios (He/p, Fe/p, CNO/p) from flux data.
    
    Args:
        df: DataFrame containing aligned flux data with columns:
            'date', 'rigidity', 'proton_flux', 'helium_flux', 'heavy_flux', 'cno_flux', 'fe_flux', 'sunspot_number'
        logger: Logger instance for logging events
    
    Returns:
        DataFrame with added ratio columns (He/p, Fe/p, CNO/p)
    """
    # Create a copy to avoid modifying original
    result_df = df.copy()
    
    # Initialize ratio columns with NaN
    result_df['he_p_ratio'] = np.nan
    result_df['fe_p_ratio'] = np.nan
    result_df['cno_p_ratio'] = np.nan
    
    # Identify rows where proton flux is valid (non-zero, non-missing)
    valid_proton_mask = (result_df['proton_flux'].notna()) & (result_df['proton_flux'] > 0)
    
    # Count total rows
    total_rows = len(result_df)
    valid_proton_count = valid_proton_mask.sum()
    
    logger.info(f"Total rows: {total_rows}, Valid proton flux rows: {valid_proton_count}")
    
    # Calculate He/p ratio where proton flux is valid
    if valid_proton_count > 0:
        he_p = result_df.loc[valid_proton_mask, 'helium_flux'] / result_df.loc[valid_proton_mask, 'proton_flux']
        result_df.loc[valid_proton_mask, 'he_p_ratio'] = he_p
        
        # Log any rows where helium flux is missing/zero but proton is valid
        he_missing_mask = valid_proton_mask & (result_df['helium_flux'].isna() | (result_df['helium_flux'] <= 0))
        if len(he_missing_mask) > 0:
            logger.warning(f"Found {he_missing_mask.sum()} rows with valid proton flux but missing/zero helium flux (Below Detection Limit)")
            log_missing_flux(logger, 'helium', he_missing_mask.sum())
    
    # Calculate Fe/p ratio where proton flux is valid
    if valid_proton_count > 0:
        # Check if fe_flux column exists
        if 'fe_flux' in result_df.columns:
            fe_p = result_df.loc[valid_proton_mask, 'fe_flux'] / result_df.loc[valid_proton_mask, 'proton_flux']
            result_df.loc[valid_proton_mask, 'fe_p_ratio'] = fe_p
            
            # Log any rows where iron flux is missing/zero but proton is valid
            fe_missing_mask = valid_proton_mask & (result_df['fe_flux'].isna() | (result_df['fe_flux'] <= 0))
            if len(fe_missing_mask) > 0:
                logger.warning(f"Found {fe_missing_mask.sum()} rows with valid proton flux but missing/zero iron flux (Below Detection Limit)")
                log_missing_flux(logger, 'iron', fe_missing_mask.sum())
        else:
            logger.warning("fe_flux column not found in input data, skipping Fe/p ratio calculation")
    
    # Calculate CNO/p ratio where proton flux is valid (if CNO flux is available)
    if valid_proton_count > 0 and 'cno_flux' in result_df.columns:
        cno_p = result_df.loc[valid_proton_mask, 'cno_flux'] / result_df.loc[valid_proton_mask, 'proton_flux']
        result_df.loc[valid_proton_mask, 'cno_p_ratio'] = cno_p
        
        # Log any rows where CNO flux is missing/zero but proton is valid
        cno_missing_mask = valid_proton_mask & (result_df['cno_flux'].isna() | (result_df['cno_flux'] <= 0))
        if len(cno_missing_mask) > 0:
            logger.warning(f"Found {cno_missing_mask.sum()} rows with valid proton flux but missing/zero CNO flux (Below Detection Limit)")
            log_missing_flux(logger, 'cno', cno_missing_mask.sum())
    elif 'cno_flux' not in result_df.columns:
        logger.info("CNO flux data not available, skipping CNO/p ratio calculation")
    
    # Log rows where proton flux is zero or missing (excluded from all ratio calculations)
    invalid_proton_count = total_rows - valid_proton_count
    if invalid_proton_count > 0:
        logger.warning(f"Found {invalid_proton_count} rows with zero or missing proton flux (Below Detection Limit) - excluded from ratio calculations")
        log_missing_flux(logger, 'proton', invalid_proton_count)
    
    return result_df

def main():
    """
    Main function to run the preprocessing pipeline.
    Reads aligned data, calculates composition ratios, and saves output.
    """
    # Setup logging
    logger = setup_logger('preprocess', 'code/data/preprocess.log')
    logger.info("Starting composition ratio preprocessing")
    
    # Define paths
    input_file = Path('data/processed/unified_timeseries.csv')
    output_file = Path('data/processed/composition_ratios.csv')
    
    # Verify input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run the data alignment pipeline (T013) first to generate unified_timeseries.csv")
        sys.exit(1)
    
    # Load aligned data
    logger.info(f"Loading aligned data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    logger.info(f"Loaded {len(df)} rows of aligned data")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Calculate composition ratios
    logger.info("Calculating composition ratios (He/p, Fe/p, CNO/p)")
    df_ratios = calculate_composition_ratios(df, logger)
    
    # Save output
    logger.info(f"Saving output to {output_file}")
    df_ratios.to_csv(output_file, index=False)
    
    # Log summary statistics
    logger.info(f"Output saved: {len(df_ratios)} rows")
    logger.info(f"He/p ratio range: {df_ratios['he_p_ratio'].min():.4f} to {df_ratios['he_p_ratio'].max():.4f}")
    
    if 'fe_p_ratio' in df_ratios.columns:
        fe_valid = df_ratios['fe_p_ratio'].dropna()
        if len(fe_valid) > 0:
            logger.info(f"Fe/p ratio range: {fe_valid.min():.4f} to {fe_valid.max():.4f}")
    
    if 'cno_p_ratio' in df_ratios.columns:
        cno_valid = df_ratios['cno_p_ratio'].dropna()
        if len(cno_valid) > 0:
            logger.info(f"CNO/p ratio range: {cno_valid.min():.4f} to {cno_valid.max():.4f}")
    
    logger.info("Preprocessing completed successfully")
    
    return df_ratios

if __name__ == '__main__':
    main()