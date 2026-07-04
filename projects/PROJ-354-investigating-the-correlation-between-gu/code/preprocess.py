"""
Preprocessing pipeline for Gut Microbiome-Cognitive Correlation Study.

This module implements cohort filtering logic:
- Excludes recent antibiotic users
- Excludes participants missing either microbiome or cognitive data
- Logs exclusion counts and reasons to a JSON file

Prerequisites:
- T004: code/config.py (UK Biobank field IDs, paths)
- T012: code/download.py (raw data files downloaded)
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Import project utilities and config
from code.config import (
    get_project_root,
    PATHS,
    UKB_FIELD_IDS,
    RANDOM_SEED,
    ANTIBIOTIC_EXCLUSION_WINDOW_DAYS,
)
from code.utils.logging import get_logger, PreprocessingError
from code.utils.streaming import load_in_batches, concatenate_batches

# Configure logger
logger = get_logger(__name__)

# Constants for filtering
MIN_PARTICIPANTS_TO_KEEP = 10  # Safety threshold


def load_raw_microbiome_data() -> pd.DataFrame:
    """
    Load raw microbiome count data from downloaded files.
    
    Returns:
        DataFrame with participant IDs and genus-level counts.
        
    Raises:
        PreprocessingError: If data file is missing or invalid.
    """
    microbiome_path = PATHS["raw_microbiome"]
    
    if not os.path.exists(microbiome_path):
        raise PreprocessingError(
            f"Raw microbiome data not found at {microbiome_path}. "
            "Run T012 (download.py) first."
        )
    
    logger.info(f"Loading microbiome data from {microbiome_path}")
    
    # Use streaming loader for large files
    try:
        df = load_in_batches(microbiome_path, batch_size=100000)
        logger.info(f"Loaded {len(df):,} rows of microbiome data")
    except Exception as e:
        raise PreprocessingError(f"Failed to load microbiome data: {str(e)}")
    
    return df


def load_raw_cognitive_data() -> pd.DataFrame:
    """
    Load raw cognitive assessment data from downloaded files.
    
    Returns:
        DataFrame with participant IDs and cognitive scores.
        
    Raises:
        PreprocessingError: If data file is missing or invalid.
    """
    cognitive_path = PATHS["raw_cognitive"]
    
    if not os.path.exists(cognitive_path):
        raise PreprocessingError(
            f"Raw cognitive data not found at {cognitive_path}. "
            "Run T012 (download.py) first."
        )
    
    logger.info(f"Loading cognitive data from {cognitive_path}")
    
    try:
        df = load_in_batches(cognitive_path, batch_size=100000)
        logger.info(f"Loaded {len(df):,} rows of cognitive data")
    except Exception as e:
        raise PreprocessingError(f"Failed to load cognitive data: {str(e)}")
    
    return df


def load_raw_medication_data() -> pd.DataFrame:
    """
    Load raw medication/antibiotic usage data.
    
    Returns:
        DataFrame with participant IDs and medication records.
        
    Raises:
        PreprocessingError: If data file is missing or invalid.
    """
    medication_path = PATHS["raw_medication"]
    
    if not os.path.exists(medication_path):
        raise PreprocessingError(
            f"Raw medication data not found at {medication_path}. "
            "Run T012 (download.py) first."
        )
    
    logger.info(f"Loading medication data from {medication_path}")
    
    try:
        df = load_in_batches(medication_path, batch_size=100000)
        logger.info(f"Loaded {len(df):,} rows of medication data")
    except Exception as e:
        raise PreprocessingError(f"Failed to load medication data: {str(e)}")
    
    return df


def filter_antibiotic_users(
    microbiome_df: pd.DataFrame,
    medication_df: pd.DataFrame,
    window_days: int = ANTIBIOTIC_EXCLUSION_WINDOW_DAYS
) -> Tuple[pd.DataFrame, int]:
    """
    Exclude participants who took antibiotics within the exclusion window.
    
    Args:
        microbiome_df: DataFrame with microbiome samples and collection dates.
        medication_df: DataFrame with medication records and dates.
        window_days: Number of days before sample collection to check for antibiotics.
        
    Returns:
        Tuple of (filtered microbiome DataFrame, count of excluded participants)
    """
    logger.info(f"Filtering antibiotic users (window: {window_days} days)")
    
    # Get the primary antibiotic field ID from config
    antibiotic_field = UKB_FIELD_IDS["medication_antibiotics"]
    if not antibiotic_field:
        logger.warning("No antibiotic field ID found in config. Skipping antibiotic filter.")
        return microbiome_df, 0
    
    # Merge medication data with microbiome data on participant ID
    merged = microbiome_df.merge(
        medication_df[[UKB_FIELD_IDS["participant_id"], antibiotic_field, "assessment_date"]],
        on=UKB_FIELD_IDS["participant_id"],
        how="left"
    )
    
    # Convert dates to datetime
    merged["sample_date"] = pd.to_datetime(merged["assessment_date_x"], errors="coerce")
    merged["med_date"] = pd.to_datetime(merged["assessment_date_y"], errors="coerce")
    
    # Identify antibiotic users within window
    # Antibiotic codes typically start with 'J01' (ATC code for antibiotics)
    antibiotic_codes = merged[antibiotic_field].dropna().unique()
    if len(antibiotic_codes) == 0:
        logger.info("No antibiotic codes found in data. Skipping antibiotic filter.")
        return microbiome_df, 0
    
    # Filter for recent antibiotic use
    recent_use_mask = (
        merged["med_date"].notna() &
        merged["sample_date"].notna() &
        (merged["sample_date"] - merged["med_date"]).dt.days <= window_days
    )
    
    participants_with_recent_antibiotics = merged.loc[recent_use_mask, UKB_FIELD_IDS["participant_id"]].unique()
    excluded_count = len(participants_with_recent_antibiotics)
    
    if excluded_count > 0:
        logger.info(f"Excluding {excluded_count:,} participants with recent antibiotic use")
        filtered_df = microbiome_df[
            ~microbiome_df[UKB_FIELD_IDS["participant_id"]].isin(participants_with_recent_antibiotics)
        ].copy()
    else:
        logger.info("No participants excluded for recent antibiotic use")
        filtered_df = microbiome_df.copy()
    
    return filtered_df, excluded_count


def filter_missing_data(
    microbiome_df: pd.DataFrame,
    cognitive_df: pd.DataFrame
) -> Tuple[pd.DataFrame, int, int]:
    """
    Exclude participants missing either microbiome or cognitive data.
    
    Args:
        microbiome_df: Filtered microbiome DataFrame.
        cognitive_df: Raw cognitive DataFrame.
        
    Returns:
        Tuple of (final filtered microbiome DataFrame, count missing microbiome, count missing cognitive)
    """
    logger.info("Filtering participants with missing data")
    
    participant_id_col = UKB_FIELD_IDS["participant_id"]
    
    # Get participants with valid microbiome data
    valid_microbiome = microbiome_df[participant_id_col].unique()
    
    # Get participants with valid cognitive data
    # Check for non-null cognitive scores
    valid_cognitive = cognitive_df[
        cognitive_df[UKB_FIELD_IDS["cognitive_score"]].notna()
    ][participant_id_col].unique()
    
    # Find intersection
    valid_microbiome_set = set(valid_microbiome)
    valid_cognitive_set = set(valid_cognitive)
    
    missing_microbiome = valid_cognitive_set - valid_microbiome_set
    missing_cognitive = valid_microbiome_set - valid_cognitive_set
    
    missing_microbiome_count = len(missing_microbiome)
    missing_cognitive_count = len(missing_cognitive)
    
    logger.info(f"Missing microbiome data: {missing_microbiome_count:,} participants")
    logger.info(f"Missing cognitive data: {missing_cognitive_count:,} participants")
    
    # Keep only participants with both data types
    final_participants = valid_microbiome_set.intersection(valid_cognitive_set)
    
    if len(final_participants) < MIN_PARTICIPANTS_TO_KEEP:
        raise PreprocessingError(
            f"Remaining cohort size ({len(final_participants)}) below minimum threshold "
            f"({MIN_PARTICIPANTS_TO_KEEP}). Data may be too sparse."
        )
    
    filtered_df = microbiome_df[microbiome_df[participant_id_col].isin(final_participants)].copy()
    
    return filtered_df, missing_microbiome_count, missing_cognitive_count


def generate_retention_log(
    initial_count: int,
    antibiotic_excluded: int,
    missing_microbiome: int,
    missing_cognitive: int,
    final_count: int,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate retention log JSON file.
    
    Args:
        initial_count: Starting participant count.
        antibiotic_excluded: Count excluded for antibiotic use.
        missing_microbiome: Count missing microbiome data.
        missing_cognitive: Count missing cognitive data.
        final_count: Final participant count.
        output_path: Path to write the JSON log.
        
    Returns:
        Dictionary containing the retention statistics.
    """
    retention_log = {
        "initial_participants": initial_count,
        "exclusions": {
            "recent_antibiotic_users": antibiotic_excluded,
            "missing_microbiome_data": missing_microbiome,
            "missing_cognitive_data": missing_cognitive,
        },
        "final_participants": final_count,
        "retention_rate": round(final_count / initial_count, 4) if initial_count > 0 else 0,
        "timestamp": pd.Timestamp.now().isoformat(),
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(retention_log, f, indent=2)
    
    logger.info(f"Retention log written to {output_path}")
    return retention_log


def run_preprocessing_pipeline() -> Dict[str, Any]:
    """
    Execute the full preprocessing pipeline:
    1. Load raw data
    2. Filter antibiotic users
    3. Filter missing data
    4. Generate retention log
    5. Save intermediate outputs
    
    Returns:
        Dictionary with pipeline statistics and output paths.
    """
    logger.info("=" * 60)
    logger.info("Starting Preprocessing Pipeline (T013)")
    logger.info("=" * 60)
    
    try:
        # Step 1: Load raw data
        logger.info("Step 1: Loading raw data...")
        microbiome_df = load_raw_microbiome_data()
        cognitive_df = load_raw_cognitive_data()
        medication_df = load_raw_medication_data()
        
        initial_count = len(microbiome_df[UKB_FIELD_IDS["participant_id"]].unique())
        logger.info(f"Initial participants: {initial_count:,}")
        
        # Step 2: Filter antibiotic users
        logger.info("Step 2: Filtering antibiotic users...")
        microbiome_df, antibiotic_excluded = filter_antibiotic_users(
            microbiome_df, medication_df
        )
        
        # Step 3: Filter missing data
        logger.info("Step 3: Filtering missing data...")
        microbiome_df, missing_microbiome, missing_cognitive = filter_missing_data(
            microbiome_df, cognitive_df
        )
        
        final_count = len(microbiome_df[UKB_FIELD_IDS["participant_id"]].unique())
        logger.info(f"Final participants: {final_count:,}")
        
        # Step 4: Generate retention log
        logger.info("Step 4: Generating retention log...")
        retention_log_path = PATHS["retention_log"]
        retention_stats = generate_retention_log(
            initial_count,
            antibiotic_excluded,
            missing_microbiome,
            missing_cognitive,
            final_count,
            retention_log_path
        )
        
        # Step 5: Save filtered microbiome data (intermediate output)
        logger.info("Step 5: Saving filtered microbiome data...")
        filtered_microbiome_path = PATHS["filtered_microbiome"]
        filtered_microbiome_path.parent.mkdir(parents=True, exist_ok=True)
        microbiome_df.to_parquet(filtered_microbiome_path, index=False)
        logger.info(f"Filtered microbiome data saved to {filtered_microbiome_path}")
        
        # Step 6: Save filtered cognitive data (intermediate output)
        logger.info("Step 6: Saving filtered cognitive data...")
        filtered_cognitive_path = PATHS["filtered_cognitive"]
        filtered_cognitive_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Merge cognitive data for the final cohort
        final_cognitive_df = cognitive_df[
            cognitive_df[UKB_FIELD_IDS["participant_id"]].isin(
                microbiome_df[UKB_FIELD_IDS["participant_id"]].unique()
            )
        ].copy()
        final_cognitive_df.to_parquet(filtered_cognitive_path, index=False)
        logger.info(f"Filtered cognitive data saved to {filtered_cognitive_path}")
        
        logger.info("=" * 60)
        logger.info("Preprocessing Pipeline Completed Successfully")
        logger.info("=" * 60)
        
        return {
            "status": "success",
            "initial_count": initial_count,
            "final_count": final_count,
            "exclusions": {
                "antibiotic_users": antibiotic_excluded,
                "missing_microbiome": missing_microbiome,
                "missing_cognitive": missing_cognitive,
            },
            "retention_rate": retention_stats["retention_rate"],
            "output_files": {
                "retention_log": str(retention_log_path),
                "filtered_microbiome": str(filtered_microbiome_path),
                "filtered_cognitive": str(filtered_cognitive_path),
            }
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise PreprocessingError(f"Preprocessing pipeline failed: {str(e)}")


def main():
    """Entry point for the preprocessing script."""
    logger.info("Running preprocessing script as main module...")
    result = run_preprocessing_pipeline()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
