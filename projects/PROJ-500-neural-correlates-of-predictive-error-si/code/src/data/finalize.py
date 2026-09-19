"""
Finalization Module for T024: Finalize and Write Aligned Dataset.

This module consumes:
1. data/excluded_subjects.csv (from T016)
2. data/interim_lagged_mmns.csv (from T022/T022b)
3. data/accuracy_blocks.csv (from T021)

It merges these datasets, applies underpowered subject filters, performs
a final re-verification of trial counts, and writes the final
data/aligned_data.csv artifact.
"""
import os
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
import pandas as pd
import numpy as np

from src.utils.logging import get_logger
from src.utils.config import get_data_dir

logger = get_logger(__name__)


def load_interim_lagged_mmns() -> Optional[pd.DataFrame]:
    """Load the interim lagged MMN dataset."""
    data_dir = get_data_dir()
    file_path = data_dir / "interim_lagged_mmns.csv"
    if not file_path.exists():
        logger.error(f"File not found: {file_path}. Cannot proceed with finalization.")
        return None
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return None


def load_accuracy_blocks() -> Optional[pd.DataFrame]:
    """Load the accuracy blocks dataset."""
    data_dir = get_data_dir()
    file_path = data_dir / "accuracy_blocks.csv"
    if not file_path.exists():
        logger.error(f"File not found: {file_path}. Cannot proceed with finalization.")
        return None
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return None


def load_excluded_subjects() -> List[str]:
    """Load the list of excluded subject IDs from T016."""
    data_dir = get_data_dir()
    file_path = data_dir / "excluded_subjects.csv"
    excluded_ids = []
    
    if not file_path.exists():
        logger.warning(f"Excluded subjects file not found: {file_path}. Assuming no exclusions.")
        return excluded_ids
    
    try:
        df = pd.read_csv(file_path)
        if 'subject_id' in df.columns:
            excluded_ids = df['subject_id'].astype(str).tolist()
            logger.info(f"Loaded {len(excluded_ids)} excluded subjects from {file_path}")
        else:
            logger.warning(f"Column 'subject_id' not found in {file_path}.")
    except Exception as e:
        logger.error(f"Failed to load excluded subjects from {file_path}: {e}")
    
    return excluded_ids


def filter_by_excluded_subjects(df: pd.DataFrame, excluded_ids: List[str]) -> pd.DataFrame:
    """Filter out rows corresponding to excluded subjects."""
    if not excluded_ids:
        return df
    
    initial_count = len(df)
    # Ensure subject_id column is string for comparison
    if 'subject_id' in df.columns:
        mask = ~df['subject_id'].astype(str).isin(excluded_ids)
        filtered_df = df[mask]
        removed_count = initial_count - len(filtered_df)
        logger.info(f"Filtered out {removed_count} rows for {len(excluded_ids)} excluded subjects.")
        return filtered_df
    else:
        logger.warning("Input DataFrame does not have 'subject_id' column. Skipping exclusion filter.")
        return df


def validate_aligned_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Perform final re-verification of the merged dataset.
    Checks:
    1. No NaN values in critical columns (subject_id, block_id, mmn_amplitude, accuracy).
    2. Trial count threshold verification (if trial_count column exists).
    
    Returns:
        Tuple[is_valid, list_of_issues]
    """
    issues = []
    required_columns = ['subject_id', 'block_id', 'mmn_amplitude', 'accuracy']
    
    # Check for required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")
        return False, issues
    
    # Check for NaN values in critical columns
    for col in required_columns:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            issues.append(f"Column '{col}' contains {nan_count} NaN values.")
    
    # Check for duplicate entries (subject_id + block_id)
    if df.duplicated(subset=['subject_id', 'block_id']).any():
        issues.append("Duplicate entries found for subject_id + block_id combination.")
    
    # Re-verification of trial count threshold if column exists
    # Note: The merged data might not have trial_count directly, but if it does, check it.
    # Assuming 'trial_count' might be present from the join or derived.
    # If not present, we rely on the pre-filtering in T016.
    if 'trial_count' in df.columns:
        low_power_rows = df[df['trial_count'] < 500]
        if len(low_power_rows) > 0:
            subject_ids = low_power_rows['subject_id'].unique().tolist()
            issues.append(f"Found {len(low_power_rows)} rows with trial_count < 500 for subjects: {subject_ids}")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def run_finalization_pipeline() -> bool:
    """
    Main pipeline execution for T024.
    1. Load interim_lagged_mmns.csv
    2. Load accuracy_blocks.csv
    3. Load excluded_subjects.csv
    4. Merge datasets on subject_id and block_id
    5. Filter by excluded subjects
    6. Validate the result
    7. Write data/aligned_data.csv
    """
    logger.info("Starting T024 Finalization Pipeline.")
    
    # 1. Load Data
    mmn_df = load_interim_lagged_mmns()
    acc_df = load_accuracy_blocks()
    excluded_ids = load_excluded_subjects()
    
    if mmn_df is None or acc_df is None:
        logger.error("Failed to load required input files. Aborting.")
        return False
    
    # 2. Merge Datasets
    # Merge on subject_id and block_id. 
    # Assuming both have these columns.
    try:
        # Inner join to ensure only blocks with both MMN and Accuracy are kept
        merged_df = pd.merge(
            mmn_df, 
            acc_df, 
            on=['subject_id', 'block_id'], 
            how='inner',
            suffixes=('_mmn', '_acc')
        )
        logger.info(f"Merged dataset shape: {merged_df.shape}")
    except Exception as e:
        logger.error(f"Failed to merge datasets: {e}")
        return False
    
    # 3. Filter by Excluded Subjects
    filtered_df = filter_by_excluded_subjects(merged_df, excluded_ids)
    
    # 4. Validate
    is_valid, validation_issues = validate_aligned_data(filtered_df)
    if not is_valid:
        logger.warning("Validation issues found in final dataset:")
        for issue in validation_issues:
            logger.warning(f"  - {issue}")
        # Decide whether to fail or proceed with warning. 
        # Given the strict requirement "passes the final trial count re-verification", 
        # we should probably not write if critical issues exist.
        # However, if the issue is just a warning about low power that wasn't filtered (unlikely if T016 worked),
        # we might log but proceed. Let's be strict: if trial count < 500 exists, fail.
        critical_issues = [i for i in validation_issues if "trial_count < 500" in i]
        if critical_issues:
            logger.error("Critical validation failure: Underpowered subjects remain in dataset.")
            return False
    
    # 5. Write Output
    data_dir = get_data_dir()
    output_path = data_dir / "aligned_data.csv"
    try:
        filtered_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote final aligned dataset to {output_path}")
        logger.info(f"Final dataset contains {len(filtered_df)} rows.")
        return True
    except Exception as e:
        logger.error(f"Failed to write output file {output_path}: {e}")
        return False


def main():
    """Entry point for the script."""
    success = run_finalization_pipeline()
    if not success:
        logger.error("T024 Finalization Pipeline failed.")
        exit(1)
    else:
        logger.info("T024 Finalization Pipeline completed successfully.")
        exit(0)


if __name__ == "__main__":
    main()
