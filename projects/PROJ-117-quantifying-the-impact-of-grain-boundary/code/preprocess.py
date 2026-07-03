"""
Preprocessing module for grain boundary diffusivity dataset.

Loads parsed geometry data, filters records with missing required features,
tags simulation metadata, enforces minimum record count (n >= 500),
and outputs a cleaned dataset.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

import pandas as pd
import numpy as np

# Import shared utilities
from utils import setup_logging, raise_data_insufficiency, set_random_seed
from models.grain_boundary_record import GrainBoundaryRecord

# Constants
MIN_RECORDS = 500
REQUIRED_FEATURES = [
    'misorientation_angle',
    'boundary_plane_normal',
    'sigma_value',
    'temperature',
    'composition',
    'diffusivity',
    'boundary_width',
    'excess_volume'
]
METADATA_FEATURES = [
    'simulation_method',
    'potential_id'
]

def load_parsed_data(input_path: str) -> pd.DataFrame:
    """
    Load parsed geometry data from Parquet file.
    
    Args:
        input_path: Path to the parsed geometry Parquet file.
        
    Returns:
        DataFrame containing parsed geometry data.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Parsed data file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    logging.info(f"Loaded {len(df)} records from {input_path}")
    return df

def validate_required_features(df: pd.DataFrame) -> Set[str]:
    """
    Identify which required features are missing (NaN or None) in the dataset.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Set of feature names that have missing values.
    """
    missing_features = set()
    
    for feature in REQUIRED_FEATURES:
        if feature not in df.columns:
            missing_features.add(feature)
        else:
            # Check for NaN/None values
            if df[feature].isna().any():
                missing_features.add(feature)
    
    return missing_features

def filter_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out records with missing required features.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Filtered DataFrame with only complete records.
    """
    # Create a mask for records that have all required features
    mask = pd.Series([True] * len(df), index=df.index)
    
    for feature in REQUIRED_FEATURES:
        if feature in df.columns:
            mask = mask & df[feature].notna()
        else:
            # If feature column doesn't exist, all records are filtered out
            mask = pd.Series([False] * len(df), index=df.index)
    
    filtered_df = df[mask].copy()
    logging.info(f"Filtered from {len(df)} to {len(filtered_df)} complete records")
    return filtered_df

def tag_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure metadata features are present and properly tagged.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with metadata features tagged/normalized.
    """
    for feature in METADATA_FEATURES:
        if feature not in df.columns:
            # Create default column if missing
            df[feature] = 'unknown'
        else:
            # Normalize string values
            df[feature] = df[feature].fillna('unknown').astype(str)
    
    return df

def preprocess_data(input_path: str, output_path: str, random_seed: int = 42) -> None:
    """
    Main preprocessing pipeline: load, validate, filter, tag, and save.
    
    Args:
        input_path: Path to parsed geometry Parquet file.
        output_path: Path for cleaned dataset Parquet file.
        random_seed: Random seed for reproducibility.
    """
    set_random_seed(random_seed)
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting preprocessing pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Load data
    df = load_parsed_data(input_path)
    
    # Validate required features
    missing_features = validate_required_features(df)
    
    if missing_features:
        logger.warning(f"Missing required features in raw data: {missing_features}")
    
    # Filter records
    df_clean = filter_records(df)
    
    # Tag metadata features
    df_clean = tag_metadata_features(df_clean)
    
    # Enforce minimum record count
    valid_count = len(df_clean)
    if valid_count < MIN_RECORDS:
        missing_from_clean = validate_required_features(df_clean)
        error_msg = (
            f"Data Insufficiency: {valid_count} < {MIN_RECORDS}. "
            f"Missing features: {list(missing_from_clean) if missing_from_clean else 'None (count too low after filtering)'}"
        )
        raise_data_insufficiency(error_msg, valid_count, MIN_RECORDS)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save cleaned dataset
    df_clean.to_parquet(output_path, index=False)
    logger.info(f"Saved cleaned dataset to {output_path} ({valid_count} records)")
    
    # Log summary statistics
    logger.info("Preprocessing summary:")
    for col in REQUIRED_FEATURES:
        if col in df_clean.columns:
            logger.info(f"  {col}: {df_clean[col].notna().sum()} valid values")
    
    for col in METADATA_FEATURES:
        if col in df_clean.columns:
            logger.info(f"  {col}: unique values = {df_clean[col].nunique()}")

def main():
    """Entry point for preprocessing script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess grain boundary diffusivity data")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/parsed_geometry.parquet",
        help="Path to parsed geometry Parquet file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/cleaned_dataset.parquet",
        help="Path for cleaned dataset Parquet file"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    try:
        preprocess_data(args.input, args.output, args.seed)
        logging.info("Preprocessing completed successfully")
    except Exception as e:
        logging.error(f"Preprocessing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
