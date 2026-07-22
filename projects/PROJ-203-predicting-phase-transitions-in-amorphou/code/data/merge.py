"""
Merge simulation descriptors with experimental labels.

This module implements T013: Join simulation descriptors with experimental labels
from literature_subset.csv into a temporary merged dataset.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Project imports based on provided API surface
from config import get_data_config, get_paths
from data.validate_literature_subset import main as validate_literature
from utils.logging_config import setup_pipeline_logging, get_missing_data_logger

# Configure logging
logger = logging.getLogger(__name__)
missing_data_logger = get_missing_data_logger()

def load_simulation_descriptors() -> pd.DataFrame:
    """
    Load the intermediate descriptor dataset produced by the simulation pipeline.
    
    Expected source: data/processed/descriptors_batch_{index}.parquet or similar
    For this implementation, we assume a consolidated intermediate file exists
    or we aggregate multiple batch files.
    
    Returns:
        pd.DataFrame: DataFrame containing composition IDs and structural descriptors.
    """
    data_config = get_data_config()
    paths = get_paths()
    
    # Check for consolidated intermediate file first
    intermediate_file = paths.processed / "intermediate_descriptors.parquet"
    
    if intermediate_file.exists():
        logger.info(f"Loading consolidated descriptors from {intermediate_file}")
        df = pd.read_parquet(intermediate_file)
        return df
    
    # Fallback: Try to load from batch files if consolidated doesn't exist
    batch_pattern = paths.processed / "descriptors_batch_*.parquet"
    batch_files = list(paths.processed.glob("descriptors_batch_*.parquet"))
    
    if not batch_files:
        raise FileNotFoundError(
            f"No descriptor files found. Expected {intermediate_file} or "
            f"batch files matching {batch_pattern}"
        )
    
    logger.info(f"Loading {len(batch_files)} batch descriptor files")
    dfs = []
    for batch_file in sorted(batch_files):
        logger.debug(f"Loading batch: {batch_file.name}")
        dfs.append(pd.read_parquet(batch_file))
    
    if not dfs:
        raise FileNotFoundError("No data loaded from batch files")
    
    df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(df)} rows from batch files")
    return df

def load_experimental_labels() -> pd.DataFrame:
    """
    Load experimental thermal properties from the literature subset.
    
    Reads from data/raw/literature_subset.csv after validating its existence.
    
    Returns:
        pd.DataFrame: DataFrame with composition IDs and experimental Tg, Tx values.
    """
    data_config = get_data_config()
    paths = get_paths()
    
    # Validate the literature subset file exists (T009 dependency)
    literature_file = paths.raw / "literature_subset.csv"
    
    if not literature_file.exists():
        missing_data_logger.error(
            f"FATAL: literature_subset.csv missing at {literature_file}"
        )
        raise FileNotFoundError(
            f"FATAL: literature_subset.csv missing or corrupted at {literature_file}. "
            "Run T009 first to validate."
        )
    
    logger.info(f"Loading experimental labels from {literature_file}")
    df = pd.read_csv(literature_file)
    
    # Log column names for debugging
    logger.debug(f"Experimental labels columns: {list(df.columns)}")
    
    return df

def merge_datasets(
    descriptors: pd.DataFrame,
    experimental: pd.DataFrame,
    key_column: str = "composition_id"
) -> pd.DataFrame:
    """
    Join simulation descriptors with experimental labels on composition ID.
    
    Args:
        descriptors: DataFrame with structural descriptors from MD simulations
        experimental: DataFrame with experimental Tg, Tx values
        key_column: Column name to join on (default: composition_id)
    
    Returns:
        pd.DataFrame: Merged DataFrame with both descriptor and experimental data
    """
    logger.info(f"Merging datasets on column: {key_column}")
    
    # Ensure key column exists in both
    if key_column not in descriptors.columns:
        raise KeyError(
            f"Key column '{key_column}' not found in descriptors. "
            f"Available: {list(descriptors.columns)}"
        )
    
    if key_column not in experimental.columns:
        raise KeyError(
            f"Key column '{key_column}' not found in experimental. "
            f"Available: {list(experimental.columns)}"
        )
    
    # Perform inner join to keep only compositions with both data sources
    merged = pd.merge(
        descriptors,
        experimental,
        on=key_column,
        how='inner'
    )
    
    logger.info(f"Merged dataset size: {len(merged)} rows (from {len(descriptors)} descriptors, "
               f"{len(experimental)} experimental)")
    
    # Track dropped rows
    dropped_desc = len(descriptors) - len(merged)
    dropped_exp = len(experimental) - len(merged)
    
    if dropped_desc > 0:
        logger.warning(f"Dropped {dropped_desc} compositions: missing experimental labels")
        missing_data_logger.warning(
            f"{dropped_desc} compositions dropped due to missing experimental labels"
        )
    
    if dropped_exp > 0:
        logger.warning(f"Dropped {dropped_exp} compositions: missing simulation descriptors")
        missing_data_logger.warning(
            f"{dropped_exp} compositions dropped due to missing simulation descriptors"
        )
    
    return merged

def save_merged_dataset(
    merged_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save the merged dataset to a temporary Parquet file.
    
    Args:
        merged_df: The merged DataFrame
        output_path: Optional custom output path. Defaults to data/processed/temp_merged.parquet
    
    Returns:
        Path: Path to the saved file
    """
    paths = get_paths()
    
    if output_path is None:
        output_path = paths.processed / "temp_merged.parquet"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving merged dataset to {output_path}")
    merged_df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved {len(merged_df)} rows to {output_path}")
    return output_path

def main():
    """
    Main entry point for the merge pipeline (T013).
    
    Executes:
    1. Load simulation descriptors
    2. Load experimental labels
    3. Merge on composition_id
    4. Save to temporary Parquet
    """
    setup_pipeline_logging()
    logger.info("Starting T013: Merge simulation descriptors with experimental labels")
    
    try:
        # Step 1: Load descriptors
        descriptors = load_simulation_descriptors()
        logger.info(f"Loaded {len(descriptors)} descriptor rows")
        
        # Step 2: Load experimental labels
        experimental = load_experimental_labels()
        logger.info(f"Loaded {len(experimental)} experimental rows")
        
        # Step 3: Merge datasets
        merged = merge_datasets(descriptors, experimental)
        
        if len(merged) == 0:
            raise RuntimeError(
                "Merged dataset is empty. No compositions found in both sources. "
                "Check composition_id formatting in both datasets."
            )
        
        # Step 4: Save merged dataset
        output_path = save_merged_dataset(merged)
        
        logger.info(f"T013 completed successfully. Output: {output_path}")
        print(f"MERGE_COMPLETE: {output_path}")
        
        return output_path
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except KeyError as e:
        logger.error(f"Key error during merge: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        raise

if __name__ == "__main__":
    main()
