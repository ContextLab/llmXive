"""
Edge case handling for ROI mapping.

This module provides functionality to:
1. Exclude trials with missing ROI coordinates
2. Log exclusion counts and reasons
3. Handle zero fixations on source ROI (treated as valid data)
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from utils.logging_config import get_exclusion_logger, get_pipeline_logger

def load_roi_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load ROI configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default path.
        
    Returns:
        Dictionary containing ROI configuration parameters.
    """
    if config_path is None:
        config_path = Path("code/config.yaml")
        
    if not config_path.exists():
        logging.warning(f"ROI config file not found at {config_path}, using defaults")
        return {
            "source_attribution_box": [0, 0, 100, 100],
            "other_box": [0, 0, 100, 100],
            "min_coordinates": 2,
            "allow_zero_fixations": True
        }
        
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    return config.get('roi', {})

def is_roi_coordinate_valid(row: pd.Series, roi_columns: List[str]) -> bool:
    """
    Check if a row has valid ROI coordinates.
    
    Args:
        row: DataFrame row to check
        roi_columns: List of column names that should contain ROI coordinates
        
    Returns:
        True if all ROI coordinates are present and valid, False otherwise
    """
    for col in roi_columns:
        if col not in row.index:
            return False
        value = row[col]
        if pd.isna(value) or (isinstance(value, (int, float)) and np.isnan(value)):
            return False
        # Check for invalid coordinate formats (e.g., None, empty string)
        if value is None or value == "" or value == "nan":
            return False
    return True

def exclude_trials_with_missing_roi(
    df: pd.DataFrame,
    roi_columns: List[str],
    exclusion_log_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, int, List[Dict[str, Any]]]:
    """
    Exclude trials with missing ROI coordinates and log exclusions.
    
    This function implements the edge case handling for T016:
    - Identifies trials where ROI coordinates are missing
    - Excludes these trials from the dataset
    - Logs exclusion counts and reasons
    
    Args:
        df: Input DataFrame with gaze/fixation data
        roi_columns: List of column names containing ROI coordinates
        exclusion_log_path: Optional path to write exclusion log
        
    Returns:
        Tuple of (filtered DataFrame, number of excluded trials, list of exclusion records)
    """
    pipeline_logger = get_pipeline_logger()
    exclusion_logger = get_exclusion_logger()
    
    total_trials = len(df)
    if total_trials == 0:
        pipeline_logger.warning("Input DataFrame is empty, no trials to process")
        return df, 0, []
    
    # Identify rows with missing ROI coordinates
    missing_mask = pd.DataFrame(False, index=df.index, columns=['missing_roi'])
    for col in roi_columns:
        if col not in df.columns:
            missing_mask['missing_roi'] = True
            pipeline_logger.error(f"Required ROI column '{col}' not found in DataFrame")
            continue
        
        # Check for NaN, None, or invalid values
        col_missing = df[col].isna() | (df[col] == "") | (df[col] == "nan")
        missing_mask['missing_roi'] = missing_mask['missing_roi'] | col_missing
    
    # Count exclusions
    excluded_indices = df[missing_mask['missing_roi']].index
    excluded_count = len(excluded_indices)
    retained_count = total_trials - excluded_count
    
    # Log exclusions
    exclusion_records = []
    if excluded_count > 0:
        # Log individual exclusions
        for idx in excluded_indices:
            trial_info = df.loc[idx].to_dict()
            exclusion_record = {
                "trial_id": trial_info.get('trial_id', 'unknown'),
                "participant_id": trial_info.get('participant_id', 'unknown'),
                "headline_id": trial_info.get('headline_id', 'unknown'),
                "reason": "missing_roi_coordinates",
                "missing_columns": [col for col in roi_columns if col in trial_info and pd.isna(trial_info.get(col))]
            }
            exclusion_records.append(exclusion_record)
            exclusion_logger.warning(
                f"Excluded trial {exclusion_record['trial_id']} for participant "
                f"{exclusion_record['participant_id']}: missing ROI coordinates "
                f"{exclusion_record['missing_columns']}"
            )
        
        pipeline_logger.info(
            f"Excluded {excluded_count} trials ({excluded_count/total_trials*100:.2f}%) "
            f"due to missing ROI coordinates. Retained {retained_count} trials."
        )
        
        # Write exclusion log to file if path provided
        if exclusion_log_path:
            exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(exclusion_log_path, 'r') as f:
                    existing_logs = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_logs = []
                
            existing_logs.extend(exclusion_records)
            
            with open(exclusion_log_path, 'w') as f:
                json.dump(existing_logs, f, indent=2)
            
            pipeline_logger.info(f"Exclusion log written to {exclusion_log_path}")
    
    # Filter DataFrame
    filtered_df = df[~missing_mask['missing_roi']].reset_index(drop=True)
    
    return filtered_df, excluded_count, exclusion_records

def handle_zero_fixation_roi(
    df: pd.DataFrame,
    roi_type_column: str = 'roi_type',
    source_roi_value: str = 'source_attribution'
) -> Tuple[pd.DataFrame, int]:
    """
    Handle trials with zero fixations on source ROI.
    
    Per T017, these are treated as valid data (duration=0) rather than missing.
    This function ensures such trials are kept and properly marked.
    
    Args:
        df: Input DataFrame with fixation data
        roi_type_column: Column name containing ROI type
        source_roi_value: Value representing the source attribution ROI
        
    Returns:
        Tuple of (DataFrame with zero-fixation trials marked, count of such trials)
    """
    pipeline_logger = get_pipeline_logger()
    
    if roi_type_column not in df.columns:
        pipeline_logger.warning(f"ROI type column '{roi_type_column}' not found")
        return df, 0
    
    # Identify trials with zero fixations on source ROI
    # Assuming duration=0 or fixation_count=0 indicates zero fixations
    zero_fixation_mask = (
        (df[roi_type_column] == source_roi_value) & 
        ((df['duration'] == 0) | (df['duration'].isna()))
    )
    
    zero_fixation_count = zero_fixation_mask.sum()
    
    if zero_fixation_count > 0:
        pipeline_logger.info(
            f"Found {zero_fixation_count} trials with zero fixations on source ROI. "
            f"Treated as valid data per T017."
        )
        
        # Ensure duration is explicitly set to 0 for clarity
        df.loc[zero_fixation_mask, 'duration'] = 0
        df.loc[zero_fixation_mask, 'zero_fixation_source_roi'] = True
    else:
        df['zero_fixation_source_roi'] = False
    
    return df, int(zero_fixation_count)

def aggregate_exclusion_stats(
    exclusion_records: List[Dict[str, Any]],
    total_trials: int,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Aggregate and summarize exclusion statistics.
    
    Args:
        exclusion_records: List of individual exclusion records
        total_trials: Total number of trials before exclusion
        output_path: Optional path to write summary statistics
        
    Returns:
        Dictionary containing aggregated exclusion statistics
    """
    if not exclusion_records:
        stats = {
            "total_trials": total_trials,
            "excluded_trials": 0,
            "retained_trials": total_trials,
            "exclusion_rate": 0.0,
            "reasons": {}
        }
    else:
        reasons = {}
        for record in exclusion_records:
            reason = record.get('reason', 'unknown')
            reasons[reason] = reasons.get(reason, 0) + 1
        
        excluded_count = len(exclusion_records)
        stats = {
            "total_trials": total_trials,
            "excluded_trials": excluded_count,
            "retained_trials": total_trials - excluded_count,
            "exclusion_rate": excluded_count / total_trials if total_trials > 0 else 0.0,
            "reasons": reasons
        }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
    
    return stats

def main():
    """
    Main entry point for testing edge case handling.
    
    This function demonstrates the exclusion of trials with missing ROI coordinates
    and logs the exclusion counts as required by T016.
    """
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Handle ROI edge cases")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file path")
    parser.add_argument("--exclusion-log", type=str, default="state/exclusions.json", help="Exclusion log path")
    parser.add_argument("--stats", type=str, default="state/exclusion_stats.json", help="Exclusion stats path")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    pipeline_logger = get_pipeline_logger()
    
    pipeline_logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    # Define ROI columns (adjust based on actual data schema)
    roi_columns = ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2']
    
    # Check if ROI columns exist, if not, try common alternatives
    available_roi_cols = [col for col in roi_columns if col in df.columns]
    if not available_roi_cols:
        # Try to find any column with 'roi' in the name
        roi_cols_from_data = [col for col in df.columns if 'roi' in col.lower()]
        if roi_cols_from_data:
            available_roi_cols = roi_cols_from_data[:4]  # Take first 4
            pipeline_logger.warning(
                f"Standard ROI columns not found. Using: {available_roi_cols}"
            )
        else:
            pipeline_logger.error("No ROI coordinate columns found in data")
            raise ValueError("No ROI coordinate columns found in input data")
    
    pipeline_logger.info(f"Using ROI columns: {available_roi_cols}")
    
    # Exclude trials with missing ROI coordinates
    filtered_df, excluded_count, exclusion_records = exclude_trials_with_missing_roi(
        df, 
        available_roi_cols, 
        Path(args.exclusion_log)
    )
    
    # Aggregate and log statistics
    stats = aggregate_exclusion_stats(
        exclusion_records, 
        len(df), 
        Path(args.stats)
    )
    
    pipeline_logger.info(f"Exclusion statistics: {stats}")
    
    # Save filtered data
    filtered_df.to_csv(args.output, index=False)
    pipeline_logger.info(f"Saved filtered data to {args.output}")
    
    return 0

if __name__ == "__main__":
    exit(main())
