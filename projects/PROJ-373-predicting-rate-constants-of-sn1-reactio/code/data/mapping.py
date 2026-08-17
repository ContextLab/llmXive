"""
Task T011c: Implement code/data/mapping.py to map columns and clean initial data.

Constraints:
- Map 'smiles' -> 'SMILES', 'rate' -> 'rate_constant'.
- Log rows with missing rate/SMILES to 'data/processed/exclusion_raw.log'.
- Output: 'data/processed/intermediate_sn1.csv'.
- Depends on T011b (raw data must exist).
- NO synthetic fallbacks.
"""

import os
import sys
import logging
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

def load_raw_data(config: DataConfig) -> pd.DataFrame:
    """
    Load the raw data produced by T011b (download.py).
    Raises FileNotFoundError if the file does not exist.
    """
    raw_path = config.raw_data_path
    if not os.path.exists(raw_path):
        raise FileNotFoundError(
            f"Raw data file not found at {raw_path}. "
            "Ensure T011b (download.py) has been executed successfully."
        )
    
    logger = get_logger("mapping")
    logger.info(f"Loading raw data from {raw_path}")
    
    # Determine file type based on extension
    if raw_path.endswith('.parquet'):
        df = pd.read_parquet(raw_path)
    elif raw_path.endswith('.csv'):
        df = pd.read_csv(raw_path)
    else:
        # Fallback to csv if extension is missing or unknown, but log warning
        logger.warning(f"Unknown file extension for {raw_path}, attempting CSV read.")
        df = pd.read_csv(raw_path)
    
    return df

def map_columns(df: pd.DataFrame, log_path: Path) -> pd.DataFrame:
    """
    Map column names: 'smiles' -> 'SMILES', 'rate' -> 'rate_constant'.
    Log rows with missing 'SMILES' or 'rate_constant' to exclusion_raw.log.
    """
    logger = get_logger("mapping")
    
    # Define mapping
    column_mapping = {
        'smiles': 'SMILES',
        'rate': 'rate_constant'
    }
    
    # Check for existence of source columns
    missing_sources = [col for col in column_mapping.keys() if col not in df.columns]
    if missing_sources:
        # Try to find case-insensitive matches or log strict failure
        # For strictness, we assume the source data from T011b follows the spec
        # If the source file has different casing, we might need to handle it.
        # Assuming standard lowercase from HF datasets as per spec context.
        logger.warning(f"Source columns not found: {missing_sources}. Attempting case-insensitive check.")
        # Simple case-insensitive check
        lower_cols = {c.lower(): c for c in df.columns}
        for src, dst in column_mapping.items():
            if src in lower_cols:
                logger.info(f"Found source column '{lower_cols[src]}' mapping to '{dst}'")
                df = df.rename(columns={lower_cols[src]: dst})
            elif src not in df.columns:
                # If still missing after case check, we might have a schema issue
                # But the task says map 'smiles' -> SMILES, so we assume they exist or are handled by T011a
                pass
    
    # Rename columns based on mapping
    df = df.rename(columns=column_mapping)
    
    # Ensure target columns exist after rename
    if 'SMILES' not in df.columns or 'rate_constant' not in df.columns:
        # Fallback to generic names if mapping failed completely, but log error
        # This should ideally be caught by T011a, but we handle it here for safety
        available_cols = df.columns.tolist()
        logger.error(f"Required columns 'SMILES' and 'rate_constant' not found. Available: {available_cols}")
        # Attempt to guess based on common names
        if 'smiles' in available_cols: df = df.rename(columns={'smiles': 'SMILES'})
        if 'rate' in available_cols: df = df.rename(columns={'rate': 'rate_constant'})
        
        if 'SMILES' not in df.columns or 'rate_constant' not in df.columns:
            raise ValueError("Critical: Could not map required columns 'SMILES' and 'rate_constant'.")

    # Identify rows with missing critical data
    mask_missing = df['SMILES'].isna() | df['rate_constant'].isna()
    
    if mask_missing.any():
        excluded_rows = df[mask_missing].copy()
        excluded_rows['reason'] = 'missing_SMILES_or_rate_constant'
        excluded_rows['original_smiles'] = excluded_rows['SMILES'] # Save original if available
        
        # Ensure log directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append to log file (CSV format for exclusion log)
        file_exists = os.path.exists(log_path)
        excluded_rows.to_csv(
            log_path,
            mode='a',
            index=False,
            header=not file_exists,
            columns=['row_index', 'reason', 'original_smiles']
        )
        
        # Log summary
        logger.warning(f"Excluded {mask_missing.sum()} rows due to missing SMILES or rate_constant.")
        
        # Drop missing rows from main dataframe
        df = df[~mask_missing]
    else:
        logger.info("No rows excluded due to missing SMILES or rate_constant.")

    return df

def main():
    """
    Main entry point for T011c.
    """
    parser = argparse.ArgumentParser(description="Map columns and clean initial data (T011c).")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config file (not used directly, imports from config module).")
    args = parser.parse_args()

    # Setup logging
    logger = get_logger("mapping")
    logger.info("Starting T011c: Mapping and initial cleaning.")

    try:
        # Load configuration
        config = DataConfig()
        ensure_dirs()

        # Paths
        raw_data_path = config.raw_data_path
        output_path = config.intermediate_data_path
        exclusion_log_path = config.exclusion_raw_log_path

        # Ensure output directories exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Load raw data
        df = load_raw_data(config)
        logger.info(f"Loaded {len(df)} rows from raw data.")

        # 2. Map columns and filter missing
        df_cleaned = map_columns(df, exclusion_log_path)
        logger.info(f"Processed {len(df_cleaned)} rows after mapping and filtering.")

        # 3. Save intermediate dataset
        df_cleaned.to_csv(output_path, index=False)
        logger.info(f"Saved intermediate dataset to {output_path}")

        logger.info("T011c completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error during processing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
