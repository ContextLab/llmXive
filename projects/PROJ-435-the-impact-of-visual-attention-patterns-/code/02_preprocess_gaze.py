"""
Preprocess Gaze Data: Apply I-VT, ROI Mapping, and Edge Case Handling.

This script implements the full pipeline for User Story 1:
1. Load raw eye-tracking data (from T005).
2. Apply I-VT fixation detection (from T006).
3. Map gaze points to ROIs (from T015).
4. Filter low-quality participants (data_loss > 20%).
5. Handle edge cases:
   - Exclude trials with missing ROI coordinates.
   - Log exclusion counts to the exclusion logger and state file.
   - Treat zero fixations on source ROI as valid (duration=0).
6. Output: data/derived/preprocessed_gaze.csv
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np

# Import utilities from the project structure
from utils.data_loading import fetch_eye_tracking_data
from utils.fixation_detection import process_gaze_data, load_fixation_config
from utils.roi_mapping import map_gaze_to_rois, load_roi_config
from utils.logging_config import get_quality_logger, get_exclusion_logger, get_pipeline_logger, log_exclusion, log_pipeline_progress
from utils.environment_manager import load_config, get_paths, setup_reproducibility

# Ensure the code directory is in the path for imports if running as script
CODE_DIR = Path(__file__).parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

def load_raw_eye_tracking_data() -> pd.DataFrame:
    """
    Loads the raw eye-tracking data fetched in T005.
    Returns a DataFrame with columns: participant_id, headline_id, timestamp, x, y, ...
    """
    paths = get_paths()
    raw_data_path = paths['raw_data']
    
    if not raw_data_path.exists():
        logger = get_pipeline_logger()
        logger.error(f"Raw data file not found at {raw_data_path}. Please run T005 first.")
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    # Attempt to load as parquet first, then csv
    if raw_data_path.suffix == '.parquet':
        return pd.read_parquet(raw_data_path)
    else:
        return pd.read_csv(raw_data_path)

def validate_raw_data(df: pd.DataFrame) -> bool:
    """
    Validates that the raw data contains necessary columns for processing.
    """
    required_cols = ['participant_id', 'headline_id', 'timestamp', 'x', 'y']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger = get_quality_logger()
        logger.error(f"Raw data missing required columns: {missing}")
        return False
    return True

def calculate_data_loss(df: pd.DataFrame, threshold: float = 20.0) -> Tuple[pd.DataFrame, int]:
    """
    Calculates data loss per participant and filters out those exceeding the threshold.
    Returns filtered DataFrame and count of excluded participants.
    """
    logger = get_quality_logger()
    
    # Group by participant to calculate total points vs valid points
    # Assuming 'valid' is a boolean column or we infer from missing coordinates
    # For this implementation, we assume missing x/y or NaNs indicate loss
    total_points = df.groupby('participant_id').size()
    valid_points = df.groupby('participant_id').apply(lambda g: g[['x', 'y']].dropna().shape[0])
    
    data_loss_df = pd.DataFrame({
        'participant_id': total_points.index,
        'total_points': total_points.values,
        'valid_points': valid_points.values
    })
    
    data_loss_df['loss_percent'] = ((data_loss_df['total_points'] - data_loss_df['valid_points']) / data_loss_df['total_points']) * 100
    
    # Filter participants with > 20% loss
    excluded_participants = data_loss_df[data_loss_df['loss_percent'] > threshold]['participant_id'].tolist()
    excluded_count = len(excluded_participants)
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} participants with data loss > {threshold}%")
        for pid in excluded_participants:
            log_exclusion(f"Participant {pid} excluded due to data loss > {threshold}%")
    
    filtered_df = df[~df['participant_id'].isin(excluded_participants)]
    return filtered_df, excluded_count

def handle_edge_cases(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Handles edge cases:
    1. Exclude trials with missing ROI coordinates.
    2. Log exclusion counts.
    3. Treat zero fixations on source ROI as valid (duration=0).
    
    Returns:
        Tuple of (cleaned DataFrame, exclusion_counts_dict)
    """
    logger = get_exclusion_logger()
    exclusion_counts = {
        'missing_roi_coords': 0,
        'zero_source_fixations': 0,
        'total_rows_before': len(df)
    }

    # 1. Exclude trials with missing ROI coordinates
    # Assuming 'roi_x', 'roi_y' or similar are added by ROI mapping, or we check for NaN in ROI columns
    # If ROI mapping hasn't happened yet, we check for NaN in x/y which implies no ROI could be mapped
    # However, T015 (ROI Mapping) is a dependency. We assume ROI columns exist or are created here.
    # Let's assume the input 'df' has 'roi_type' from T015. If 'roi_type' is NaN, it's a missing ROI.
    
    if 'roi_type' in df.columns:
        missing_roi_mask = df['roi_type'].isna()
        if missing_roi_mask.any():
            count = missing_roi_mask.sum()
            exclusion_counts['missing_roi_coords'] = count
            logger.warning(f"Excluding {count} rows with missing ROI coordinates (unmapped gaze points).")
            df = df.dropna(subset=['roi_type'])
            log_exclusion(f"{count} rows excluded: missing ROI coordinates")

    # 2. Treat zero fixations on source ROI as valid
    # This is a data integrity check. If a participant has 0 fixations on source, 
    # we do NOT exclude them. We just ensure the duration is 0.
    # This logic is mostly informational for the log, as we don't exclude.
    # We count how many participants have 0 duration on source ROI to log it.
    if 'roi_type' in df.columns and 'fixation_duration' in df.columns:
        source_fixations = df[df['roi_type'] == 'source']
        if len(source_fixations) == 0:
            # No source fixations at all in the dataset? Unlikely but possible.
            logger.warning("No fixations found on 'source' ROI for any participant.")
            exclusion_counts['zero_source_fixations'] = len(df['participant_id'].unique())
        else:
            # Check per participant
            participants_with_zero_source = source_fixations.groupby('participant_id')['fixation_duration'].sum()
            zero_source_pids = participants_with_zero_source[participants_with_zero_source == 0].index.tolist()
            if zero_source_pids:
                exclusion_counts['zero_source_fixations'] = len(zero_source_pids)
                logger.info(f"Found {len(zero_source_pids)} participants with 0 total duration on source ROI. Retained as valid data.")
                # Ensure their duration is explicitly 0 if they exist in the dataframe (they should be 0 by aggregation)
    
    exclusion_counts['total_rows_after'] = len(df)
    return df, exclusion_counts

def preprocess_gaze_data() -> pd.DataFrame:
    """
    Main pipeline function to preprocess gaze data.
    """
    logger = get_pipeline_logger()
    logger.info("Starting gaze data preprocessing (T016: Edge Case Handling).")
    
    # Load config
    config = load_config()
    setup_reproducibility(config)
    paths = get_paths()
    
    # 1. Load Raw Data
    logger.info("Loading raw eye-tracking data...")
    raw_df = load_raw_eye_tracking_data()
    if not validate_raw_data(raw_df):
        raise ValueError("Raw data validation failed.")
    
    # 2. Apply I-VT Fixation Detection
    logger.info("Applying I-VT fixation detection...")
    config_fix = load_fixation_config()
    # process_gaze_data expects raw gaze and returns fixations
    fixation_df = process_gaze_data(raw_df, config_fix)
    
    # 3. Map to ROIs
    logger.info("Mapping gaze to ROIs...")
    config_roi = load_roi_config()
    # map_gaze_to_rois expects fixation data and ROI config
    # We assume it adds 'roi_type' column
    mapped_df = map_gaze_to_rois(fixation_df, config_roi)
    
    # 4. Filter Low Quality Participants
    logger.info("Filtering low-quality participants...")
    filtered_df, loss_count = calculate_data_loss(mapped_df, threshold=20.0)
    
    # 5. Handle Edge Cases (T016 Specific)
    logger.info("Handling edge cases (missing ROI, zero source fixations)...")
    cleaned_df, edge_counts = handle_edge_cases(filtered_df)
    
    # 6. Ensure Output Schema
    required_cols = ['participant_id', 'headline_id', 'fixation_duration', 'roi_type']
    for col in required_cols:
        if col not in cleaned_df.columns:
            # Fallback for missing columns if logic above didn't create them
            if col == 'fixation_duration' and 'duration' in cleaned_df.columns:
                cleaned_df['fixation_duration'] = cleaned_df['duration']
            elif col == 'roi_type':
                # If ROI mapping failed to assign, we might have NaNs, which we already dropped
                pass
    
    # Final cleanup: drop NaNs in critical columns just in case
    cleaned_df = cleaned_df.dropna(subset=required_cols)
    
    # Save exclusion stats to state
    state_dir = paths['state']
    state_dir.mkdir(parents=True, exist_ok=True)
    exclusion_log_path = state_dir / 'exclusion_stats.json'
    
    stats = {
        'data_loss_excluded': loss_count,
        'edge_case_exclusions': edge_counts
    }
    
    with open(exclusion_log_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Exclusion statistics saved to {exclusion_log_path}")
    
    return cleaned_df

def main():
    """
    Entry point for the script.
    """
    try:
        output_df = preprocess_gaze_data()
        paths = get_paths()
        output_path = paths['derived_gaze']
        
        output_df.to_csv(output_path, index=False)
        logging.getLogger().info(f"Preprocessed gaze data saved to {output_path}")
        print(f"Successfully wrote {len(output_df)} rows to {output_path}")
        
    except Exception as e:
        logging.getLogger().error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()