"""
Preprocessing module for Grain Boundary Diffusivity pipeline.

Loads parsed geometry data, filters records with missing required features,
tags metadata fields, and enforces the n >= 500 constraint.
"""
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np

# Import existing project utilities
from utils import setup_logging, set_random_seed
from error_handling import DataInsufficiencyError, check_data_sufficiency, exit_on_insufficiency
from models.grain_boundary_record import GrainBoundaryRecord

# Configure logging
logger = setup_logging("preprocess")

# Define required features based on task specification
REQUIRED_FEATURES = [
    'misorientation_angle',
    'boundary_plane_normal',  # Stored as string or tuple representation
    'sigma_value',
    'temperature',
    'composition',
    'diffusivity',
    'boundary_width',
    'excess_volume'
]

# Optional features that should be tagged if present
OPTIONAL_FEATURES = [
    'simulation_method',
    'potential_id'
]

MIN_RECORDS = 500

def load_parsed_data(input_path: str) -> pd.DataFrame:
    """Load the parsed geometry data from parquet file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Parsed data file not found: {input_path}")
    
    logger.info(f"Loading parsed data from {input_path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} records")
    return df

def validate_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter records with missing required features and identify missing features.
    
    Returns:
        Tuple of (cleaned dataframe, list of missing feature names found in dataset)
    """
    missing_features = []
    
    # Check which required features are missing entirely from the dataset
    available_cols = set(df.columns)
    for feature in REQUIRED_FEATURES:
        if feature not in available_cols:
            missing_features.append(feature)
    
    if missing_features:
        logger.warning(f"Dataset is missing required columns: {missing_features}")
        # If entire columns are missing, we cannot proceed
        raise DataInsufficiencyError(
            f"Dataset missing required columns: {missing_features}. "
            f"Cannot filter records for missing values in non-existent columns."
        )
    
    # Create a mask for records with all required features present
    valid_mask = pd.Series([True] * len(df), index=df.index)
    
    for feature in REQUIRED_FEATURES:
        # Check for NaN, None, or empty string values
        if df[feature].dtype == object:
            # For object columns, check for None, empty strings, or NaN
            col_mask = df[feature].notna() & (df[feature] != '') & (df[feature] != 'None')
        else:
            # For numeric columns, just check NaN
            col_mask = df[feature].notna()
        
        valid_mask &= col_mask
        
        # Track if this feature has missing values
        if not col_mask.all():
            logger.debug(f"Feature '{feature}' has {(~col_mask).sum()} missing values")
    
    cleaned_df = df[valid_mask].reset_index(drop=True)
    
    # Identify which features caused records to be dropped
    dropped_count = len(df) - len(cleaned_df)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} records due to missing required features")
    
    return cleaned_df, []

def tag_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tag simulation_method and potential_id as features if present.
    
    These are added as metadata tags to the dataset.
    """
    for feature in OPTIONAL_FEATURES:
        if feature in df.columns:
            logger.info(f"Tagging optional feature: {feature}")
            # Ensure categorical encoding if needed
            if df[feature].dtype == object:
                df[feature] = df[feature].astype('category')
        else:
            logger.debug(f"Optional feature '{feature}' not present in dataset")
    
    return df

def enforce_minimum_records(df: pd.DataFrame, min_count: int = MIN_RECORDS) -> pd.DataFrame:
    """
    Enforce the minimum record count constraint.
    
    Args:
        df: Cleaned dataframe
        min_count: Minimum required records
        
    Returns:
        DataFrame if sufficient, otherwise raises DataInsufficiencyError
    """
    valid_count = len(df)
    
    if valid_count < min_count:
        # Determine which features contributed to the insufficiency
        missing_features = []
        for feature in REQUIRED_FEATURES:
            if feature in df.columns:
                if df[feature].isna().any() or (df[feature] == '').any() if df[feature].dtype == object else False:
                    missing_features.append(feature)
        
        error_msg = (
            f"Data Insufficiency: {valid_count} < {min_count}. "
            f"Missing features: {missing_features if missing_features else 'N/A (insufficient valid records)'}"
        )
        logger.error(error_msg)
        raise DataInsufficiencyError(error_msg)
    
    logger.info(f"Dataset meets minimum record requirement: {valid_count} >= {min_count}")
    return df

def save_cleaned_data(df: pd.DataFrame, output_path: str):
    """Save the cleaned dataset to parquet format."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving cleaned dataset to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    # Set random seed for reproducibility
    set_random_seed(42)
    
    # Define paths
    input_path = "data/processed/parsed_geometry.parquet"
    output_path = "data/processed/cleaned_dataset.parquet"
    
    try:
        # Load parsed data
        df = load_parsed_data(input_path)
        
        # Validate and filter features
        df_clean, missing_features = validate_features(df)
        
        # Tag metadata features
        df_clean = tag_metadata_features(df_clean)
        
        # Enforce minimum record count
        df_clean = enforce_minimum_records(df_clean)
        
        # Save cleaned dataset
        save_cleaned_data(df_clean, output_path)
        
        logger.info("Preprocessing completed successfully")
        return 0
        
    except DataInsufficiencyError as e:
        logger.error(f"Data insufficiency error: {e}")
        exit_on_insufficiency(str(e))
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
