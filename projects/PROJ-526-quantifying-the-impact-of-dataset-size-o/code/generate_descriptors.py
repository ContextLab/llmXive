"""
generate_descriptors.py

Computes Magpie composition-only descriptors for all entries in the raw material data.
Reads from data/raw/ (Parquet/CSV) and outputs to data/processed/materials_master.parquet.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import utilities from the project
from config import get_config, require_data_dir
from utils.logging_config import setup_logging, get_logger, log_descriptor_stats
from utils.seed import set_seed
from utils.integrity import compute_sha256, log_checksum

# Import Magpie descriptor generation from matminer
try:
    from matminer.featurizers.composition import MagpieData
except ImportError:
    raise ImportError(
        "The 'matminer' package is required for Magpie descriptor generation. "
        "Please install it via 'pip install matminer' and ensure 'pymatgen' is also installed."
    )

# Setup logging
logger = get_logger(__name__)

def load_raw_materials(input_dir: Path) -> pd.DataFrame:
    """
    Loads all material data from the raw input directory.
    Supports .parquet and .csv files.
    """
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    dataframes = []
    supported_extensions = ['.parquet', '.csv']

    # Find all supported files
    files = [f for f in input_dir.iterdir() if f.suffix in supported_extensions]
    
    if not files:
        raise FileNotFoundError(f"No supported data files (.parquet, .csv) found in {input_dir}")

    for file_path in sorted(files):
        logger.info(f"Loading file: {file_path.name}")
        try:
            if file_path.suffix == '.parquet':
                df = pd.read_parquet(file_path)
            elif file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
            
            # Basic validation
            if df.empty:
                logger.warning(f"File {file_path.name} is empty. Skipping.")
                continue

            # Ensure composition column exists (expected by Magpie)
            # Common names: 'composition', 'formula', 'comp'
            comp_col = None
            for col in ['composition', 'formula', 'comp', 'Composition']:
                if col in df.columns:
                    comp_col = col
                    break
            
            if not comp_col:
                # Try to infer if there's a column with 'comp' in name
                candidates = [c for c in df.columns if 'comp' in c.lower()]
                if candidates:
                    comp_col = candidates[0]
                    logger.warning(f"Assuming '{comp_col}' is the composition column.")
                else:
                    raise ValueError(
                        f"Could not find a composition column in {file_path.name}. "
                        f"Expected columns: 'composition', 'formula', 'comp'. Found: {list(df.columns)}"
                    )

            # Standardize composition column name for downstream processing
            df = df.rename(columns={comp_col: 'composition'})
            dataframes.append(df)
            logger.info(f"Loaded {len(df)} rows from {file_path.name}")

        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            raise

    if not dataframes:
        raise ValueError("No valid data could be loaded from the input directory.")

    # Concatenate all dataframes
    logger.info(f"Concatenating {len(dataframes)} dataframes...")
    master_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Total rows loaded: {len(master_df)}")
    
    return master_df

def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validates the input dataframe has necessary columns for Magpie descriptors.
    """
    required_cols = ['composition']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for descriptor generation: {missing}")
    
    # Check for non-null compositions
    null_count = df['composition'].isnull().sum()
    if null_count > 0:
        logger.warning(f"Found {null_count} null compositions. Dropping them.")
        df = df.dropna(subset=['composition'])
    
    if len(df) == 0:
        raise ValueError("No valid compositions remaining after cleaning.")

def compute_magpie_descriptors(df: pd.DataFrame, chunk_size: int = 5000) -> pd.DataFrame:
    """
    Computes Magpie composition descriptors for the dataframe.
    Processes in chunks to manage memory.
    """
    logger.info("Initializing Magpie featurizer...")
    # MagpieData is a standard featurizer in matminer
    # It generates 145 features by default (elemental property stats)
    featurizer = MagpieData()
    
    # Validate input
    validate_dataframe(df)
    
    logger.info(f"Starting descriptor generation for {len(df)} entries...")
    all_features = []
    
    # Process in chunks to avoid memory spikes
    total_rows = len(df)
    for i in range(0, total_rows, chunk_size):
        chunk_end = min(i + chunk_size, total_rows)
        chunk = df.iloc[i:chunk_end]
        
        logger.info(f"Processing chunk {i//chunk_size + 1}: rows {i} to {chunk_end-1}")
        
        try:
            # Featurize the composition column
            # MagpieData.featurize_dataframe expects the column name and returns new columns
            # We use 'composition' as the target column
            chunk_features = featurizer.featurize_dataframe(
                chunk, 
                col_id='composition',
                ignore_errors=False, # Fail loudly on bad composition
                pbar=True
            )
            
            # Keep original columns + new features
            # Ensure we don't drop the original data if needed later, 
            # but typically we want the features + the label/property columns
            # The input df likely has 'property_value' and 'property_name'
            # We keep them.
            all_features.append(chunk_features)
            
        except Exception as e:
            logger.error(f"Error processing chunk {i//chunk_size + 1}: {e}")
            raise

    logger.info("Concatenating feature chunks...")
    result_df = pd.concat(all_features, ignore_index=True)
    
    # Log stats
    log_descriptor_stats(result_df)
    
    return result_df

def save_master_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the master dataset with descriptors to the specified path.
    Uses Parquet format for efficiency.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving master dataset to {output_path}...")
    
    # Save as Parquet
    df.to_parquet(output_path, index=False)
    
    # Compute and log checksum for integrity
    checksum = compute_sha256(output_path)
    log_checksum(output_path, checksum)
    
    logger.info(f"Saved {len(df)} rows with {len(df.columns)} columns to {output_path}")
    logger.info(f"File checksum (SHA256): {checksum}")

def main():
    """
    Main entry point for the descriptor generation pipeline.
    """
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Generate Magpie descriptors for material data.")
    parser.add_argument('--input', type=str, required=True, help="Input directory containing raw data (Parquet/CSV)")
    parser.add_argument('--output', type=str, required=True, help="Output path for the master dataset (Parquet)")
    parser.add_argument('--chunk-size', type=int, default=5000, help="Number of rows to process per chunk")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger.info("Starting Magpie descriptor generation pipeline...")
    
    # Set seed
    set_seed(args.seed)
    
    # Paths
    input_dir = Path(args.input)
    output_path = Path(args.output)
    
    # Load data
    try:
        raw_df = load_raw_materials(input_dir)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)
    
    # Compute descriptors
    try:
        master_df = compute_magpie_descriptors(raw_df, chunk_size=args.chunk_size)
    except Exception as e:
        logger.error(f"Failed to compute descriptors: {e}")
        sys.exit(1)
    
    # Save results
    try:
        save_master_dataset(master_df, output_path)
    except Exception as e:
        logger.error(f"Failed to save master dataset: {e}")
        sys.exit(1)
    
    logger.info("Descriptor generation completed successfully.")

if __name__ == "__main__":
    main()
