"""
ROI Mapping Utilities for Visual Attention Analysis.

This module provides logic to assign gaze points and fixations to
Regions of Interest (ROIs) such as 'source_attribution', 'headline',
and 'body_text'. It handles coordinate mapping, edge case exclusion,
and zero-duration valid cases.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from utils.logging_config import get_quality_logger, get_pipeline_logger

# Initialize loggers
pipeline_logger = get_pipeline_logger("roi_mapping")
quality_logger = get_quality_logger("roi_mapping")

# Default ROI definitions (normalized coordinates 0-1)
DEFAULT_ROIS = {
    "source_attribution": {"x_min": 0.0, "x_max": 0.2, "y_min": 0.0, "y_max": 0.15},
    "headline": {"x_min": 0.0, "x_max": 1.0, "y_min": 0.15, "y_max": 0.30},
    "body_text": {"x_min": 0.0, "x_max": 1.0, "y_min": 0.30, "y_max": 1.0},
}

def load_roi_config(config_path: Optional[Path] = None) -> Dict[str, Dict[str, float]]:
    """
    Load ROI bounding box configurations.
    Falls back to DEFAULT_ROIS if config file is missing or invalid.
    """
    if config_path and config_path.exists():
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'rois' in config:
                    pipeline_logger.info(f"Loaded ROI configuration from {config_path}")
                    return config['rois']
        except Exception as e:
            quality_logger.warning(f"Failed to load ROI config from {config_path}: {e}. Using defaults.")
    
    pipeline_logger.info("Using default ROI configuration.")
    return DEFAULT_ROIS

def map_single_point_to_roi(
    x: float, 
    y: float, 
    rois: Dict[str, Dict[str, float]]
) -> Optional[str]:
    """
    Determine which ROI a single gaze point (x, y) falls into.
    
    Args:
        x: Normalized x-coordinate (0.0 to 1.0)
        y: Normalized y-coordinate (0.0 to 1.0)
        rois: Dictionary of ROI definitions with min/max bounds
        
    Returns:
        The ROI name if found, None if outside all defined ROIs.
    """
    for roi_name, bounds in rois.items():
        if (bounds['x_min'] <= x <= bounds['x_max'] and 
            bounds['y_min'] <= y <= bounds['y_max']):
            return roi_name
    return None

def map_gaze_to_rois(
    df: pd.DataFrame, 
    rois: Optional[Dict[str, Dict[str, float]]] = None,
    x_col: str = 'x',
    y_col: str = 'y',
    roi_col: str = 'roi_assigned'
) -> Tuple[pd.DataFrame, int]:
    """
    Assign ROI labels to a DataFrame of gaze events or fixations.
    
    This function processes the gaze data, assigning each point to a
    specific ROI based on its coordinates. It logs exclusions for
    points falling outside all defined ROIs.
    
    Args:
        df: DataFrame containing gaze/fixation data with x, y columns.
        rois: Dictionary of ROI bounding boxes. If None, uses defaults.
        x_col: Name of the x-coordinate column.
        y_col: Name of the y-coordinate column.
        roi_col: Name of the column to store the assigned ROI.
        
    Returns:
        Tuple of (updated DataFrame, count of excluded points)
    """
    if rois is None:
        rois = DEFAULT_ROIS
    
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Missing required columns for ROI mapping: {x_col}, {y_col}")
    
    # Initialize ROI column with None
    df[roi_col] = None
    
    # Vectorized mapping for performance
    # Create a mask for points within each ROI
    exclusion_count = 0
    valid_indices = []
    
    for roi_name, bounds in rois.items():
        mask = (
            (df[x_col] >= bounds['x_min']) & 
            (df[x_col] <= bounds['x_max']) &
            (df[y_col] >= bounds['y_min']) & 
            (df[y_col] <= bounds['y_max'])
        )
        df.loc[mask, roi_col] = roi_name
        valid_indices.extend(df[mask].index.tolist())
    
    # Identify points not assigned to any ROI
    unassigned_mask = df[roi_col].isna()
    unassigned_count = unassigned_mask.sum()
    
    if unassigned_count > 0:
        exclusion_count = int(unassigned_count)
        quality_logger.warning(
            f"Excluded {exclusion_count} gaze points that fell outside all defined ROIs."
        )
        # Log sample of excluded points for debugging
        sample_excluded = df[unassigned_mask].head(5)
        quality_logger.debug(f"Sample excluded points:\n{sample_excluded[[x_col, y_col]].to_string()}")
    
    pipeline_logger.info(f"ROI mapping complete. Assigned {len(valid_indices)} points, excluded {exclusion_count}.")
    
    return df, exclusion_count

def aggregate_fixation_roi_stats(
    df: pd.DataFrame, 
    roi_col: str = 'roi_assigned',
    duration_col: str = 'duration',
    participant_col: str = 'participant_id',
    stimulus_col: str = 'stimulus_id'
) -> pd.DataFrame:
    """
    Aggregate fixation duration statistics by ROI, participant, and stimulus.
    
    Args:
        df: DataFrame with mapped ROIs and fixation durations.
        roi_col: Column name for assigned ROI.
        duration_col: Column name for fixation duration (ms).
        participant_col: Column name for participant ID.
        stimulus_col: Column name for stimulus ID.
        
    Returns:
        DataFrame with aggregated stats per participant/stimulus/ROI.
    """
    if roi_col not in df.columns:
        raise ValueError(f"ROI column '{roi_col}' not found in data. Run map_gaze_to_rois first.")
    
    # Filter out unassigned ROIs (None)
    df_valid = df[df[roi_col].notna()].copy()
    
    if df_valid.empty:
        pipeline_logger.warning("No valid ROI data found for aggregation.")
        return pd.DataFrame()
    
    # Aggregate
    agg_df = df_valid.groupby([participant_col, stimulus_col, roi_col]).agg(
        total_duration=(duration_col, 'sum'),
        fixation_count=(duration_col, 'count'),
        avg_duration=(duration_col, 'mean')
    ).reset_index()
    
    return agg_df

def handle_zero_fixation_roi(
    df: pd.DataFrame, 
    roi_col: str = 'roi_assigned',
    duration_col: str = 'duration'
) -> pd.DataFrame:
    """
    Ensure trials with zero fixations on a specific ROI are handled as valid data.
    
    According to task requirements, zero fixations on the source ROI should
    be treated as valid data (duration=0) rather than missing data.
    This function ensures that all expected ROIs are represented for every
    participant-stimulus pair, filling missing combinations with zero duration.
    
    Args:
        df: Aggregated fixation data.
        roi_col: Column name for ROI.
        duration_col: Column name for duration.
        
    Returns:
        DataFrame with zero-filled rows for missing ROI combinations.
    """
    if df.empty:
        return df
    
    # Get unique participants and stimuli
    participants = df['participant_id'].unique()
    stimuli = df['stimulus_id'].unique()
    rois = df[roi_col].unique()
    
    # Create a complete grid of combinations
    complete_grid = pd.MultiIndex.from_product(
        [participants, stimuli, rois],
        names=['participant_id', 'stimulus_id', roi_col]
    )
    
    # Reindex to include missing combinations
    df_complete = df.set_index(['participant_id', 'stimulus_id', roi_col]).reindex(complete_grid)
    
    # Fill missing duration values with 0
    df_complete = df_complete.reset_index()
    df_complete[duration_col] = df_complete[duration_col].fillna(0)
    df_complete['fixation_count'] = df_complete['fixation_count'].fillna(0).astype(int)
    df_complete['avg_duration'] = df_complete['avg_duration'].fillna(0)
    
    pipeline_logger.info(f"Handled zero-fixation cases. Total rows: {len(df_complete)}")
    
    return df_complete

def main():
    """
    Main entry point for ROI mapping utility testing/demo.
    In a real pipeline, this would be called by 01_ingest_and_preprocess.py
    """
    pipeline_logger.info("ROI Mapping Utility initialized.")
    pipeline_logger.info("This module is designed to be imported by preprocessing scripts.")
    pipeline_logger.info("To use: from utils.roi_mapping import map_gaze_to_rois, aggregate_fixation_roi_stats")

if __name__ == "__main__":
    main()
