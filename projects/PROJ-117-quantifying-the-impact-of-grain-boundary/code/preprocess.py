"""
Preprocessing module for Grain Boundary Diffusivity pipeline.

This module handles:
- Loading parsed geometry data from T010
- Validating required features
- Tagging metadata features (simulation_method, potential_id)
- Enforcing minimum record count (n >= 500)
- Saving cleaned dataset to parquet
"""

import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np

# Import error handling utilities
from error_handling import DataInsufficiencyError, exit_on_insufficiency
# Import utility functions
from utils import setup_logging, set_random_seed
# Import geometry parser functions if needed for validation
from geometry_parser import calculate_sigma_from_misorientation

# Configure logging
logger = logging.getLogger(__name__)

# Define required features for the model
REQUIRED_FEATURES = [
    'misorientation_angle',
    'boundary_plane_normal',  # Tuple or string representation
    'sigma_value',
    'temperature',
    'composition',
    'diffusivity',
    'boundary_width',
    'excess_volume',
    'simulation_method',
    'potential_id'
]

# Metadata features that need tagging
METADATA_FEATURES = ['simulation_method', 'potential_id']

def load_parsed_data(input_path: str) -> pd.DataFrame:
    """
    Load parsed geometry data from Parquet file.

    Args:
        input_path: Path to the parsed geometry parquet file

    Returns:
        DataFrame containing parsed geometry data
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Parsed data file not found: {input_path}")

    logger.info(f"Loading parsed data from {input_path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def validate_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter records with missing required features.

    Args:
        df: DataFrame with parsed geometry data

    Returns:
        Tuple of (cleaned DataFrame, list of missing features found)
    """
    logger.info(f"Validating features for {len(df)} records")
    
    # Track which features are missing
    missing_features = []
    
    # Check for required features in the dataframe
    available_cols = set(df.columns)
    missing_cols = set(REQUIRED_FEATURES) - available_cols
    
    if missing_cols:
        logger.warning(f"Missing required columns in dataset: {missing_cols}")
        missing_features.extend(missing_cols)
    
    # Create a copy to avoid modifying original
    cleaned_df = df.copy()
    
    # Filter out rows with missing values in required features
    # Only consider the features that are actually present in the dataframe
    present_required = [f for f in REQUIRED_FEATURES if f in cleaned_df.columns]
    
    if not present_required:
        logger.error("No required features found in dataset")
        return cleaned_df, list(missing_cols)
    
    # Drop rows with any missing values in required features
    initial_count = len(cleaned_df)
    cleaned_df = cleaned_df.dropna(subset=present_required)
    dropped_count = initial_count - len(cleaned_df)
    
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} records due to missing values in required features")
    
    # Check for specific feature validity
    # For sigma_value, ensure it's a valid positive number
    if 'sigma_value' in cleaned_df.columns:
        invalid_sigma = cleaned_df[cleaned_df['sigma_value'] <= 0]
        if len(invalid_sigma) > 0:
            logger.warning(f"Found {len(invalid_sigma)} records with invalid sigma_value (<=0)")
            cleaned_df = cleaned_df[cleaned_df['sigma_value'] > 0]
    
    # For misorientation_angle, ensure it's within valid range (0-90 degrees typically)
    if 'misorientation_angle' in cleaned_df.columns:
        invalid_angle = cleaned_df[(cleaned_df['misorientation_angle'] < 0) | 
                                  (cleaned_df['misorientation_angle'] > 90)]
        if len(invalid_angle) > 0:
            logger.warning(f"Found {len(invalid_angle)} records with invalid misorientation_angle")
            cleaned_df = cleaned_df[(cleaned_df['misorientation_angle'] >= 0) & 
                                   (cleaned_df['misorientation_angle'] <= 90)]
    
    # Check for boundary_plane_normal validity (should be a 3-tuple or similar)
    if 'boundary_plane_normal' in cleaned_df.columns:
        # Filter out empty or invalid entries
        invalid_plane = cleaned_df[cleaned_df['boundary_plane_normal'].isna() | 
                                 (cleaned_df['boundary_plane_normal'] == '')]
        if len(invalid_plane) > 0:
            logger.warning(f"Found {len(invalid_plane)} records with invalid boundary_plane_normal")
            cleaned_df = cleaned_df[cleaned_df['boundary_plane_normal'].notna() & 
                                  (cleaned_df['boundary_plane_normal'] != '')]
    
    logger.info(f"Feature validation complete: {len(cleaned_df)} valid records remaining")
    return cleaned_df, missing_features

def tag_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tag metadata features (simulation_method, potential_id) for model training.

    Args:
        df: DataFrame with validated features

    Returns:
        DataFrame with tagged metadata features
    """
    logger.info("Tagging metadata features")
    
    cleaned_df = df.copy()
    
    # Ensure metadata features exist
    for feature in METADATA_FEATURES:
        if feature not in cleaned_df.columns:
            logger.warning(f"Metadata feature '{feature}' not found in dataset, creating placeholder")
            cleaned_df[feature] = 'unknown'
        else:
            # Convert to string if not already
            cleaned_df[feature] = cleaned_df[feature].astype(str)
            # Replace any remaining NaN with 'unknown'
            cleaned_df[feature] = cleaned_df[feature].fillna('unknown')
    
    logger.info(f"Tagged metadata features: {METADATA_FEATURES}")
    return cleaned_df

def enforce_minimum_records(df: pd.DataFrame, min_records: int = 500) -> None:
    """
    Enforce minimum record count constraint.

    Args:
        df: DataFrame to check
        min_records: Minimum required records (default 500)

    Raises:
        DataInsufficiencyError: If record count is below minimum
    """
    valid_count = len(df)
    
    if valid_count < min_records:
        # Determine which features might be causing insufficiency
        missing_feature_list = []
        for feature in REQUIRED_FEATURES:
            if feature not in df.columns or df[feature].isna().all():
                missing_feature_list.append(feature)
        
        error_msg = (f"Data Insufficiency: {valid_count} < {min_records}. "
                    f"Missing features: {missing_feature_list if missing_feature_list else 'None detected'}")
        
        logger.error(error_msg)
        raise DataInsufficiencyError(error_msg)
    
    logger.info(f"Data sufficiency check passed: {valid_count} >= {min_records} records")

def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save cleaned dataset to Parquet file.

    Args:
        df: Cleaned DataFrame to save
        output_path: Path for output file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving cleaned dataset to {output_path}")
    df.to_parquet(path, index=False)
    
    # Verify file was created
    if path.exists():
        file_size = path.stat().st_size
        logger.info(f"Saved {len(df)} records to {output_path} ({file_size} bytes)")
    else:
        raise IOError(f"Failed to save cleaned dataset to {output_path}")

def main():
    """
    Main preprocessing pipeline execution.
    """
    # Set up logging
    setup_logging()
    set_random_seed(42)
    
    logger.info("Starting preprocessing pipeline")
    
    # Define paths
    input_path = "data/processed/parsed_geometry.parquet"
    output_path = "data/processed/cleaned_dataset.parquet"
    
    try:
        # Load parsed data
        df = load_parsed_data(input_path)
        
        # Validate features and filter
        df_cleaned, missing_features = validate_features(df)
        
        # Tag metadata features
        df_tagged = tag_metadata_features(df_cleaned)
        
        # Enforce minimum record count
        enforce_minimum_records(df_tagged, min_records=500)
        
        # Save cleaned dataset
        save_cleaned_data(df_tagged, output_path)
        
        logger.info("Preprocessing pipeline completed successfully")
        
    except DataInsufficiencyError as e:
        logger.error(f"Data insufficiency detected: {e}")
        exit_on_insufficiency(str(e))
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()