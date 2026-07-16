"""
Data Ingestion and Preprocessing Pipeline for Eye-Tracking Data.

This script handles:
1. Loading raw eye-tracking data
2. Validating schema
3. Calculating data loss
4. Filtering low-quality participants
5. Detecting fixations (I-VT)
6. Mapping gaze points to ROIs
7. Handling edge cases
8. Generating the final preprocessed gaze dataset
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.data_loading import load_dundee_eye_tracking, load_boston_eye_tracking, fetch_eye_tracking_data
from utils.fixation_detection import detect_fixations_ivt, process_gaze_data
from utils.roi_mapping import (
    load_roi_config, 
    map_gaze_to_rois, 
    aggregate_fixation_roi_stats, 
    handle_zero_fixation_roi
)
from utils.logging_config import (
    setup_logging, 
    get_quality_logger, 
    get_exclusion_logger, 
    get_pipeline_logger,
    log_data_quality_warning,
    log_exclusion,
    log_pipeline_progress
)
from utils.environment_manager import get_paths, get_config_value, setup_reproducibility

# Setup logging
setup_logging()
pipeline_logger = get_pipeline_logger("ingest_preprocess")
quality_logger = get_quality_logger("ingest_preprocess")
exclusion_logger = get_exclusion_logger("ingest_preprocess")

def load_raw_eye_tracking_data(source_type: str = "dundee") -> pd.DataFrame:
    """
    Load raw eye-tracking data from the specified source.
    
    Args:
        source_type: 'dundee' or 'boston'
        
    Returns:
        DataFrame with raw gaze data
    """
    pipeline_logger.info(f"Loading raw eye-tracking data from {source_type} source.")
    
    try:
        if source_type == "dundee":
            df = load_dundee_eye_tracking()
        elif source_type == "boston":
            df = load_boston_eye_tracking()
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        if df is None or df.empty:
            raise ValueError(f"Failed to load data from {source_type} source.")
        
        pipeline_logger.info(f"Loaded {len(df)} raw gaze records.")
        return df
        
    except Exception as e:
        pipeline_logger.error(f"Error loading raw data: {e}")
        raise

def validate_raw_data(df: pd.DataFrame) -> bool:
    """
    Validate the raw data schema and basic quality checks.
    
    Args:
        df: Raw gaze DataFrame
        
    Returns:
        True if valid, False otherwise
    """
    required_columns = ['x', 'y', 'timestamp', 'participant_id', 'stimulus_id']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        quality_logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for NaN in critical columns
    critical_nan = df[required_columns].isna().sum()
    if critical_nan.any():
        quality_logger.warning(f"Found NaN values in critical columns: {critical_nan[critical_nan > 0].to_dict()}")
    
    pipeline_logger.info("Raw data validation passed.")
    return True

def calculate_data_loss(df: pd.DataFrame, participant_col: str = 'participant_id') -> pd.Series:
    """
    Calculate data loss percentage per participant.
    
    Args:
        df: Gaze DataFrame
        participant_col: Column name for participant ID
        
    Returns:
        Series of loss percentages per participant
    """
    # Assuming loss is calculated by missing timestamps or invalid coordinates
    # For this implementation, we'll count rows per participant and compare to a baseline
    # In a real scenario, we'd have a known number of expected samples per trial
    
    participant_counts = df.groupby(participant_col).size()
    total_samples = len(df)
    avg_samples = total_samples / len(participant_counts)
    
    # Simulate loss calculation based on deviation from mean (placeholder for real logic)
    # In a real implementation, we would compare against expected sample count per trial
    loss_percent = ((avg_samples - participant_counts) / avg_samples) * 100
    
    return loss_percent

def filter_low_quality_participants(
    df: pd.DataFrame, 
    threshold: float = 20.0,
    participant_col: str = 'participant_id'
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out participants with data loss > threshold (default 20%).
    
    Args:
        df: Gaze DataFrame
        threshold: Maximum allowed data loss percentage
        participant_col: Column name for participant ID
        
    Returns:
        Tuple of (filtered DataFrame, list of excluded participant IDs)
    """
    loss_series = calculate_data_loss(df, participant_col)
    excluded_participants = loss_series[loss_series > threshold].index.tolist()
    
    if excluded_participants:
        quality_logger.warning(f"Excluding {len(excluded_participants)} participants with >{threshold}% data loss.")
        for pid in excluded_participants:
            log_exclusion(exclusion_logger, pid, "High data loss")
        
        filtered_df = df[~df[participant_col].isin(excluded_participants)].copy()
        log_pipeline_progress(pipeline_logger, f"Filtered {len(excluded_participants)} low-quality participants.")
        return filtered_df, excluded_participants
    
    return df, []

def map_roi(
    df: pd.DataFrame, 
    config_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Map gaze points to Regions of Interest (ROIs).
    
    Args:
        df: Gaze DataFrame
        config_path: Path to ROI configuration file
        
    Returns:
        Tuple of (DataFrame with ROI assignments, count of excluded points)
    """
    rois = load_roi_config(config_path)
    return map_gaze_to_rois(df, rois=rois)

def handle_edge_cases(
    df: pd.DataFrame, 
    roi_col: str = 'roi_assigned',
    participant_col: str = 'participant_id',
    stimulus_col: str = 'stimulus_id'
) -> pd.DataFrame:
    """
    Handle edge cases:
    1. Exclude trials with missing ROI coordinates (already handled in map_roi)
    2. Treat zero fixations on source ROI as valid data (duration=0)
    
    Args:
        df: Gaze DataFrame
        roi_col: Column name for ROI assignments
        participant_col: Column name for participant ID
        stimulus_col: Column name for stimulus ID
        
    Returns:
        Processed DataFrame with edge cases handled
    """
    # Step 1: Aggregate fixation stats by ROI
    agg_df = aggregate_fixation_roi_stats(df, roi_col=roi_col)
    
    if agg_df.empty:
        quality_logger.warning("No valid fixation data found for aggregation.")
        return pd.DataFrame()
    
    # Step 2: Handle zero-fixation cases (ensure all ROIs are represented)
    final_df = handle_zero_fixation_roi(agg_df, roi_col=roi_col)
    
    pipeline_logger.info(f"Edge cases handled. Final dataset size: {len(final_df)}")
    return final_df

def preprocess_gaze_data(
    df: pd.DataFrame,
    fixation_threshold_ms: int = 100
) -> pd.DataFrame:
    """
    Apply fixation detection and data cleaning.
    
    Args:
        df: Raw gaze DataFrame
        fixation_threshold_ms: Minimum duration for a fixation (ms)
        
    Returns:
        DataFrame with detected fixations
    """
    pipeline_logger.info(f"Detecting fixations with threshold {fixation_threshold_ms}ms.")
    
    # Use the fixation detection utility
    fixations = process_gaze_data(df, min_duration=fixation_threshold_ms)
    
    if fixations is None or fixations.empty:
        quality_logger.warning("No fixations detected.")
        return pd.DataFrame()
    
    pipeline_logger.info(f"Detected {len(fixations)} fixations.")
    return fixations

def main():
    """
    Main execution pipeline for data ingestion and preprocessing.
    """
    log_pipeline_progress(pipeline_logger, "Starting data ingestion and preprocessing pipeline.")
    
    try:
        # 1. Load raw data
        raw_df = load_raw_eye_tracking_data(source_type="dundee")
        
        # 2. Validate
        if not validate_raw_data(raw_df):
            raise RuntimeError("Raw data validation failed.")
        
        # 3. Filter low-quality participants
        filtered_df, excluded_pids = filter_low_quality_participants(raw_df)
        log_pipeline_progress(pipeline_logger, f"Excluded participants: {excluded_pids}")
        
        # 4. Preprocess (fixation detection)
        fixations_df = preprocess_gaze_data(filtered_df, fixation_threshold_ms=100)
        
        if fixations_df.empty:
            raise RuntimeError("No fixations detected after preprocessing.")
        
        # 5. Map to ROIs
        mapped_df, excluded_points = map_roi(fixations_df)
        log_pipeline_progress(pipeline_logger, f"Excluded gaze points during ROI mapping: {excluded_points}")
        
        # 6. Handle edge cases
        final_df = handle_edge_cases(mapped_df)
        
        if final_df.empty:
            raise RuntimeError("Final dataset is empty after edge case handling.")
        
        # 7. Save output
        output_path = get_paths()['derived'] / 'preprocessed_gaze.csv'
        final_df.to_csv(output_path, index=False)
        log_pipeline_progress(pipeline_logger, f"Saved preprocessed gaze data to {output_path}")
        
        pipeline_logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        pipeline_logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
