"""
ROI Mapping utilities for visual attention analysis.

This module provides functions to map gaze points to Regions of Interest (ROIs)
based on bounding box coordinates defined in the configuration.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from utils.logging_config import get_quality_logger, get_pipeline_logger

# Logger instances
quality_logger = get_quality_logger()
pipeline_logger = get_pipeline_logger()


def load_roi_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load ROI configuration from YAML file.

    Args:
        config_path: Path to the configuration file. If None, uses default path.

    Returns:
        Dictionary containing ROI bounding box definitions and parameters.
    """
    if config_path is None:
        config_path = Path("code/config.yaml")

    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        roi_config = config.get('roi_mapping', {})
        
        # Validate required keys
        if 'bounding_boxes' not in roi_config:
            raise ValueError("ROI config missing 'bounding_boxes' key")
        
        return roi_config
        
    except FileNotFoundError:
        pipeline_logger.warning(f"ROI config file not found at {config_path}, using defaults")
        return _get_default_roi_config()
    except Exception as e:
        pipeline_logger.error(f"Error loading ROI config: {e}")
        return _get_default_roi_config()


def _get_default_roi_config() -> Dict[str, Any]:
    """
    Return default ROI configuration if config file is missing or invalid.
    
    Returns:
        Default ROI configuration dictionary.
    """
    return {
        'bounding_boxes': {
            'source_attribution': {
                'x_min': 0,
                'y_min': 0,
                'x_max': 100,
                'y_max': 50
            },
            'headline': {
                'x_min': 0,
                'y_min': 50,
                'x_max': 100,
                'y_max': 100
            },
            'body_text': {
                'x_min': 100,
                'y_min': 0,
                'x_max': 200,
                'y_max': 100
            },
            'other': {
                'x_min': 200,
                'y_min': 0,
                'x_max': 300,
                'y_max': 100
            }
        },
        'coordinate_system': 'normalized',
        'default_roi': 'other'
    }


def map_single_point_to_roi(
    x: float, 
    y: float, 
    roi_config: Dict[str, Any]
) -> str:
    """
    Map a single gaze point to an ROI based on bounding box coordinates.
    
    Args:
        x: X coordinate of the gaze point.
        y: Y coordinate of the gaze point.
        roi_config: ROI configuration dictionary with bounding boxes.
        
    Returns:
        String identifier of the ROI the point falls into, or 'other' if no match.
    """
    bounding_boxes = roi_config.get('bounding_boxes', {})
    default_roi = roi_config.get('default_roi', 'other')
    
    # Check each ROI in priority order
    for roi_name, box in bounding_boxes.items():
        x_min = box.get('x_min', 0)
        y_min = box.get('y_min', 0)
        x_max = box.get('x_max', 100)
        y_max = box.get('y_max', 100)
        
        if x_min <= x <= x_max and y_min <= y <= y_max:
            return roi_name
    
    return default_roi


def map_gaze_to_rois(
    gaze_data: pd.DataFrame, 
    roi_config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Map all gaze points in a DataFrame to their corresponding ROIs.
    
    Args:
        gaze_data: DataFrame containing gaze tracking data with 'x' and 'y' columns.
        roi_config: Optional ROI configuration. If None, loads from config file.
        
    Returns:
        DataFrame with an added 'roi_type' column indicating the mapped ROI for each point.
        
    Raises:
        ValueError: If required columns are missing from the input DataFrame.
    """
    if roi_config is None:
        roi_config = load_roi_config()
    
    # Validate required columns
    required_cols = ['x', 'y']
    missing_cols = [col for col in required_cols if col not in gaze_data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for ROI mapping: {missing_cols}")
    
    # Map each point to an ROI
    gaze_data['roi_type'] = gaze_data.apply(
        lambda row: map_single_point_to_roi(row['x'], row['y'], roi_config),
        axis=1
    )
    
    # Log mapping statistics
    roi_counts = gaze_data['roi_type'].value_counts()
    pipeline_logger.info(f"ROI mapping complete. Distribution: {roi_counts.to_dict()}")
    
    return gaze_data


def aggregate_fixation_roi_stats(
    fixation_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Aggregate fixation data by ROI, calculating total duration and count per ROI.
    
    Args:
        fixation_data: DataFrame with fixation events including 'roi_type' and 'duration'.
        
    Returns:
        DataFrame with aggregated statistics per ROI.
    """
    if 'roi_type' not in fixation_data.columns or 'duration' not in fixation_data.columns:
        raise ValueError("Fixation data must contain 'roi_type' and 'duration' columns")
    
    aggregated = fixation_data.groupby('roi_type').agg(
        fixation_count=('roi_type', 'count'),
        total_duration=('duration', 'sum'),
        mean_duration=('duration', 'mean')
    ).reset_index()
    
    pipeline_logger.info(f"Aggregated ROI stats for {len(aggregated)} ROIs")
    return aggregated


def handle_zero_fixation_roi(
    fixation_data: pd.DataFrame,
    roi_config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Handle cases where a participant has zero fixations on a specific ROI.
    
    This function ensures that all defined ROIs are present in the output,
    even if no fixations were recorded for them (duration=0).
    
    Args:
        fixation_data: DataFrame with aggregated fixation data per ROI.
        roi_config: ROI configuration containing all defined bounding boxes.
        
    Returns:
        DataFrame with all ROIs represented, filling missing ones with zero values.
    """
    # Get all defined ROIs from config
    defined_rois = set(roi_config.get('bounding_boxes', {}).keys())
    present_rois = set(fixation_data['roi_type'].unique())
    
    missing_rois = defined_rois - present_rois
    
    if missing_rois:
        quality_logger.warning(f"Missing ROIs with zero fixations: {missing_rois}")
        
        # Create rows for missing ROIs with zero values
        zero_rows = []
        for roi in missing_rois:
            zero_rows.append({
                'roi_type': roi,
                'fixation_count': 0,
                'total_duration': 0.0,
                'mean_duration': 0.0
            })
        
        # Append missing rows
        if zero_rows:
            missing_df = pd.DataFrame(zero_rows)
            fixation_data = pd.concat([fixation_data, missing_df], ignore_index=True)
    
    return fixation_data


def main():
    """
    Main function to demonstrate ROI mapping functionality.
    This is primarily used for testing and validation.
    """
    pipeline_logger.info("Starting ROI mapping demonstration")
    
    # Load sample data
    sample_data = pd.DataFrame({
        'x': [10.0, 50.0, 150.0, 250.0, 5.0],
        'y': [25.0, 75.0, 50.0, 50.0, 5.0],
        'participant_id': ['P001', 'P001', 'P001', 'P001', 'P002'],
        'timestamp': [100, 150, 200, 250, 300]
    })
    
    # Load config
    roi_config = load_roi_config()
    
    # Map gaze to ROIs
    mapped_data = map_gaze_to_rois(sample_data, roi_config)
    
    print("Sample ROI Mapping Results:")
    print(mapped_data[['x', 'y', 'roi_type']])
    
    # Aggregate statistics
    aggregated = aggregate_fixation_roi_stats(mapped_data)
    print("\nAggregated ROI Statistics:")
    print(aggregated)
    
    pipeline_logger.info("ROI mapping demonstration complete")


if __name__ == "__main__":
    main()