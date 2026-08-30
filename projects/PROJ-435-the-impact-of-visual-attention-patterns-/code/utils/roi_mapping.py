import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from .config_loader import load_config

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def load_roi_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load ROI configuration from config.yaml."""
    if config_path is None:
        config_path = get_project_root() / "code" / "config.yaml"
    config = load_config(config_path)
    return config.get("roi_definitions", {})

def is_point_in_roi(
    x: float,
    y: float,
    roi_polygon: List[Tuple[float, float]]
) -> bool:
    """
    Check if a point is inside a polygon using ray casting algorithm.
    
    Args:
        x: X coordinate of the point
        y: Y coordinate of the point
        roi_polygon: List of (x, y) tuples defining the polygon vertices
        
    Returns:
        True if point is inside polygon, False otherwise
    """
    if len(roi_polygon) < 3:
        return False

    inside = False
    n = len(roi_polygon)
    p1x, p1y = roi_polygon[0]

    for i in range(1, n + 1):
        p2x, p2y = roi_polygon[i % n]
        
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        
        p1x, p1y = p2x, p2y

    return inside

def map_single_point_to_roi(
    x: float,
    y: float,
    roi_definitions: Dict[str, List[Tuple[float, float]]],
    default_roi: str = "unknown"
) -> str:
    """
    Map a single gaze point to an ROI.
    
    Args:
        x: X coordinate
        y: Y coordinate
        roi_definitions: Dictionary of ROI name -> polygon vertices
        default_roi: ROI name to return if point doesn't match any ROI
        
    Returns:
        ROI name string
    """
    for roi_name, polygon in roi_definitions.items():
        if is_point_in_roi(x, y, polygon):
            return roi_name
    return default_roi

def map_gaze_to_rois(
    gaze_data: pd.DataFrame,
    roi_definitions: Optional[Dict[str, List[Tuple[float, float]]]] = None,
    x_col: str = "x",
    y_col: str = "y",
    default_roi: str = "unknown"
) -> pd.DataFrame:
    """
    Map all gaze points in a DataFrame to ROIs.
    
    Args:
        gaze_data: DataFrame with gaze points
        roi_definitions: Dictionary of ROI name -> polygon vertices
        x_col: Name of x-coordinate column
        y_col: Name of y-coordinate column
        default_roi: ROI name for unmapped points
        
    Returns:
        DataFrame with added 'roi_type' column
    """
    if roi_definitions is None:
        roi_definitions = load_roi_config()

    if len(gaze_data) == 0:
        gaze_data["roi_type"] = default_roi
        return gaze_data

    # Vectorized approach for better performance
    def apply_roi_mapping(row):
        return map_single_point_to_roi(
            row[x_col],
            row[y_col],
            roi_definitions,
            default_roi
        )

    gaze_data = gaze_data.copy()
    gaze_data["roi_type"] = gaze_data.apply(apply_roi_mapping, axis=1)

    return gaze_data

def aggregate_fixation_roi_stats(
    fixation_data: pd.DataFrame,
    roi_col: str = "roi_type",
    duration_col: str = "duration"
) -> Dict[str, float]:
    """
    Aggregate fixation statistics by ROI.
    
    Args:
        fixation_data: DataFrame with fixations and ROI assignments
        roi_col: Name of ROI column
        duration_col: Name of duration column
        
    Returns:
        Dictionary mapping ROI names to total fixation duration
    """
    if len(fixation_data) == 0:
        return {}

    stats = {}
    for roi in fixation_data[roi_col].unique():
        roi_fixations = fixation_data[fixation_data[roi_col] == roi]
        stats[roi] = float(roi_fixations[duration_col].sum())

    return stats

def handle_zero_fixation_roi(
    gaze_data: pd.DataFrame,
    roi_definitions: Dict[str, List[Tuple[float, float]]],
    x_col: str = "x",
    y_col: str = "y"
) -> Dict[str, Any]:
    """
    Handle cases where a ROI has no gaze points.
    
    Args:
        gaze_data: DataFrame with gaze points
        roi_definitions: Dictionary of ROI definitions
        x_col: X coordinate column name
        y_col: Y coordinate column name
        
    Returns:
        Dictionary with statistics about ROI coverage
    """
    mapped_data = map_gaze_to_rois(gaze_data, roi_definitions, x_col, y_col)
    
    roi_coverage = {}
    for roi_name in roi_definitions.keys():
        count = (mapped_data["roi_type"] == roi_name).sum()
        roi_coverage[roi_name] = {
            "point_count": int(count),
            "has_fixations": count > 0
        }

    return roi_coverage

def main():
    """Main entry point for ROI mapping module."""
    logger.info("ROI mapping module loaded successfully")
    logger.info("Available functions: is_point_in_roi, map_single_point_to_roi, map_gaze_to_rois")

if __name__ == "__main__":
    main()
