"""
Consolidate processed material property data into a single master Parquet file.

This script merges individual property datasets (downloaded and processed separately)
into a unified `data/processed/materials_master.parquet` file. It handles:
- Merging multiple Parquet/CSV files from the raw/processed directories
- Optimizing data types for memory efficiency (float32)
- Adding metadata columns (source, property_name)
- Fallback to CSV if Parquet memory limits are exceeded
- Logging statistics about the consolidated dataset
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

# Import from sibling modules
from config import get_config, require_data_dir
from utils.logging_config import setup_logging, get_logger
from utils.integrity import compute_sha256, log_checksum

# Configure logging
logger = get_logger(__name__)

# Constants
MEMORY_LIMIT_GB = 6.0  # Conservative limit to stay under 7GB total
PARQUET_COMPRESSION = 'snappy'
CHUNK_SIZE = 100000  # Rows to process at a time if needed

def load_processed_data(data_dir: Path) -> List[pd.DataFrame]:
    """
    Load all processed data files from the data directory.
    
    Args:
        data_dir: Path to the processed data directory
        
    Returns:
        List of DataFrames, one per property file
        
    Raises:
        FileNotFoundError: If no data files are found
        ValueError: If no valid data can be loaded
    """
    processed_dir = data_dir / 'processed'
    
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {processed_dir}")
    
    # Find all parquet and csv files
    parquet_files = list(processed_dir.glob('*.parquet'))
    csv_files = list(processed_dir.glob('*.csv'))
    
    # Filter out the master file if it exists (avoid circular loading)
    parquet_files = [f for f in parquet_files if 'master' not in f.name]
    csv_files = [f for f in csv_files if 'master' not in f.name and 'scaling' not in f.name]
    
    all_files = parquet_files + csv_files
    
    if not all_files:
        raise FileNotFoundError(f"No processed data files found in {processed_dir}")
    
    logger.info(f"Found {len(all_files)} data files to consolidate")
    
    dataframes = []
    for file_path in all_files:
        try:
            logger.info(f"Loading {file_path.name}...")
            if file_path.suffix == '.parquet':
                df = pd.read_parquet(file_path)
            elif file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
            else:
                logger.warning(f"Skipping unsupported file type: {file_path}")
                continue
            
            # Extract property name from filename
            property_name = file_path.stem.replace('_processed', '').replace('_raw', '')
            df['property_name'] = property_name
            df['source_file'] = file_path.name
            
            logger.info(f"  Loaded {len(df)} rows from {file_path.name}")
            dataframes.append(df)
            
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            logger.debug(traceback.format_exc())
            continue
    
    if not dataframes:
        raise ValueError("No valid data could be loaded from any files")
    
    return dataframes

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by converting to appropriate dtypes.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with optimized dtypes
    """
    initial_memory = df.memory_usage(deep=True).sum() / (1024 ** 2)
    
    # Convert object columns to category if appropriate
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:  # Low cardinality
            df[col] = df[col].astype('category')
    
    # Convert numeric columns to float32 if precision allows
    for col in df.select_dtypes(include=['float64']).columns:
        if df[col].max() < 3.4e38 and df[col].min() > -3.4e38:
            df[col] = df[col].astype('float32')
    
    # Convert int64 to int32 if possible
    for col in df.select_dtypes(include=['int64']).columns:
        if df[col].max() < 2.1e9 and df[col].min() > -2.1e9:
            df[col] = df[col].astype('int32')
    
    final_memory = df.memory_usage(deep=True).sum() / (1024 ** 2)
    savings = ((initial_memory - final_memory) / initial_memory) * 100
    
    logger.info(f"Memory optimization: {initial_memory:.1f}MB -> {final_memory:.1f}MB ({savings:.1f}% reduction)")
    
    return df

def save_consolidated_data(dataframes: List[pd.DataFrame], output_path: Path, use_csv_fallback: bool = False) -> str:
    """
    Save consolidated data to a single file.
    
    Args:
        dataframes: List of DataFrames to merge
        output_path: Path for the output file
        use_csv_fallback: If True, force CSV output instead of Parquet
        
    Returns:
        Path to the saved file
    """
    logger.info(f"Merging {len(dataframes)} DataFrames...")
    
    # Concatenate all dataframes
    try:
        consolidated = pd.concat(dataframes, ignore_index=True)
    except MemoryError:
        logger.error("Memory error during concatenation. Attempting chunked merge...")
        # Fallback: process in chunks if available
        raise MemoryError("Dataset too large for in-memory concatenation")
    
    logger.info(f"Total consolidated dataset: {len(consolidated)} rows, {len(consolidated.columns)} columns")
    
    # Optimize memory
    consolidated = optimize_dataframe_memory(consolidated)
    
    # Estimate memory usage
    mem_usage = consolidated.memory_usage(deep=True).sum() / (1024 ** 3)  # GB
    logger.info(f"Estimated memory usage: {mem_usage:.2f} GB")
    
    if mem_usage > MEMORY_LIMIT_GB:
        logger.warning(f"Memory usage ({mem_usage:.2f}GB) exceeds limit ({MEMORY_LIMIT_GB}GB)")
        if use_csv_fallback:
            logger.info("Using CSV fallback as requested")
        else:
            logger.warning("Consider enabling CSV fallback for large datasets")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save based on extension
    if output_path.suffix == '.parquet' and not use_csv_fallback:
        try:
            consolidated.to_parquet(output_path, compression=PARQUET_COMPRESSION, index=False)
            logger.info(f"Saved Parquet file: {output_path}")
        except MemoryError:
            logger.warning("Parquet save failed due to memory. Falling back to CSV...")
            output_path = output_path.with_suffix('.csv')
            consolidated.to_csv(output_path, index=False)
            logger.info(f"Saved CSV fallback: {output_path}")
    elif output_path.suffix == '.csv' or use_csv_fallback:
        consolidated.to_csv(output_path, index=False)
        logger.info(f"Saved CSV file: {output_path}")
    else:
        consolidated.to_parquet(output_path, compression=PARQUET_COMPRESSION, index=False)
        logger.info(f"Saved Parquet file: {output_path}")
    
    # Compute checksum
    checksum = compute_sha256(output_path)
    log_checksum(output_path, checksum)
    logger.info(f"Checksum: {checksum}")
    
    return str(output_path)

def main():
    """Main entry point for data consolidation."""
    logger.info("Starting data consolidation...")
    
    try:
        # Get configuration
        config = get_config()
        data_dir = require_data_dir()
        
        # Load all processed data
        dataframes = load_processed_data(data_dir)
        
        # Determine output path
        output_path = Path(data_dir) / 'processed' / 'materials_master.parquet'
        
        # Check if we should use CSV fallback
        use_csv = False
        if len(dataframes) == 1 and len(dataframes[0]) < 10000:
            logger.info("Small dataset detected, using Parquet format")
        else:
            # Estimate if we might hit memory limits
            total_rows = sum(len(df) for df in dataframes)
            if total_rows > 1000000:
                logger.warning("Large dataset detected, preparing for potential memory issues")
                use_csv = False  # Try Parquet first, fallback in save_consolidated_data
        
        # Save consolidated data
        output_file = save_consolidated_data(dataframes, output_path, use_csv_fallback=use_csv)
        
        # Log statistics
        logger.info("Consolidation complete!")
        logger.info(f"Output file: {output_file}")
        
        # Clean up
        del dataframes
        gc.collect()
        
    except Exception as e:
        logger.error(f"Consolidation failed: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    setup_logging()
    main()
