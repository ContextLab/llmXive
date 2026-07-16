"""
Preprocessing module for Grain Boundary Diffusivity pipeline.

This module handles:
1. Loading parsed geometry data
2. Validating required features
3. Tagging metadata features
4. Enforcing minimum record constraints (n >= 500)
5. Saving cleaned datasets

Specific to T037:
- Explicitly logs counts of excluded records due to missing Σ value or boundary plane normal.
- Verifies these counts are non-zero if the dataset is incomplete (transparency).
"""

import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

# Import local utilities
from utils import setup_logging
from error_handling import DataInsufficiencyError, exit_on_insufficiency

# Configure logging
logger = setup_logging("preprocess")

# Required features for the model
REQUIRED_FEATURES = [
    "misorientation_angle",
    "rodrigues_x", "rodrigues_y", "rodrigues_z",
    "boundary_plane_h", "boundary_plane_k", "boundary_plane_l",
    "sigma_value",
    "temperature",
    "composition",
    "diffusivity",
    "boundary_width",
    "excess_volume",
    "simulation_method",
    "potential_id"
]

# Features specifically monitored for T037 transparency
MONITORED_MISSING_FEATURES = ["sigma_value", "boundary_plane_h", "boundary_plane_k", "boundary_plane_l"]

def load_parsed_data(input_path: str) -> pd.DataFrame:
    """
    Load parsed geometry data from parquet file.

    Args:
        input_path: Path to the parquet file (e.g., data/processed/parsed_geometry.parquet)

    Returns:
        DataFrame containing parsed geometry features
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Parsed geometry file not found: {input_path}")

    logger.info(f"Loading parsed data from {input_path}")
    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

def validate_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter records with missing required features.

    This function:
    1. Identifies missing values in required features.
    2. Drops rows with any missing required feature.
    3. Logs the count of excluded records, specifically highlighting
       missing Σ value and boundary plane normal components (T037 requirement).

    Args:
        df: Input DataFrame

    Returns:
        Tuple of (cleaned DataFrame, dict of missing counts per feature)
    """
    logger.info("Validating features and filtering missing values...")
    initial_count = len(df)
    missing_counts = {}

    # Check for missing values in required features
    for feature in REQUIRED_FEATURES:
        if feature not in df.columns:
            logger.warning(f"Required feature '{feature}' not found in dataset.")
            missing_counts[feature] = initial_count # All rows missing this
        else:
            count_missing = df[feature].isna().sum()
            if count_missing > 0:
                missing_counts[feature] = count_missing
                logger.warning(f"Feature '{feature}' has {count_missing} missing values.")

    # T037: Explicitly log counts for monitored features (Σ value and boundary plane normal)
    # Note: Boundary plane normal is represented by h, k, l. If any are missing, the record is invalid.
    monitored_missing_summary = {}

    # Check Sigma
    if "sigma_value" in df.columns:
        sigma_missing = df["sigma_value"].isna().sum()
        monitored_missing_summary["sigma_value"] = sigma_missing
        if sigma_missing > 0:
            logger.warning(f"DATA FILTERING TRANSPARENCY: {sigma_missing} records excluded due to missing 'sigma_value'.")
        else:
            logger.info("DATA FILTERING TRANSPARENCY: No records excluded due to missing 'sigma_value'.")

    # Check Boundary Plane Normal (h, k, l)
    plane_features = ["boundary_plane_h", "boundary_plane_k", "boundary_plane_l"]
    if all(f in df.columns for f in plane_features):
        # A record is invalid if ANY of h, k, l is missing
        plane_mask = df[plane_features].isna().any(axis=1)
        plane_missing_count = plane_mask.sum()
        monitored_missing_summary["boundary_plane_normal"] = plane_missing_count

        if plane_missing_count > 0:
            logger.warning(f"DATA FILTERING TRANSPARENCY: {plane_missing_count} records excluded due to missing 'boundary plane normal' (h, k, or l).")
        else:
            logger.info("DATA FILTERING TRANSPARENCY: No records excluded due to missing 'boundary plane normal'.")
    else:
        logger.error("Boundary plane normal columns (h, k, l) missing from dataset.")
        monitored_missing_summary["boundary_plane_normal"] = initial_count

    # Perform the actual filtering
    # Drop rows where ANY required feature is missing
    valid_df = df.dropna(subset=REQUIRED_FEATURES)
    final_count = len(valid_df)
    excluded_count = initial_count - final_count

    logger.info(f"Filtering complete. Excluded {excluded_count} records due to missing features.")
    logger.info(f"Remaining valid records: {final_count}")

    return valid_df, missing_counts

def tag_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tag simulation method and potential ID as features.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with metadata features tagged (ensuring they are in correct format)
    """
    logger.info("Tagging metadata features...")

    # Ensure simulation_method and potential_id exist and are strings
    if "simulation_method" in df.columns:
        df["simulation_method"] = df["simulation_method"].astype(str)
    else:
        logger.warning("Column 'simulation_method' not found. Adding placeholder.")
        df["simulation_method"] = "unknown"

    if "potential_id" in df.columns:
        df["potential_id"] = df["potential_id"].astype(str)
    else:
        logger.warning("Column 'potential_id' not found. Adding placeholder.")
        df["potential_id"] = "unknown"

    return df

def enforce_minimum_records(df: pd.DataFrame, min_records: int = 500) -> None:
    """
    Enforce the minimum record constraint (n >= 500).

    If the dataset has fewer than min_records after filtering,
    raises DataInsufficiencyError with detailed logging.

    Args:
        df: Cleaned DataFrame
        min_records: Minimum required records (default 500)

    Raises:
        DataInsufficiencyError: If record count is insufficient
    """
    count = len(df)
    if count < min_records:
        # Identify which features caused the most exclusions
        # This logic assumes we have the missing_counts from validate_features,
        # but since we are in a separate function, we re-calculate or pass context.
        # For robustness, we log the current state.
        missing_features = [col for col in REQUIRED_FEATURES if df[col].isna().any()]
        
        error_msg = (
            f"Data Insufficiency: Retrieved (initial) records not tracked here, "
            f"Valid {count}, Required {min_records}. "
            f"Missing features causing insufficiency: {missing_features if missing_features else 'Unknown (all valid but low count)'}"
        )
        
        logger.error(error_msg)
        raise DataInsufficiencyError(error_msg)
    
    logger.info(f"Data sufficiency check passed: {count} >= {min_records}")

def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save cleaned dataset to parquet file.

    Args:
        df: Cleaned DataFrame
        output_path: Output path for the parquet file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving cleaned dataset to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def main():
    """
    Main entry point for the preprocessing pipeline.
    Executes the full preprocessing workflow:
    1. Load parsed data
    2. Validate and filter features (with T037 logging)
    3. Tag metadata
    4. Enforce minimum records
    5. Save cleaned data
    """
    # Configuration paths
    input_path = "data/processed/parsed_geometry.parquet"
    output_path = "data/processed/cleaned_dataset.parquet"
    min_records = 500

    try:
        # 1. Load
        df = load_parsed_data(input_path)

        # 2. Validate & Filter (T037: Logs missing counts explicitly)
        df_clean, missing_counts = validate_features(df)

        # 3. Tag Metadata
        df_clean = tag_metadata_features(df_clean)

        # 4. Enforce Minimum
        enforce_minimum_records(df_clean, min_records)

        # 5. Save
        save_cleaned_data(df_clean, output_path)

        logger.info("Preprocessing pipeline completed successfully.")
        return 0

    except DataInsufficiencyError as e:
        logger.error(f"Pipeline halted due to data insufficiency: {e}")
        exit_on_insufficiency(str(e))
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())