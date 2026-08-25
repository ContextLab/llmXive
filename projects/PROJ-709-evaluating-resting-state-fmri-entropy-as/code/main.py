"""
Main orchestration script for the fMRI Entropy Biomarker pipeline.

This script orchestrates the subject-loop to compute Sample Entropy features
for all valid subjects, skipping those listed in the exclusions log, and
aggregates the results into a single CSV file.

Output:
    data/processed/subject_entropy_features.csv
        A matrix of shape (N_subjects, N_parcels + 1) containing subject IDs
        and their corresponding entropy values for each parcel.
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
import numpy as np
import pandas as pd

# Import from sibling modules using the exact API surface provided
from entropy_engine import compute_entropy_features, load_scrubbed_subject, truncate_time_series
from preprocessing import process_subject_truncation
from utils import setup_logger
from config import (
    TARGET_LENGTH,
    ATLAS_N,
    DATASET_ID,
    R_FACTOR,
    M
)

# Configure logging
logger = setup_logger("main")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"

EXCLUSIONS_LOG_PATH = DATA_RAW_DIR / "exclusions.log"
VALID_SUBJECTS_CSV_PATH = DATA_DERIVED_DIR / "valid_subjects.csv"
OUTPUT_CSV_PATH = DATA_PROCESSED_DIR / "subject_entropy_features.csv"

def load_valid_subjects() -> List[Dict[str, Any]]:
    """
    Load the list of valid subjects from the derived CSV.
    
    Returns:
        List of dictionaries containing subject metadata (subject_id, path, etc.).
    """
    if not VALID_SUBJECTS_CSV_PATH.exists():
        logger.error(f"Valid subjects file not found: {VALID_SUBJECTS_CSV_PATH}")
        raise FileNotFoundError(f"Valid subjects file not found: {VALID_SUBJECTS_CSV_PATH}")
    
    df = pd.read_csv(VALID_SUBJECTS_CSV_PATH)
    # Ensure we have the necessary columns
    required_cols = ['subject_id', 'nifti_path']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {VALID_SUBJECTS_CSV_PATH}: {missing_cols}")
    
    return df.to_dict(orient='records')

def load_exclusions() -> Set[str]:
    """
    Load the set of excluded subject IDs from the exclusions log.
    
    Returns:
        Set of subject IDs that should be skipped.
    """
    excluded_ids = set()
    if not EXCLUSIONS_LOG_PATH.exists():
        logger.warning(f"Exclusions log not found: {EXCLUSIONS_LOG_PATH}. Proceeding without exclusions.")
        return excluded_ids
    
    with open(EXCLUSIONS_LOG_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'subject_id' in row:
                excluded_ids.add(row['subject_id'])
    
    logger.info(f"Loaded {len(excluded_ids)} excluded subjects from {EXCLUSIONS_LOG_PATH}")
    return excluded_ids

def process_single_subject(subject_info: Dict[str, Any], exclusions: Set[str]) -> Optional[Dict[str, Any]]:
    """
    Process a single subject: check exclusions, load data, truncate, compute entropy.
    
    Args:
        subject_info: Dictionary with subject metadata (subject_id, nifti_path).
        exclusions: Set of excluded subject IDs.
        
    Returns:
        Dictionary with subject_id and entropy features, or None if skipped/failed.
    """
    subject_id = subject_info['subject_id']
    nifti_path = subject_info['nifti_path']
    
    # Check exclusions
    if subject_id in exclusions:
        logger.info(f"Skipping excluded subject: {subject_id}")
        return None
    
    if not os.path.exists(nifti_path):
        logger.error(f"NIfTI file not found for subject {subject_id}: {nifti_path}")
        return None
    
    try:
        # Step 1: Load scrubbed subject data (assumes preprocessing has been run)
        # Note: T013/T014/T015 ensure scrubbed files exist in data/processed/
        # We expect the path to be the scrubbed version or the original if scrubbing was in-place
        # For this pipeline, we assume the input path points to the preprocessed/scrubbed data
        # or we load from the expected processed location.
        # Based on T015, we read from data/processed/scrubbed_*.nii.gz
        
        # Construct expected scrubbed path if input was raw
        if "scrubbed" not in nifti_path:
            # Try to find the scrubbed version in processed
            scrubbed_name = f"scrubbed_{subject_id}.nii.gz"
            scrubbed_path = DATA_PROCESSED_DIR / scrubbed_name
            if scrubbed_path.exists():
                nifti_path = str(scrubbed_path)
            else:
                logger.warning(f"Scrubbed file not found for {subject_id}, attempting to use original: {nifti_path}")
        
        # Load time series
        time_series = load_scrubbed_subject(nifti_path)
        
        if time_series is None or time_series.shape[0] == 0:
            logger.error(f"Failed to load time series for subject {subject_id}")
            return None
        
        # Step 2: Truncate to target length (T014/T015 requirement)
        # T015 specifies: FIRST truncate, THEN compute SD
        truncated_ts = truncate_time_series(time_series, TARGET_LENGTH)
        
        if truncated_ts.shape[0] < TARGET_LENGTH:
            logger.warning(f"Subject {subject_id} has fewer than {TARGET_LENGTH} volumes after truncation: {truncated_ts.shape[0]}")
            # We proceed with what we have, but log it
        
        # Step 3: Compute entropy features
        # m and r are from config
        entropy_values = compute_entropy_features(
            time_series_data=truncated_ts,
            m=M,
            r_factor=R_FACTOR
        )
        
        if entropy_values is None or len(entropy_values) == 0:
            logger.error(f"Entropy computation failed for subject {subject_id}")
            return None
        
        # Handle zero variance parcels (T016)
        # The compute_entropy_features should handle this internally or we do it here
        # Assuming compute_entropy_features returns a list/array of values for all parcels
        
        return {
            'subject_id': subject_id,
            **{f'parcel_{i}': val for i, val in enumerate(entropy_values)}
        }
        
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {str(e)}", exc_info=True)
        return None

def main():
    """
    Main entry point for the pipeline orchestration.
    
    1. Loads valid subjects and exclusions.
    2. Iterates through subjects, computing entropy features.
    3. Aggregates results and writes to data/processed/subject_entropy_features.csv.
    """
    logger.info("Starting main pipeline orchestration...")
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data lists
    try:
        valid_subjects = load_valid_subjects()
        exclusions = load_exclusions()
    except Exception as e:
        logger.critical(f"Failed to load subject lists: {e}")
        return 1
    
    logger.info(f"Found {len(valid_subjects)} valid subjects. {len(exclusions)} excluded.")
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for subject_info in valid_subjects:
        subject_id = subject_info['subject_id']
        logger.info(f"Processing subject {subject_id}...")
        
        result = process_single_subject(subject_info, exclusions)
        
        if result is not None:
            results.append(result)
            successful_count += 1
        else:
            failed_count += 1
            logger.error(f"Skipping subject {subject_id} due to failure.")
    
    if not results:
        logger.error("No subjects were successfully processed. Aborting output generation.")
        return 1
    
    # Convert to DataFrame and write CSV
    df_output = pd.DataFrame(results)
    
    # Ensure subject_id is the first column
    cols = ['subject_id'] + [c for c in df_output.columns if c != 'subject_id']
    df_output = df_output[cols]
    
    df_output.to_csv(OUTPUT_CSV_PATH, index=False)
    
    logger.info(f"Pipeline complete. Successfully processed {successful_count} subjects.")
    logger.info(f"Failed to process {failed_count} subjects.")
    logger.info(f"Output written to: {OUTPUT_CSV_PATH}")
    
    # Verify output shape
    expected_parcels = ATLAS_N  # Assuming 200 parcels + 1 ID column = 201
    actual_cols = len(df_output.columns)
    if actual_cols != expected_parcels + 1:
        logger.warning(f"Output column count ({actual_cols}) does not match expected ({expected_parcels + 1}).")
    
    return 0

if __name__ == "__main__":
    exit(main())
