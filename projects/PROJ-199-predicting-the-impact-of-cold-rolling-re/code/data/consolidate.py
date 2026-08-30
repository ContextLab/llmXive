"""
Consolidates preprocessed EBSD data into a single Parquet file.

This module implements T015: Generate consolidated Parquet output to 
data/processed/cleaned_ebsd.parquet with metadata.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from config import get_data_path

logger = get_logger(__name__)

def load_all_processed_datasets() -> pd.DataFrame:
    """
    Loads all preprocessed EBSD datasets from the data/processed/interim directory.
    
    Returns:
        pd.DataFrame: Concatenated DataFrame of all valid datasets.
        
    Raises:
        FileNotFoundError: If no valid data files are found.
        ValueError: If no valid rows remain after filtering.
    """
    data_path = get_data_path()
    interim_dir = data_path / "interim"
    
    if not interim_dir.exists():
        logger.warning(f"Interim directory not found at {interim_dir}. Attempting to find processed data.")
        interim_dir = data_path / "processed"
    
    if not interim_dir.exists():
        raise FileNotFoundError(f"Data processing directory not found: {interim_dir}")
    
    # Look for parquet files in interim or processed directories
    parquet_files = list(interim_dir.glob("*.parquet"))
    if not parquet_files:
        # Fallback to processed directory if interim is empty
        processed_dir = data_path / "processed"
        if processed_dir.exists():
            parquet_files = list(processed_dir.glob("*.parquet"))
    
    if not parquet_files:
        raise FileNotFoundError("No preprocessed Parquet files found in data/processed or data/interim.")
    
    logger.info(f"Found {len(parquet_files)} preprocessed dataset(s) to consolidate.")
    
    dfs = []
    for file_path in parquet_files:
        try:
            df = pd.read_parquet(file_path)
            if df.empty:
                logger.warning(f"Skipping empty file: {file_path}")
                continue
            
            # Ensure required columns exist
            required_cols = ['material', 'reduction', 'confidence']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"File {file_path} missing columns: {missing_cols}. Attempting to proceed with available data.")
            
            dfs.append(df)
            logger.info(f"Loaded {len(df)} rows from {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue
    
    if not dfs:
        raise ValueError("No valid data rows found in any preprocessed files.")
    
    consolidated_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Consolidated total of {len(consolidated_df)} rows across {len(dfs)} files.")
    
    # Final validation: ensure we have at least some valid data
    if consolidated_df.empty:
        raise ValueError("Consolidated DataFrame is empty. No valid data available.")
    
    return consolidated_df

def write_consolidated_parquet(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Writes the consolidated DataFrame to a Parquet file with metadata.
    
    Args:
        df: The consolidated DataFrame.
        output_path: Optional path for the output file. Defaults to data/processed/cleaned_ebsd.parquet.
        
    Returns:
        str: The path to the written file.
        
    Raises:
        ValueError: If the input DataFrame is empty.
    """
    if df.empty:
        raise ValueError("Cannot write empty DataFrame to Parquet. Zero valid rows found.")
    
    data_path = get_data_path()
    processed_dir = data_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    if output_path is None:
        output_path = str(processed_dir / "cleaned_ebsd.parquet")
    
    # Ensure output path is absolute and within project
    output_path = Path(output_path).resolve()
    if not str(output_path).startswith(str(project_root)):
        raise ValueError(f"Output path {output_path} is outside project root.")
    
    # Add metadata to Parquet
    metadata = {
        b'created_by': b'code/data/consolidate.py (T015)',
        b'description': b'Consolidated cleaned EBSD data with metadata (material, reduction, confidence)',
        b'row_count': str(len(df)).encode(),
        b'columns': ','.join(df.columns).encode(),
    }
    
    # Convert to PyArrow Table to add metadata
    table = pa.Table.from_pandas(df)
    existing_metadata = table.schema.metadata or {}
    merged_metadata = {**existing_metadata, **metadata}
    table = table.replace_schema_metadata(merged_metadata)
    
    # Write Parquet
    pq.write_table(table, output_path, compression='snappy')
    
    logger.info(f"Wrote consolidated Parquet to {output_path} ({len(df)} rows)")
    logger.info(f"Metadata summary: {dict(metadata)}")
    
    return str(output_path)

def main():
    """
    Main entry point for the consolidation script.
    """
    try:
        logger.info("Starting EBSD data consolidation (T015)...")
        
        # Load all processed datasets
        consolidated_df = load_all_processed_datasets()
        
        # Log summary of excluded/missing entries
        total_rows = len(consolidated_df)
        logger.info(f"Total valid rows available: {total_rows}")
        
        # Check for specific metadata completeness
        meta_cols = ['material', 'reduction', 'confidence']
        for col in meta_cols:
            if col in consolidated_df.columns:
                null_count = consolidated_df[col].isna().sum()
                if null_count > 0:
                    logger.warning(f"Column '{col}' has {null_count} missing values.")
                else:
                    logger.info(f"Column '{col}' is complete.")
        
        # Write to Parquet
        output_path = write_consolidated_parquet(consolidated_df)
        
        logger.info(f"Consolidation complete. Output: {output_path}")
        return 0
        
    except ValueError as e:
        logger.error(f"Data validation failed: {e}")
        logger.error("Zero valid rows found. Cannot generate output file.")
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during consolidation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())