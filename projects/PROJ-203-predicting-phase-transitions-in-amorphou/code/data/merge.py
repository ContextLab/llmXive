"""
Merge simulation descriptors with experimental labels.

This module provides functions to load simulation descriptors and experimental
labels, merge them, and save the result.

T013: Merge simulation descriptors with experimental labels from literature_subset.csv.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, get_data_config
from utils.logging_config import setup_pipeline_logging, get_missing_data_logger

def load_simulation_descriptors(config) -> pd.DataFrame:
    """
    Load simulation descriptors from the descriptor extraction output.

    Expected output from T011: data/processed/descriptors.csv or similar
    """
    data_config = get_data_config()
    
    # Try multiple possible locations for descriptor data
    possible_paths = [
        Path(config.data.processed_dir) / "descriptors.csv",
        Path(config.data.processed_dir) / "descriptor_data.csv",
        Path(config.data.raw_dir) / "descriptors.csv",
    ]
    
    descriptor_path = None
    for path in possible_paths:
        if path.exists():
            descriptor_path = path
            break
    
    if descriptor_path is None:
        # Try to find any CSV file in processed directory
        processed_dir = Path(config.data.processed_dir)
        csv_files = list(processed_dir.glob("*.csv"))
        if csv_files:
            descriptor_path = csv_files[0]
            logging.warning(f"Using first CSV found: {descriptor_path}")
        else:
            raise FileNotFoundError(f"No descriptor CSV found in {config.data.processed_dir}")
    
    logging.info(f"Loading simulation descriptors from {descriptor_path}")
    df = pd.read_csv(descriptor_path)
    
    # Ensure composition_id is present
    if 'composition_id' not in df.columns:
        # Try to infer from filename or other columns
        if 'composition' in df.columns:
            df['composition_id'] = df['composition']
        else:
            raise ValueError("Could not find composition_id column in descriptor data")
    
    return df

def load_experimental_labels(config) -> pd.DataFrame:
    """
    Load experimental labels from literature_subset.csv.
    
    Expected file: data/raw/literature_subset.csv
    """
    data_config = get_data_config()
    labels_path = Path(config.data.raw_dir) / "literature_subset.csv"
    
    if not labels_path.exists():
        raise FileNotFoundError(f"Experimental labels file not found: {labels_path}")
    
    logging.info(f"Loading experimental labels from {labels_path}")
    df = pd.read_csv(labels_path)
    
    # Ensure composition_id is present
    if 'composition_id' not in df.columns:
        if 'composition' in df.columns:
            df['composition_id'] = df['composition']
        else:
            raise ValueError("Could not find composition_id column in experimental labels")
    
    return df

def merge_datasets(descriptors_df: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge simulation descriptors with experimental labels on composition_id.
    
    Performs an inner join to ensure only compositions with both simulation
    and experimental data are included.
    """
    logging.info(f"Merging {len(descriptors_df)} descriptor rows with {len(labels_df)} label rows")
    
    merged_df = pd.merge(
        descriptors_df,
        labels_df,
        on='composition_id',
        how='inner'
    )
    
    logging.info(f"Merged dataset has {len(merged_df)} rows")
    
    # Log any compositions that were dropped
    dropped_comps = set(descriptors_df['composition_id']) - set(merged_df['composition_id'])
    if dropped_comps:
        logging.warning(f"Dropped {len(dropped_comps)} compositions without experimental labels: {list(dropped_comps)[:5]}...")
    
    return merged_df

def save_merged_dataset(df: pd.DataFrame, config) -> Path:
    """
    Save the merged dataset to a temporary CSV file.
    
    This is an intermediate step before T013.1 adds the crystallization labels.
    """
    output_path = Path(config.data.processed_dir) / "merged_dataset_with_labels.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logging.info(f"Saved merged dataset to {output_path}")
    
    return output_path

def main():
    """Main entry point for T013."""
    setup_pipeline_logging()
    config = get_config()
    
    logging.info("Starting T013: Merge simulation descriptors with experimental labels")
    
    try:
        # Load data
        descriptors_df = load_simulation_descriptors(config)
        labels_df = load_experimental_labels(config)
        
        # Merge
        merged_df = merge_datasets(descriptors_df, labels_df)
        
        # Save
        save_merged_dataset(merged_df, config)
        
        logging.info("T013 completed successfully")
        
    except Exception as e:
        logging.error(f"T013 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
