import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from utils.logging_config import get_quality_logger, get_pipeline_logger

logger = get_pipeline_logger(__name__)
quality_logger = get_quality_logger(__name__)

def load_roi_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load ROI configuration from a YAML file or return defaults.
    Defaults define bounding boxes for 'source', 'headline', and 'other'.
    """
    defaults = {
        "source": {"x_min": 0, "y_min": 0, "x_max": 100, "y_max": 100},
        "headline": {"x_min": 0, "y_min": 100, "x_max": 100, "y_max": 150},
        "other": {"x_min": 0, "y_min": 0, "x_max": 100, "y_max": 100}
    }
    # In a real implementation, load from config_path if provided
    return defaults

def map_single_point_to_roi(x: float, y: float, roi_config: Dict[str, Dict]) -> str:
    """
    Map a single gaze coordinate (x, y) to a specific ROI string.
    Returns 'source', 'headline', 'other', or 'unknown' if no match.
    """
    for roi_name, bounds in roi_config.items():
        if (bounds["x_min"] <= x <= bounds["x_max"] and
            bounds["y_min"] <= y <= bounds["y_max"]):
            return roi_name
    return "unknown"

def map_gaze_to_rois(df: pd.DataFrame, roi_config: Dict[str, Dict]) -> pd.DataFrame:
    """
    Apply ROI mapping to a DataFrame of gaze points.
    Adds a 'roi_type' column.
    """
    df = df.copy()
    df['roi_type'] = df.apply(
        lambda row: map_single_point_to_roi(row['x'], row['y'], roi_config),
        axis=1
    )
    return df

def aggregate_fixation_roi_stats(df: pd.DataFrame, fixation_col: str = 'fixation_id') -> pd.DataFrame:
    """
    Aggregate gaze data into fixation-level statistics per ROI.
    Calculates total duration per fixation and ROI.
    """
    if df.empty:
        return pd.DataFrame(columns=['fixation_id', 'roi_type', 'duration', 'count'])

    # Ensure necessary columns exist
    required_cols = ['fixation_id', 'roi_type', 'duration']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for aggregation: {missing}")

    agg_df = df.groupby(['fixation_id', 'roi_type']).agg(
        duration=('duration', 'sum'),
        count=('duration', 'count')
    ).reset_index()
    return agg_df

def handle_zero_fixation_roi(df: pd.DataFrame, source_roi: str = 'source') -> pd.DataFrame:
    """
    Handle edge cases where a participant has zero fixations on a specific ROI (e.g., 'source').
    
    Constraint: Treat zero fixations as valid data (duration=0) rather than missing.
    
    Logic:
    1. Identify unique (participant_id, headline_id) pairs in the input data.
    2. Identify all unique ROIs present in the data for those pairs.
    3. Create a complete grid of all combinations of (participant_id, headline_id, roi_type).
    4. Merge the aggregated data onto this grid.
    5. Fill NaN values in duration/count for the source ROI (and others) with 0.
    
    This ensures that if a participant looked at a headline but never the source,
    the record exists with duration=0, preventing data loss in downstream joins.
    """
    if df.empty:
        quality_logger.warning("Input DataFrame is empty in handle_zero_fixation_roi. Returning empty frame.")
        return df

    # Ensure we have participant and headline context if not already aggregated at that level
    # Assuming the input 'df' here is already aggregated at fixation level or needs to be
    # If the input is raw gaze points, we must aggregate first.
    # For this function, we assume input is already aggregated or raw gaze points that need
    # to be converted to a 'duration per ROI' view.
    
    # If 'fixation_id' is present, we assume we are working with fixations.
    # We need to group by participant and headline to ensure we capture the "zero" case.
    # Let's assume the input df has 'participant_id', 'headline_id', 'roi_type', 'duration'.
    
    # If the input is raw gaze points (no fixation_id), we must group by participant, headline, roi
    if 'fixation_id' not in df.columns:
        if 'participant_id' not in df.columns or 'headline_id' not in df.columns:
            raise ValueError("Input DataFrame must contain 'participant_id' and 'headline_id' if 'fixation_id' is missing.")
        # Aggregate raw gaze to ROI level per participant/headline
        agg_df = df.groupby(['participant_id', 'headline_id', 'roi_type']).agg(
            duration=('duration', 'sum'),
            count=('count', 'sum')
        ).reset_index()
    else:
        # If we have fixations, we need to aggregate fixations to ROI level per participant/headline
        # First ensure we have participant/headline in the fixation df (usually they are)
        if 'participant_id' not in df.columns or 'headline_id' not in df.columns:
            raise ValueError("Fixation DataFrame must contain 'participant_id' and 'headline_id'.")
        
        agg_df = df.groupby(['participant_id', 'headline_id', 'roi_type']).agg(
            duration=('duration', 'sum'),
            count=('count', 'sum')
        ).reset_index()

    # Get all unique participant/headline combinations
    if 'participant_id' not in agg_df.columns or 'headline_id' not in agg_df.columns:
         # If the input was already aggregated at a higher level (e.g. just participant/headline/roi)
         # but we need to ensure we cover all pairs.
         # This logic assumes agg_df has the necessary keys.
         pass

    # Create a complete grid of all (participant_id, headline_id, roi_type) combinations found in the data
    # We assume the set of ROIs is consistent or we want to cover all seen ROIs
    unique_participants = agg_df['participant_id'].unique()
    unique_headlines = agg_df['headline_id'].unique()
    unique_rois = agg_df['roi_type'].unique()

    # Create MultiIndex for the full grid
    full_grid = pd.MultiIndex.from_product(
        [unique_participants, unique_headlines, unique_rois],
        names=['participant_id', 'headline_id', 'roi_type']
    )
    
    full_df = pd.DataFrame(index=full_grid).reset_index()
    
    # Merge with actual data
    result = full_df.merge(
        agg_df,
        on=['participant_id', 'headline_id', 'roi_type'],
        how='left'
    )
    
    # Fill NaN with 0 for duration and count (representing zero fixations)
    result['duration'] = result['duration'].fillna(0)
    result['count'] = result['count'].fillna(0)
    
    # Convert to integer for count if it was float due to NaN fill
    result['count'] = result['count'].astype(int)
    
    logger.info(f"Handled zero fixations. Expanded grid from {len(agg_df)} rows to {len(result)} rows.")
    return result

def main():
    """
    Main entry point for testing ROI mapping and zero-fixation handling.
    """
    # Example usage
    config = load_roi_config()
    logger.info("ROI Mapping utility loaded.")
    logger.info(f"Default ROI Config: {config}")
