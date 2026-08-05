import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import load_config
from utils.fixation_detection import detect_fixations_ivt, process_gaze_data
from utils.roi_mapping import map_gaze_to_rois, handle_zero_fixation_roi as roi_handle_zero
from utils.roi_edge_cases import exclude_trials_with_missing_roi, handle_zero_fixation_roi as edge_handle_zero, aggregate_exclusion_stats
from utils.logging_config import get_pipeline_logger, get_exclusion_logger

# Initialize loggers
pipeline_logger = get_pipeline_logger()
exclusion_logger = get_exclusion_logger()

def get_project_root() -> Path:
    return project_root

def load_raw_eye_tracking_data(raw_data_path: Path) -> pd.DataFrame:
    """
    Load raw eye-tracking data from parquet file.
    """
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    try:
        df = pd.read_parquet(raw_data_path)
        pipeline_logger.info(f"Loaded raw data from {raw_data_path}: {len(df)} rows")
        return df
    except Exception as e:
        pipeline_logger.error(f"Failed to load raw data: {e}")
        raise

def validate_raw_data(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe contains required columns.
    """
    required_cols = ['participant_id', 'headline_id', 'timestamp', 'x', 'y']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in raw data: {missing}")
    return True

def calculate_data_loss(df: pd.DataFrame, max_loss_threshold: float = 0.20) -> pd.DataFrame:
    """
    Calculate data loss per participant and filter out low-quality participants.
    Data loss is calculated as (1 - (valid_gaze_points / expected_gaze_points)).
    For this implementation, we assume valid gaze points are those with finite coordinates.
    """
    # Count valid gaze points per participant
    df['is_valid'] = df['x'].notna() & df['y'].notna() & df['x'].apply(np.isfinite) & df['y'].apply(np.isfinite)
    
    participant_stats = df.groupby('participant_id').agg({
        'is_valid': ['sum', 'count']
    }).reset_index()
    participant_stats.columns = ['participant_id', 'valid_count', 'total_count']
    
    participant_stats['data_loss_percent'] = 1 - (participant_stats['valid_count'] / participant_stats['total_count'])
    
    # Merge back to main dataframe
    df = df.merge(participant_stats[['participant_id', 'data_loss_percent']], on='participant_id', how='left')
    
    return df

def filter_low_quality_participants(df: pd.DataFrame, threshold: float = 0.20) -> pd.DataFrame:
    """
    Filter participants with data_loss_percent >= threshold.
    """
    if 'data_loss_percent' not in df.columns:
        raise ValueError("Data loss not calculated. Run calculate_data_loss first.")
    
    filtered_df = df[df['data_loss_percent'] < threshold].copy()
    excluded_count = len(df) - len(filtered_df)
    
    if excluded_count > 0:
        exclusion_logger.warning(f"Excluded {excluded_count} rows from participants with data loss >= {threshold*100}%")
    
    return filtered_df

def handle_edge_cases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle edge cases:
    1. Exclude trials with missing ROI coordinates.
    2. Treat zero fixations on source ROI as valid (duration=0).
    """
    # 1. Exclude trials with missing ROI coordinates
    # We assume 'source_attribution_roi' column exists after ROI mapping
    # If not, we might need to map ROI first, but per task order, we do this after mapping
    # However, for T016, we are specifically handling the exclusion logic.
    # We will assume the ROI mapping step (T015) has added the 'source_attribution_roi' column.
    
    if 'source_attribution_roi' in df.columns:
        df, excluded_count, excluded_ids = exclude_trials_with_missing_roi(
            df, 
            roi_column='source_attribution_roi', 
            roi_type='source_attribution'
        )
        
        if excluded_count > 0:
            exclusion_logger.warning(f"Excluded {excluded_count} trials due to missing source_attribution ROI coordinates.")
            # Log to output/exclusion_log.txt as per task requirement
            output_dir = get_project_root() / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)
            log_path = output_dir / 'exclusion_log.txt'
            
            # Aggregate stats and write to log
            total_trials_before = len(df) + excluded_count
            stats = aggregate_exclusion_stats(total_trials_before, excluded_count, log_path)
            exclusion_logger.info(f"Exclusion log updated at {log_path}")
    else:
        pipeline_logger.warning("Column 'source_attribution_roi' not found. Skipping ROI coordinate exclusion.")

    # 2. Handle zero fixations on source ROI
    # This is handled by ensuring duration is 0, not NaN
    df = handle_zero_fixation_roi(df, roi_type='source_attribution', duration_col='fixation_duration')
    
    return df

def preprocess_gaze_data(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Main preprocessing pipeline:
    1. Apply I-VT fixation detection
    2. Map gaze to ROIs
    3. Filter low quality participants
    4. Handle edge cases (T016, T017)
    """
    # 1. I-VT Detection
    pipeline_logger.info("Starting I-VT fixation detection...")
    df_fixated = process_gaze_data(df, config)
    
    # 2. ROI Mapping
    pipeline_logger.info("Mapping gaze to ROIs...")
    df_roi = map_gaze_to_rois(df_fixated, config)
    
    # 3. Filter Low Quality
    pipeline_logger.info("Filtering low quality participants...")
    df_filtered = filter_low_quality_participants(df_roi)
    
    # 4. Handle Edge Cases (T016, T017)
    pipeline_logger.info("Handling edge cases (missing ROI, zero fixations)...")
    df_final = handle_edge_cases(df_filtered)
    
    return df_final

def main():
    """
    Main entry point for the preprocessing script.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    config = load_config()
    
    # Define paths
    raw_data_path = get_project_root() / 'data' / 'raw' / 'eye_tracking_raw.parquet'
    output_path = get_project_root() / 'data' / 'derived' / 'preprocessed_gaze.csv'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df_raw = load_raw_eye_tracking_data(raw_data_path)
        
        # Validate
        validate_raw_data(df_raw)
        
        # Preprocess
        df_processed = preprocess_gaze_data(df_raw, config)
        
        # Save output
        df_processed.to_csv(output_path, index=False)
        pipeline_logger.info(f"Preprocessing complete. Output saved to {output_path}")
        pipeline_logger.info(f"Total rows in output: {len(df_processed)}")
        
    except Exception as e:
        pipeline_logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
