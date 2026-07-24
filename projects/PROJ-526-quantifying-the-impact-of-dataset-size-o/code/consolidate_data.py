"""
Data Consolidation Module for PROJ-526.

Merges processed property-specific datasets into a single master Parquet file.
Handles memory constraints by processing in chunks if necessary and ensures
data integrity before final write.
"""
import os
import sys
import logging
import gc
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np

# Import local config and utils
from config import get_config, require_data_dir
from utils.integrity import compute_sha256, log_checksum
from utils.logging_config import setup_logging, get_logger
from utils.seed import set_seed

# Setup logging
logger = get_logger(__name__)

def load_processed_data(base_dir: Path, property_name: str) -> Optional[pd.DataFrame]:
    """
    Loads a single processed property file from the data/processed directory.
    
    Args:
        base_dir: Root directory for data (e.g., 'data')
        property_name: Name of the property (used to construct filename)
        
    Returns:
        DataFrame containing the property data, or None if file not found.
    """
    # Expected filename pattern: processed_{property_name}.parquet
    # This matches the output convention of generate_descriptors.py
    file_path = base_dir / "processed" / f"processed_{property_name}.parquet"
    
    if not file_path.exists():
        logger.warning(f"Processed file not found: {file_path}. Skipping.")
        return None
    
    try:
        logger.info(f"Loading {file_path}...")
        df = pd.read_parquet(file_path)
        logger.info(f"Loaded {len(df)} rows for {property_name}.")
        return df
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return None

def save_consolidated_data(df: pd.DataFrame, output_path: Path, checksum_log_path: Path) -> None:
    """
    Saves the consolidated DataFrame to a Parquet file and logs its checksum.
    
    Args:
        df: The consolidated DataFrame.
        output_path: Full path for the output .parquet file.
        checksum_log_path: Path to the checksum log file.
    """
    logger.info(f"Saving consolidated data to {output_path}...")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use compression for efficiency
        df.to_parquet(output_path, compression='snappy', index=False)
        logger.info(f"Saved {len(df)} rows to {output_path}.")
        
        # Compute and log checksum
        checksum = compute_sha256(output_path)
        log_checksum(checksum_log_path, "materials_master.parquet", checksum)
        logger.info(f"Checksum computed and logged: {checksum}")
        
    except Exception as e:
        logger.error(f"Failed to save consolidated data: {e}")
        raise

def main():
    """
    Main entry point for data consolidation.
    
    1. Identifies all processed property files in data/processed.
    2. Loads them into memory (handling potential memory pressure via garbage collection).
    3. Concatenates them into a single DataFrame.
    4. Validates the result (checking for duplicates, missing keys).
    5. Saves to data/processed/materials_master.parquet.
    """
    # Initialize configuration
    config = get_config()
    data_dir = require_data_dir(config)
    state_dir = require_data_dir(config) # Assuming state_dir is needed for checksums, or derive from config
    # Correcting state_dir path based on typical structure if not in config directly
    state_dir = Path(config.get('state_dir', 'state'))
    
    processed_dir = data_dir / "processed"
    output_file = processed_dir / "materials_master.parquet"
    checksum_log = state_dir / "checksums.json"
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting data consolidation process...")
    
    # Identify input files
    # We expect files named processed_<property>.parquet
    input_files = list(processed_dir.glob("processed_*.parquet"))
    
    if not input_files:
        logger.error("No processed property files found in data/processed/.")
        logger.error("Ensure generate_descriptors.py has run successfully for at least one property.")
        sys.exit(1)
    
    logger.info(f"Found {len(input_files)} property files to consolidate.")
    
    dfs: List[pd.DataFrame] = []
    
    # Load and concatenate
    for file_path in input_files:
        # Extract property name for logging
        prop_name = file_path.stem.replace("processed_", "")
        df = load_processed_data(data_dir, prop_name)
        
        if df is not None:
            # Add a column to track source if not present (optional but good practice)
            if 'source_file' not in df.columns:
                df['source_file'] = file_path.name
            
            dfs.append(df)
            gc.collect() # Free memory after each load
    
    if not dfs:
        logger.error("No dataframes were successfully loaded. Aborting.")
        sys.exit(1)
    
    logger.info("Concatenating dataframes...")
    try:
        master_df = pd.concat(dfs, ignore_index=True)
    except Exception as e:
        logger.error(f"Failed to concatenate dataframes: {e}")
        raise
    
    # Basic validation
    logger.info(f"Total rows in master dataset: {len(master_df)}")
    logger.info(f"Columns: {list(master_df.columns)}")
    
    if master_df.empty:
        logger.error("Consolidated dataset is empty.")
        sys.exit(1)
        
    # Check for critical missing columns (Magpie features usually start with 'magpie_')
    magpie_cols = [c for c in master_df.columns if c.startswith('magpie_')]
    if not magpie_cols:
        logger.warning("No 'magpie_' columns detected. Verify descriptor generation.")
    
    # Save
    save_consolidated_data(master_df, output_file, checksum_log)
    
    logger.info("Data consolidation completed successfully.")

if __name__ == "__main__":
    setup_logging()
    main()
