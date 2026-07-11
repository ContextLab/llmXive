import os
import sys
import logging
from pathlib import Path
import pandas as pd
from astroquery.mast import Observations
from astropy.table import Table

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.retry import retry_call, retry_with_backoff
from utils.logging_config import get_logger
from ingest.download_dr25 import fetch_dr25_planet_table
from ingest.download_kic import fetch_kic_catalog

logger = get_logger(__name__)

def merge_catalogs(dr25_path: str, kic_path: str, output_path: str) -> pd.DataFrame:
    """
    Merge Kepler DR25 Planet Table and KIC (Kepler Input Catalog) on KIC ID.
    
    Args:
        dr25_path: Path to the DR25 raw CSV file
        kic_path: Path to the KIC raw CSV file
        output_path: Path where the merged CSV will be saved
        
    Returns:
        Merged DataFrame containing planet data with stellar parameters
    """
    logger.info(f"Loading DR25 data from {dr25_path}")
    if not os.path.exists(dr25_path):
        raise FileNotFoundError(f"DR25 file not found: {dr25_path}")
    dr25_df = pd.read_csv(dr25_path)
    
    logger.info(f"Loading KIC data from {kic_path}")
    if not os.path.exists(kic_path):
        raise FileNotFoundError(f"KIC file not found: {kic_path}")
    kic_df = pd.read_csv(kic_path)
    
    # Identify the KIC ID column names in both datasets
    # DR25 typically uses 'koi_pname' or 'kepid', KIC uses 'kepid'
    dr25_id_col = None
    kic_id_col = None
    
    # Check for common column names
    possible_id_cols = ['kepid', 'KIC', 'koi_pname', 'kepler_id', 'oid']
    
    for col in possible_id_cols:
        if col in dr25_df.columns:
            dr25_id_col = col
            break
        # Also check case-insensitive
        for c in dr25_df.columns:
            if c.lower() == col.lower():
                dr25_id_col = c
                break
        if dr25_id_col:
            break
            
    for col in possible_id_cols:
        if col in kic_df.columns:
            kic_id_col = col
            break
        for c in kic_df.columns:
            if c.lower() == col.lower():
                kic_id_col = c
                break
        if kic_id_col:
            break
    
    if not dr25_id_col:
        raise ValueError("Could not find KIC ID column in DR25 data")
    if not kic_id_col:
        raise ValueError("Could not find KIC ID column in KIC data")
        
    logger.info(f"Merging on DR25 column '{dr25_id_col}' and KIC column '{kic_id_col}'")
    
    # Ensure ID columns are of the same type for merging (usually int or string)
    # Convert to string to handle potential NaNs or type mismatches
    dr25_df[dr25_id_col] = dr25_df[dr25_id_col].astype(str)
    kic_df[kic_id_col] = kic_df[kic_id_col].astype(str)
    
    # Perform inner merge to keep only planets with stellar parameters
    merged_df = pd.merge(
        dr25_df,
        kic_df,
        left_on=dr25_id_col,
        right_on=kic_id_col,
        how='inner'
    )
    
    logger.info(f"Merged dataset size: {len(merged_df)} rows")
    logger.info(f"Columns in merged dataset: {merged_df.columns.tolist()}")
    
    # Save to output path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Merged catalog saved to {output_path}")
    
    return merged_df

def main():
    """Main entry point for merging catalogs."""
    # Define paths based on project structure
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    
    dr25_path = data_raw_dir / "dr25_raw.csv"
    kic_path = data_raw_dir / "kic_raw.csv"
    output_path = data_raw_dir / "merged_catalog.csv"
    
    # Ensure directories exist
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting catalog merge process")
    
    try:
        # Check if source files exist, if not attempt to download them
        if not dr25_path.exists():
            logger.warning(f"DR25 file not found at {dr25_path}. Attempting download...")
            fetch_dr25_planet_table(str(dr25_path))
            
        if not kic_path.exists():
            logger.warning(f"KIC file not found at {kic_path}. Attempting download...")
            fetch_kic_catalog(str(kic_path))
        
        # Perform the merge
        merge_catalogs(
            dr25_path=str(dr25_path),
            kic_path=str(kic_path),
            output_path=str(output_path)
        )
        
        logger.info("Catalog merge completed successfully")
        
    except Exception as e:
        logger.error(f"Error during catalog merge: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()