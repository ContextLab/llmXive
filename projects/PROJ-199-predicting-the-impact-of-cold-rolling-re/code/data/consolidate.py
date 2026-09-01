import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import pyarrow.parquet as pq

from utils.logging import get_logger
from config import get_data_path
from data.preprocess import process_ebsd_dataset
from data.error_handling import apply_exclusion_logic

# Ensure we can import from code root if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

logger = get_logger(__name__)

def load_all_processed_datasets() -> pd.DataFrame:
    """
    Load all processed EBSD datasets from the data/interim directory.
    
    Returns:
        pd.DataFrame: Consolidated dataframe of all processed samples.
        
    Raises:
        ValueError: If no valid data files are found or if all data is filtered out.
    """
    data_path = get_data_path()
    interim_dir = data_path / "interim"
    
    if not interim_dir.exists():
        logger.error(f"Interim directory does not exist: {interim_dir}")
        raise FileNotFoundError(f"Interim directory not found: {interim_dir}")
    
    parquet_files = list(interim_dir.glob("*.parquet"))
    csv_files = list(interim_dir.glob("*.csv"))
    
    all_files = parquet_files + csv_files
    
    if not all_files:
        logger.error(f"No processed data files found in {interim_dir}")
        raise ValueError(f"No processed data files found in {interim_dir}. "
                       "Ensure T012 (download) and T014 (preprocess) have run successfully.")
    
    dfs = []
    for file_path in all_files:
        try:
            logger.info(f"Loading {file_path}")
            if file_path.suffix == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Ensure required columns exist
            required_cols = ['material', 'reduction', 'confidence']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"File {file_path} missing columns: {missing_cols}. Skipping.")
                continue
                
            dfs.append(df)
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue
    
    if not dfs:
        raise ValueError("No valid data files could be loaded. Check logs for errors.")
    
    consolidated_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Consolidated {len(consolidated_df)} total rows before final checks")
    
    return consolidated_df

def write_consolidated_parquet(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Write the consolidated dataframe to a Parquet file with metadata.
    
    Args:
        df: The consolidated dataframe.
        output_path: Optional path for the output file. Defaults to data/processed/cleaned_ebsd.parquet.
        
    Returns:
        Path: The path to the written file.
        
    Raises:
        ValueError: If the dataframe is empty.
    """
    if df.empty:
        logger.error("Cannot write empty dataframe. All data may have been filtered out.")
        raise ValueError("Consolidated dataframe is empty. No valid data to output.")
    
    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "processed" / "cleaned_ebsd.parquet"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    metadata = {
        'created_by': 'T015_consolidate',
        'row_count': str(len(df)),
        'columns': str(list(df.columns)),
        'materials': str(df['material'].unique().tolist()),
        'reduction_levels': str(sorted(df['reduction'].unique().tolist()))
    }
    
    # Convert metadata to bytes for PyArrow
    pa_metadata = {k.encode(): v.encode() for k, v in metadata.items()}
    
    # Write to parquet
    table = pq.Table.from_pandas(df)
    table = table.replace_schema_metadata({**table.schema.metadata, **pa_metadata})
    
    pq.write_table(table, output_path)
    
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")
    logger.info(f"Metadata: {metadata}")
    
    return output_path

def main():
    """
    Main entry point for the consolidation script.
    Loads processed data, applies final checks, and writes the consolidated Parquet file.
    """
    logger.info("Starting T015: Consolidated Parquet Output Generation")
    
    try:
        # Load all processed datasets
        df = load_all_processed_datasets()
        
        # Final validation: Check for zero valid rows
        if df.empty:
            logger.error("Consolidated dataframe is empty after loading. Task cannot proceed.")
            raise ValueError("No valid data available for consolidation.")
        
        # Log summary of excluded/missing entries (if any logic was applied during load)
        logger.info(f"Data summary:")
        logger.info(f"  - Materials: {df['material'].unique().tolist()}")
        logger.info(f"  - Reduction levels: {sorted(df['reduction'].unique().tolist())}")
        logger.info(f"  - Total rows: {len(df)}")
        
        # Write consolidated output
        output_path = write_consolidated_parquet(df)
        
        logger.info("T015 completed successfully.")
        return output_path
        
    except Exception as e:
        logger.error(f"T015 failed: {e}")
        raise

if __name__ == "__main__":
    main()