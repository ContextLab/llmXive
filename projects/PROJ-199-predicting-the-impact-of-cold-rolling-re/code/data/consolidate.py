"""
Consolidation module for aggregating processed EBSD datasets into a single Parquet file.

This module implements T015: Generate consolidated Parquet output to 
data/processed/cleaned_ebsd.parquet with metadata (material, reduction, confidence).

It reads all processed datasets from the data/processed directory (excluding the 
final consolidated file), validates their structure, and writes a unified Parquet 
file with appropriate metadata.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd

from utils.logging import get_logger
from config import get_data_path

# Configure logger
logger = get_logger(__name__)


def load_all_processed_datasets(
    source_dir: Optional[Path] = None,
    exclude_files: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load all processed EBSD datasets from the source directory.
    
    Args:
        source_dir: Directory containing processed EBSD data files. Defaults to 
                   data/processed from config.
        exclude_files: List of filenames to exclude (e.g., the consolidated output file).
                      Defaults to ['cleaned_ebsd.parquet'].
                      
    Returns:
        pd.DataFrame: Concatenated DataFrame of all processed datasets.
                      
    Raises:
        FileNotFoundError: If no valid processed files are found.
        ValueError: If the processed files have incompatible schemas.
    """
    if source_dir is None:
        data_path = get_data_path()
        source_dir = data_path / "processed"
    
    if not source_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {source_dir}")
    
    exclude_files = exclude_files or ["cleaned_ebsd.parquet"]
    
    # Find all Parquet and CSV files
    pattern_files = list(source_dir.glob("*.parquet")) + list(source_dir.glob("*.csv"))
    valid_files = [f for f in pattern_files if f.name not in exclude_files]
    
    if not valid_files:
        raise FileNotFoundError(
            f"No valid processed data files found in {source_dir} "
            f"(excluding {exclude_files})"
        )
    
    logger.info(f"Found {len(valid_files)} processed data files to consolidate")
    
    dfs = []
    for file_path in valid_files:
        logger.info(f"Loading: {file_path.name}")
        if file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        elif file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        else:
            logger.warning(f"Skipping unsupported file format: {file_path}")
            continue
        
        # Validate required columns exist
        required_cols = {"material", "reduction", "confidence_index", "sample_id"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            logger.warning(
                f"File {file_path.name} missing required columns: {missing}. "
                f"Attempting to proceed with available columns."
            )
        
        dfs.append(df)
    
    if not dfs:
        raise FileNotFoundError("No valid data could be loaded from processed files")
    
    # Concatenate all DataFrames
    consolidated_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Consolidated {len(consolidated_df)} total records")
    
    return consolidated_df


def write_consolidated_parquet(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Write the consolidated DataFrame to a Parquet file with metadata.
    
    Args:
        df: The consolidated DataFrame to write.
        output_path: Path for the output Parquet file. Defaults to 
                    data/processed/cleaned_ebsd.parquet.
        metadata: Optional metadata dictionary to embed in the Parquet file.
                
    Returns:
        Path: The path to the written Parquet file.
                
    Raises:
        ValueError: If the DataFrame is empty or missing required columns.
    """
    if df.empty:
        raise ValueError("Cannot write empty DataFrame to Parquet")
    
    required_cols = {"material", "reduction", "confidence_index", "sample_id"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(
            f"DataFrame missing required columns for consolidation: {missing}"
        )
    
    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "processed" / "cleaned_ebsd.parquet"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare metadata
    if metadata is None:
        metadata = {}
    
    # Add standard metadata
    standard_meta = {
        "consolidated_at": pd.Timestamp.now().isoformat(),
        "source": "llmXive pipeline T015",
        "total_records": len(df),
        "materials": sorted(df["material"].unique().tolist()),
        "reductions": sorted(df["reduction"].unique().tolist()),
        "confidence_range": {
            "min": float(df["confidence_index"].min()),
            "max": float(df["confidence_index"].max())
        }
    }
    
    # Merge with user-provided metadata
    final_metadata = {**standard_meta, **metadata}
    
    # Write to Parquet with metadata
    # PyArrow is used under the hood by pandas for Parquet I/O
    df.to_parquet(
        output_path,
        engine="pyarrow",
        index=False,
        # Store metadata in Parquet file properties
        custom_metadata=final_metadata
    )
    
    logger.info(f"Successfully wrote consolidated Parquet to: {output_path}")
    logger.info(f"  - Records: {len(df)}")
    logger.info(f"  - Materials: {standard_meta['materials']}")
    logger.info(f"  - Reductions: {standard_meta['reductions']}")
    
    return output_path


def main() -> None:
    """
    Main entry point for the consolidation script.
    
    This function:
    1. Loads all processed EBSD datasets from data/processed
    2. Validates and consolidates them
    3. Writes the result to data/processed/cleaned_ebsd.parquet
    """
    logger.info("Starting EBSD data consolidation (Task T015)")
    
    try:
        # Load all processed datasets
        consolidated_df = load_all_processed_datasets()
        
        # Write consolidated output
        output_path = write_consolidated_parquet(
            consolidated_df,
            metadata={"pipeline_version": "1.0.0", "task_id": "T015"}
        )
        
        logger.info(f"Consolidation complete. Output: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during consolidation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
