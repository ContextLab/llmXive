"""
Generate Magpie composition-only descriptors for material entries.

This script reads the raw material data downloaded by T011, computes
Magpie features (composition-only, no structural data), and outputs
a consolidated Parquet file to data/processed/materials_master.parquet.

Dependencies:
  - matminer (for Magpie featurizer)
  - pandas
  - numpy
  - pymatgen
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

import pandas as pd
import numpy as np
from matminer.featurizers.composition import MagpieData
from pymatgen.core import Composition

# Project imports
from config import get_config, require_data_dir, require_state_dir
from utils.seed import set_seed
from utils.integrity import compute_sha256, log_checksum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_materials(data_dir: Path) -> pd.DataFrame:
    """
    Load raw material data from the downloaded JSON/CSV files.
    Expects data to be in data/raw/ in a consolidated format or individual files.
    """
    raw_dir = data_dir / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    # Look for consolidated parquet or json files first
    parquet_files = list(raw_dir.glob("*.parquet"))
    json_files = list(raw_dir.glob("*.json"))
    csv_files = list(raw_dir.glob("*.csv"))

    all_data = []

    # Try to load parquet files (preferred format from T011)
    if parquet_files:
        for pf in parquet_files:
            logger.info(f"Loading parquet: {pf}")
            df = pd.read_parquet(pf)
            all_data.append(df)
    elif json_files:
        for jf in json_files:
            logger.info(f"Loading JSON: {jf}")
            with open(jf, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
                all_data.append(df)
    elif csv_files:
        for cf in csv_files:
            logger.info(f"Loading CSV: {cf}")
            df = pd.read_csv(cf)
            all_data.append(df)
    else:
        raise FileNotFoundError(
            f"No supported data files found in {raw_dir}. "
            "Expected .parquet, .json, or .csv files."
        )

    if not all_data:
        raise ValueError("No data loaded from raw directory.")

    # Concatenate all dataframes
    master_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"Loaded {len(master_df)} total material entries.")
    return master_df

def validate_dataframe(df: pd.DataFrame) -> None:
    """Validate that the dataframe has required columns for descriptor generation."""
    required_cols = ['composition', 'property_name', 'property_value']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check composition format
    if df['composition'].isna().any():
        logger.warning("Found NaN compositions. Will attempt to drop them.")
        df = df.dropna(subset=['composition'])
    
    logger.info(f"Validation passed. {len(df)} entries after cleaning.")
    return df

def compute_magpie_descriptors(
    df: pd.DataFrame, 
    sample_size: Optional[int] = None,
    chunk_size: int = 5000
) -> pd.DataFrame:
    """
    Compute Magpie composition-only descriptors.
    
    Args:
        df: DataFrame with 'composition' column containing string formulas
        sample_size: If provided, only process this many rows (for testing)
        chunk_size: Process in chunks to manage memory
    
    Returns:
        DataFrame with added Magpie feature columns
    """
    set_seed(42)  # Deterministic processing
    
    # Initialize Magpie featurizer
    # MagpieData provides composition-only features (no structure)
    featurizer = MagpieData()
    
    # Get feature names
    feature_names = featurizer.feature_labels()
    logger.info(f"Magpie will generate {len(feature_names)} features.")
    
    # Prepare output dataframe
    result_dfs = []
    
    # Process in chunks to manage memory
    total_rows = len(df)
    start_idx = 0
    
    if sample_size:
        total_rows = min(sample_size, total_rows)
        df = df.head(total_rows)
    
    logger.info(f"Processing {total_rows} entries in chunks of {chunk_size}...")
    
    while start_idx < total_rows:
        end_idx = min(start_idx + chunk_size, total_rows)
        chunk = df.iloc[start_idx:end_idx].copy()
        
        logger.info(f"Processing chunk {start_idx}-{end_idx}...")
        
        # Convert composition strings to Composition objects
        # Handle potential errors in composition parsing
        compositions = []
        valid_indices = []
        
        for idx, formula in enumerate(chunk['composition']):
            try:
                comp = Composition(formula)
                compositions.append(comp)
                valid_indices.append(idx)
            except Exception as e:
                logger.warning(f"Skipping invalid composition at index {idx}: {formula} ({e})")
        
        if not compositions:
            logger.warning(f"No valid compositions in chunk {start_idx}-{end_idx}")
            start_idx = end_idx
            continue
        
        # Featurize the valid compositions
        try:
            features = featurizer.featurize_many(compositions)
            features_df = pd.DataFrame(features, columns=feature_names)
            
            # Attach to original chunk data
            chunk_valid = chunk.iloc[valid_indices].copy()
            chunk_valid = chunk_valid.reset_index(drop=True)
            chunk_featurized = pd.concat([chunk_valid, features_df], axis=1)
            
            result_dfs.append(chunk_featurized)
            
        except Exception as e:
            logger.error(f"Error featurizing chunk {start_idx}-{end_idx}: {e}")
            raise
        
        start_idx = end_idx
    
    if not result_dfs:
        raise ValueError("No data was successfully featurized.")
    
    final_df = pd.concat(result_dfs, ignore_index=True)
    logger.info(f"Successfully generated descriptors for {len(final_df)} entries.")
    
    # Log descriptor statistics
    numeric_cols = final_df.select_dtypes(include=[np.number]).columns
    logger.info(f"Descriptor statistics (first 5 features):")
    for col in numeric_cols[:5]:
        logger.info(f"  {col}: mean={final_df[col].mean():.4f}, "
                   f"std={final_df[col].std():.4f}, "
                   f"min={final_df[col].min():.4f}, "
                   f"max={final_df[col].max():.4f}")
    
    return final_df

def save_master_dataset(
    df: pd.DataFrame, 
    output_path: Path,
    state_dir: Path
) -> None:
    """Save the master dataset and log checksums."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as parquet
    logger.info(f"Saving master dataset to {output_path}")
    df.to_parquet(output_path, index=False)
    
    # Compute and log checksum
    checksum = compute_sha256(output_path)
    log_checksum(state_dir / "checksums.json", "materials_master.parquet", checksum)
    
    # Also save a CSV fallback if memory permits (smaller than parquet for compatibility)
    csv_path = output_path.with_suffix('.csv')
    logger.info(f"Saving CSV fallback to {csv_path}")
    df.to_csv(csv_path, index=False)
    
    logger.info(f"Saved {len(df)} entries with {len(df.columns)} columns.")
    logger.info(f"Output files: {output_path}, {csv_path}")

def main():
    """Main entry point for descriptor generation."""
    logger.info("Starting Magpie descriptor generation...")
    
    # Load configuration
    config = get_config()
    data_dir = require_data_dir()
    state_dir = require_state_dir()
    
    # Load raw data
    logger.info("Loading raw materials data...")
    try:
        raw_df = load_raw_materials(data_dir)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)
    
    # Validate dataframe
    try:
        raw_df = validate_dataframe(raw_df)
    except ValueError as e:
        logger.error(f"Data validation failed: {e}")
        sys.exit(1)
    
    # Generate descriptors
    logger.info("Computing Magpie descriptors...")
    try:
        featurized_df = compute_magpie_descriptors(raw_df)
    except Exception as e:
        logger.error(f"Descriptor generation failed: {e}")
        sys.exit(1)
    
    # Save results
    output_path = data_dir / "processed" / "materials_master.parquet"
    try:
        save_master_dataset(featurized_df, output_path, state_dir)
    except Exception as e:
        logger.error(f"Failed to save master dataset: {e}")
        sys.exit(1)
    
    logger.info("Descriptor generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
