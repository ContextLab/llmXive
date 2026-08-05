"""
ROI Mapping Utilities for Visual Attention Analysis.

This module implements the logic to assign gaze points to specific Regions of Interest (ROIs),
specifically "source_attribution" and other bounding boxes defined in the configuration.
It handles the geometric containment checks and aggregation of fixation data per ROI.
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from utils.config_loader import load_config

logger = logging.getLogger(__name__)

def load_roi_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load ROI configuration from the project config file.

    Args:
        config_path: Optional path to config.yaml. If None, uses default project root location.

    Returns:
        Dictionary containing ROI definitions.
    """
    if config_path is None:
        # Default to code/config.yaml relative to project root
        config_path = Path("code/config.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"ROI config file not found at {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f) if config_path.suffix == '.json' else load_config(config_path)

    if 'rois' not in config:
        raise ValueError("Config missing 'rois' key. Expected ROI definitions (e.g., source_attribution).")
    
    return config['rois']

def is_point_in_roi(x: float, y: float, roi_coords: Dict[str, float]) -> bool:
    """
    Check if a gaze point (x, y) falls within a rectangular ROI.

    Args:
        x: X coordinate of the gaze point.
        y: Y coordinate of the gaze point.
        roi_coords: Dictionary containing 'x_min', 'y_min', 'x_max', 'y_max'.

    Returns:
        True if the point is inside the ROI, False otherwise.
    """
    x_min = roi_coords.get('x_min', 0)
    y_min = roi_coords.get('y_min', 0)
    x_max = roi_coords.get('x_max', 1)
    y_max = roi_coords.get('y_max', 1)

    return x_min <= x <= x_max and y_min <= y <= y_max

def map_single_point_to_roi(x: float, y: float, rois: Dict[str, Dict[str, float]]) -> Optional[str]:
    """
    Map a single gaze point to the first matching ROI name.

    Args:
        x: X coordinate.
        y: Y coordinate.
        rois: Dictionary of ROI definitions.

    Returns:
        The name of the ROI if found, None if no ROI matches.
    """
    for roi_name, coords in rois.items():
        if is_point_in_roi(x, y, coords):
            return roi_name
    return None

def map_gaze_to_rois(df: pd.DataFrame, rois: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Add a 'roi_type' column to the gaze DataFrame based on (x, y) coordinates.

    Args:
        df: DataFrame containing 'x' and 'y' columns.
        rois: Dictionary of ROI definitions.

    Returns:
        DataFrame with an added 'roi_type' column.
    """
    if 'x' not in df.columns or 'y' not in df.columns:
        raise ValueError("Input DataFrame must contain 'x' and 'y' columns for ROI mapping.")

    df['roi_type'] = df.apply(
        lambda row: map_single_point_to_roi(row['x'], row['y'], rois),
        axis=1
    )
    
    # Log unmapped points
    unmapped_count = df['roi_type'].isna().sum()
    if unmapped_count > 0:
        logger.warning(f"ROI Mapping: {unmapped_count} gaze points fell outside all defined ROIs.")
    
    return df

def aggregate_fixation_roi_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate fixation durations per participant, headline, and ROI type.
    
    This function groups the preprocessed gaze data to calculate total fixation
    duration for each ROI type (e.g., 'source_attribution'). It ensures that
    combinations with zero fixations are represented with a duration of 0.

    Args:
        df: DataFrame with 'participant_id', 'headline_id', 'roi_type', and 'duration'.

    Returns:
        DataFrame with aggregated fixation durations per ROI.
    """
    if df.empty:
        return pd.DataFrame(columns=['participant_id', 'headline_id', 'roi_type', 'fixation_duration'])

    # Ensure necessary columns exist
    required_cols = ['participant_id', 'headline_id', 'roi_type', 'duration']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' for aggregation.")

    # Group and sum
    grouped = df.groupby(['participant_id', 'headline_id', 'roi_type'])['duration'].sum().reset_index()
    grouped.rename(columns={'duration': 'fixation_duration'}, inplace=True)

    # Ensure all expected ROI types exist for every participant/headline pair
    # This handles the requirement to treat zero fixations as valid data (duration=0)
    unique_participants = df['participant_id'].unique()
    unique_headlines = df['headline_id'].unique()
    unique_rois = df['roi_type'].dropna().unique()

    # Create a full cartesian product
    index = pd.MultiIndex.from_product(
        [unique_participants, unique_headlines, unique_rois],
        names=['participant_id', 'headline_id', 'roi_type']
    )
    
    full_df = pd.DataFrame(index=index).reset_index()
    
    # Merge with actual data
    result = full_df.merge(grouped, on=['participant_id', 'headline_id', 'roi_type'], how='left')
    
    # Fill NaN durations (which represent 0 fixations) with 0
    result['fixation_duration'] = result['fixation_duration'].fillna(0)

    return result

def handle_zero_fixation_roi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure rows exist for participant/headline combinations with zero fixations on specific ROIs.
    
    This is a wrapper around aggregate_fixation_roi_stats to ensure the output
    strictly adheres to the spec: zero fixations are recorded as duration=0, not missing.

    Args:
        df: Aggregated DataFrame.

    Returns:
        DataFrame with explicit 0.0 values for missing ROI interactions.
    """
    # The aggregation logic in aggregate_fixation_roi_stats already handles this via fillna(0).
    # This function exists for explicit API clarity as per task T017 requirements.
    return df

def main():
    """
    Entry point for testing ROI mapping logic directly.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        rois = load_roi_config()
        logger.info(f"Loaded ROI config: {list(rois.keys())}")
        
        # Create a dummy dataframe for testing
        test_data = {
            'participant_id': [1, 1, 1, 2],
            'headline_id': [101, 101, 102, 101],
            'x': [100.0, 500.0, 200.0, 100.0],
            'y': [100.0, 200.0, 300.0, 100.0],
            'duration': [50, 120, 80, 50]
        }
        df = pd.DataFrame(test_data)
        
        mapped_df = map_gaze_to_rois(df, rois)
        logger.info(f"Mapped ROI types: {mapped_df['roi_type'].tolist()}")
        
        aggregated = aggregate_fixation_roi_stats(mapped_df)
        logger.info(f"Aggregated stats:\n{aggregated}")
        
    except Exception as e:
        logger.error(f"ROI mapping execution failed: {e}")
        raise

if __name__ == "__main__":
    main()