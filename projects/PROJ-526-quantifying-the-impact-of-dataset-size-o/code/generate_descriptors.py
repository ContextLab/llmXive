import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from matminer.featurizers.composition.composite import ElementProperty
from matminer.featurizers.comcomposition import MagpieData
from matminer.featurizers.base import BaseFeaturizer

from config import get_config
from utils.logging_config import get_logger, log_descriptor_stats, log_error_summary
from utils.seed import set_seed

logger = get_logger(__name__)

def load_raw_materials(raw_dir: Path, property_name: str) -> pd.DataFrame:
    """
    Load raw material data for a specific property.
    
    Args:
        raw_dir: Directory containing raw data.
        property_name: Name of the property subdirectory.
    
    Returns:
        DataFrame with raw material data.
    """
    prop_dir = raw_dir / property_name
    if not prop_dir.exists():
        raise FileNotFoundError(f"Directory not found: {prop_dir}")
    
    # Find data files
    data_files = list(prop_dir.glob("*.csv")) + list(prop_dir.glob("*.parquet"))
    
    if not data_files:
        raise FileNotFoundError(f"No data files found in {prop_dir}")
    
    logger.info("Loading data from %d file(s) in %s", len(data_files), prop_dir)
    
    dfs = []
    for f in data_files:
        if f.suffix == '.csv':
            dfs.append(pd.read_csv(f))
        elif f.suffix == '.parquet':
            dfs.append(pd.read_parquet(f))
    
    if not dfs:
        raise ValueError("No data loaded from files in {}".format(prop_dir))
    
    df = pd.concat(dfs, ignore_index=True)
    logger.info("Loaded %d rows for property %s", len(df), property_name)
    return df

def validate_dataframe(df: pd.DataFrame, required_cols: List[str] = None) -> bool:
    """
    Validate that the DataFrame has required columns.
    
    Args:
        df: DataFrame to validate.
        required_cols: List of required column names.
    
    Returns:
        True if valid, False otherwise.
    """
    if required_cols:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            logger.error("Missing required columns: %s", missing)
            return False
    return True

def compute_magpie_descriptors(df: pd.DataFrame, composition_col: str = "composition") -> pd.DataFrame:
    """
    Compute Magpie composition-only descriptors.
    
    Args:
        df: DataFrame with material data.
        composition_col: Name of the column containing composition strings.
    
    Returns:
        DataFrame with added Magpie features.
    """
    logger.info("Computing Magpie descriptors for %d samples...", len(df))
    
    # Initialize Magpie featurizer
    # MagpieData generates 145 composition-based features
    featurizer = MagpieData()
    
    # Featurize in batches to manage memory
    batch_size = 1000
    all_features = []
    valid_indices = []
    failed_count = 0
    
    total = len(df)
    current = 0
    
    for i in range(0, total, batch_size):
        batch = df.iloc[i:i+batch_size]
        current += len(batch)
        log_download_progress(logger, current, total, "Descriptor Generation")
        
        try:
            # Featurize the batch
            features = featurizer.featurize_batch(batch[composition_col].tolist())
            features_df = pd.DataFrame(features, columns=featurizer.feature_labels())
            all_features.append(features_df)
            valid_indices.extend(range(i, min(i+batch_size, total)))
        except Exception as e:
            logger.warning("Failed to featurize batch starting at index %d: %s", i, str(e))
            failed_count += len(batch)
            continue
    
    if not all_features:
        raise RuntimeError("Failed to generate descriptors for any samples.")
    
    features_df = pd.concat(all_features, ignore_index=True)
    features_df.index = valid_indices
    
    # Merge features with original data
    result = df.join(features_df, how='right')
    
    # Log statistics
    log_descriptor_stats(
        logger,
        "ALL",
        total,
        len(result),
        failed_count
    )
    
    return result

def save_master_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the master dataset to Parquet format.
    
    Args:
        df: DataFrame to save.
        output_path: Path to save the file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Saving master dataset to %s (%d rows, %d columns)...", output_path, len(df), len(df.columns))
    df.to_parquet(output_path, index=False)
    
    # Log file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("Saved file size: %.2f MB", size_mb)

def main():
    """Main entry point for descriptor generation."""
    config = get_config()
    set_seed(42)
    
    raw_dir = config.data_dir / "raw"
    processed_dir = config.data_dir / "processed"
    
    # List of properties to process (should match downloaded datasets)
    # In a real scenario, this would be dynamic based on available data
    properties = [
        "formation_energy",
        "band_gap",
        "elastic_modulus"
    ]
    
    master_data = []
    
    for prop in properties:
        logger.info("Processing property: %s", prop)
        try:
            # Load raw data
            df = load_raw_materials(raw_dir, prop)
            
            # Add property label
            df['property_name'] = prop
            
            # Compute descriptors
            df_featurized = compute_magpie_descriptors(df)
            
            master_data.append(df_featurized)
            logger.info("Completed processing for %s", prop)
            
        except Exception as e:
            logger.error("Failed to process %s: %s", prop, str(e))
            continue
    
    if not master_data:
        logger.critical("No data processed. Aborting.")
        sys.exit(1)
    
    # Consolidate all data
    master_df = pd.concat(master_data, ignore_index=True)
    
    # Save master dataset
    output_path = processed_dir / "materials_master.parquet"
    save_master_dataset(master_df, output_path)
    
    logger.info("Descriptor generation pipeline complete.")

if __name__ == "__main__":
    main()
