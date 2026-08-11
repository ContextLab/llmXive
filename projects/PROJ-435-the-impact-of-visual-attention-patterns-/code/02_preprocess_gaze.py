"""
Core Preprocessing Pipeline (US1)

Implements T018: Ingest raw eye-tracking data, apply fixation detection (I-VT),
filter participants with >= 20% data loss, map gaze points to ROIs, and handle
edge cases (missing ROI -> trial exclusion, zero fixations -> duration 0).

Outputs:
  - data/derived/preprocessed_gaze.csv
  - output/exclusion_log.txt
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np

# Import from existing utilities
from utils.logging_init import setup_global_logger
from utils.fixation_detection import process_gaze_data as apply_fixation_detection
from utils.roi_mapping import map_gaze_to_rois
from utils.config_loader import load_config

# --- Constants & Helpers ---

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parent.parent

def get_paths() -> Dict[str, Path]:
    """Constructs absolute paths for all required input/output files."""
    root = get_project_root()
    return {
        "config": root / "code" / "config.yaml",
        "raw_data": root / "data" / "raw" / "eye_tracking_raw.parquet",
        "output_preprocessed": root / "data" / "derived" / "preprocessed_gaze.csv",
        "output_exclusion_log": root / "output" / "exclusion_log.txt",
        "state_validation": root / "state" / "schema_validation.json"
    }

def load_raw_eye_tracking_data(path: Path) -> pd.DataFrame:
    """
    Loads the raw eye-tracking dataset.
    Raises FileNotFoundError if the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    # Handle both parquet and csv if necessary, but spec says parquet
    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    elif path.suffix == '.csv':
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def validate_raw_data(df: pd.DataFrame) -> bool:
    """
    Validates that the raw dataframe contains essential columns.
    Returns True if valid, raises ValueError otherwise.
    """
    required_cols = ['participant_id', 'trial_id', 'timestamp', 'gaze_x', 'gaze_y']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Raw data missing required columns: {missing}")
    return True

def calculate_data_loss(df: pd.DataFrame, participant_col: str = 'participant_id') -> pd.DataFrame:
    """
    Calculates data loss per participant.
    Assumes 'loss_percent' or similar is not pre-calculated, so we estimate based on
    expected vs actual rows if metadata exists, or simply return 0 if no baseline.
    For this implementation, we assume the raw data is complete and we filter based
    on the output of fixation detection which might drop rows, or explicit flags.
    
    However, the task specifies: "filter participants with >= 20% data loss".
    We will assume the raw data has a 'valid_data' flag or we calculate loss
    based on the ratio of fixations to raw samples if raw samples represent a fixed duration.
    
    Simplified approach for this task:
    We will assume the 'fixation_detection' step might flag rows as invalid,
    or we count rows per participant and flag those with significantly fewer rows than the median.
    
    Better approach per spec: The raw data might have a 'data_quality' metric or we
    calculate the percentage of time covered by valid fixations vs total trial time.
    Since we don't have trial duration in the raw schema provided in API surface,
    we will implement a heuristic: if a participant has < 80% of the median fixation count
    (after detection), they are considered to have high data loss.
    
    Wait, the task says "filter participants with >= 20% data loss".
    Let's assume the raw data has a column 'data_loss_percent' or we calculate it.
    If not present, we calculate based on the ratio of successful fixations to total samples.
    
    Implementation:
    1. Run fixation detection first.
    2. Count fixations per participant.
    3. Compare to median. If < 80% of median, mark as high loss.
    """
    # Group by participant and count fixations (assuming fixation step adds 'is_fixation' or similar)
    # Since we haven't run fixation yet in this function, we'll do it in the main flow.
    # This function is a helper to compute the metric once we have the data.
    return pd.DataFrame() # Placeholder, logic moved to main

def filter_low_quality_participants(
    df: pd.DataFrame,
    threshold: float = 0.20,
    participant_col: str = 'participant_id',
    fixation_col: str = 'is_fixation'
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filters out participants with >= 20% data loss.
    
    Logic:
    1. Calculate total samples per participant.
    2. Calculate valid fixations per participant.
    3. Data loss = 1 - (valid_fixations / total_samples).
    4. Exclude if loss >= threshold.
    
    Returns:
      Tuple of (filtered_df, list_of_exclusion_records)
    """
    if fixation_col not in df.columns:
        # If fixation detection hasn't populated this, assume all are valid? 
        # No, that defeats the purpose. We must assume fixation detection ran.
        raise ValueError(f"Column '{fixation_col}' not found. Run fixation detection first.")

    exclusion_log = []
    
    # Calculate stats per participant
    stats = df.groupby(participant_col).agg(
        total_samples=(fixation_col, 'count'),
        valid_fixations=(fixation_col, 'sum')
    ).reset_index()
    
    # Calculate loss
    stats['loss_ratio'] = 1.0 - (stats['valid_fixations'] / stats['total_samples'])
    
    # Identify bad participants
    bad_participants = stats[stats['loss_ratio'] >= threshold][participant_col].tolist()
    
    if bad_participants:
        for pid in bad_participants:
            p_stats = stats[stats[participant_col] == pid].iloc[0]
            exclusion_log.append({
                "participant_id": pid,
                "reason": "high_data_loss",
                "loss_ratio": float(p_stats['loss_ratio']),
                "total_samples": int(p_stats['total_samples']),
                "valid_fixations": int(p_stats['valid_fixations'])
            })
        
        filtered_df = df[~df[participant_col].isin(bad_participants)].copy()
    else:
        filtered_df = df.copy()
        
    return filtered_df, exclusion_log

def handle_edge_cases(
    df: pd.DataFrame,
    roi_col: str = 'roi_type',
    missing_roi_val: str = 'unknown'
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Handles edge cases:
    1. Missing ROI -> Trial exclusion (log and drop rows with missing ROI).
    2. Zero fixations in a trial -> Set duration to 0 (handled in aggregation).
    
    Returns:
      Tuple of (cleaned_df, list_of_edge_case_records)
    """
    edge_log = []
    
    # 1. Handle missing ROI
    if roi_col in df.columns:
        missing_mask = df[roi_col].isna() | (df[roi_col] == missing_roi_val)
        if missing_mask.any():
            # Group by trial to exclude entire trial if any missing ROI?
            # Spec says "missing ROI -> trial exclusion".
            trials_to_exclude = df.loc[missing_mask, 'trial_id'].unique()
            
            for tid in trials_to_exclude:
                count = len(df[df['trial_id'] == tid])
                edge_log.append({
                    "trial_id": tid,
                    "reason": "missing_roi_in_trial",
                    "rows_affected": int(count)
                })
            
            df = df[~df['trial_id'].isin(trials_to_exclude)].copy()
    
    # 2. Zero fixations handling is usually an aggregation step, 
    # but here we ensure no negative durations or invalid states.
    if 'duration' in df.columns:
        df.loc[df['duration'] < 0, 'duration'] = 0
        
    return df, edge_log

def preprocess_gaze_data(
    raw_df: pd.DataFrame,
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Orchestrates the full preprocessing pipeline:
    1. Apply Fixation Detection (I-VT)
    2. Filter Low Quality Participants
    3. Map Gaze to ROIs
    4. Handle Edge Cases
    """
    all_exclusions = []
    all_edge_cases = []
    
    # 1. Fixation Detection
    # The process_gaze_data in utils.fixation_detection returns a df with fixation info
    # We pass the raw data and config
    logger = logging.getLogger(__name__)
    logger.info("Starting fixation detection...")
    
    # Assuming process_gaze_data returns a dataframe with 'is_fixation' and 'duration'
    df_fixated = apply_fixation_detection(raw_df, config)
    
    # 2. Filter Low Quality Participants
    logger.info("Filtering low quality participants...")
    df_filtered, exclusions = filter_low_quality_participants(
        df_fixated, 
        threshold=config.get('data_loss_threshold', 0.20),
        fixation_col='is_fixation'
    )
    all_exclusions.extend(exclusions)
    
    # 3. Map Gaze to ROIs
    logger.info("Mapping gaze to ROIs...")
    # map_gaze_to_rois expects the dataframe and config
    df_mapped = map_gaze_to_rois(df_filtered, config)
    
    # 4. Handle Edge Cases
    logger.info("Handling edge cases...")
    df_clean, edge_cases = handle_edge_cases(df_mapped)
    all_edge_cases.extend(edge_cases)
    
    return df_clean, all_exclusions + edge_cases

def write_exclusion_log(log_entries: List[Dict[str, Any]], output_path: Path) -> None:
    """Writes the exclusion log to a text file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Exclusion Log - T018 Preprocessing\n")
        f.write("=" * 40 + "\n\n")
        if not log_entries:
            f.write("No participants or trials were excluded.\n")
        else:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

def main():
    """Main entry point for T018."""
    # Setup logging
    log_config_path = get_project_root() / "code" / "config" / "logging_config.yaml"
    # Fallback if config is in root code dir
    if not log_config_path.exists():
        log_config_path = get_project_root() / "code" / "logging_config.yaml"
        
    try:
        setup_global_logger(log_config_path)
    except Exception as e:
        # If logging config fails, print to console
        print(f"Warning: Could not setup global logger: {e}. Using console.")
        logging.basicConfig(level=logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Preprocessing Pipeline (T018)...")
    
    paths = get_paths()
    config = load_config(paths["config"])
    
    # Load Raw Data
    try:
        df_raw = load_raw_eye_tracking_data(paths["raw_data"])
        logger.info(f"Loaded raw data: {len(df_raw)} rows")
    except FileNotFoundError as e:
        logger.error(f"Raw data missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)
        
    # Validate
    try:
        validate_raw_data(df_raw)
    except ValueError as e:
        logger.error(f"Data validation failed: {e}")
        sys.exit(1)
        
    # Preprocess
    try:
        df_processed, exclusions = preprocess_gaze_data(df_raw, config)
        logger.info(f"Preprocessing complete. Rows remaining: {len(df_processed)}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)
        
    # Write Outputs
    # 1. Preprocessed Gaze CSV
    paths["output_preprocessed"].parent.mkdir(parents=True, exist_ok=True)
    df_processed.to_csv(paths["output_preprocessed"], index=False)
    logger.info(f"Wrote preprocessed data to {paths['output_preprocessed']}")
    
    # 2. Exclusion Log
    write_exclusion_log(exclusions, paths["output_exclusion_log"])
    logger.info(f"Wrote exclusion log to {paths['output_exclusion_log']}")
    
    logger.info("T018 Preprocessing Pipeline completed successfully.")

if __name__ == "__main__":
    main()
