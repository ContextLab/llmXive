"""
ROI Mapping Module for Eye-Tracking Data.

Implements point-in-polygon algorithms to assign gaze coordinates to
defined Regions of Interest (ROIs) such as 'source_attribution' and 'headline_body'.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Configure logger
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Determine the project root directory (assumes code/utils/roi_mapping.py structure)."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent

def load_roi_config() -> Dict[str, Any]:
    """
    Load ROI bounding box definitions from the project configuration.

    Expects a 'rois' section in config.yaml or a dedicated roi_config.json
    containing polygon coordinates for each ROI.

    Returns:
        Dict mapping ROI names to their polygon coordinates (list of (x, y) tuples).
    """
    project_root = get_project_root()
    config_path = project_root / "code" / "roi_config.json"

    if not config_path.exists():
        # Fallback to default definitions if file is missing, but log a warning
        logger.warning(f"ROI config file not found at {config_path}. Using default definitions.")
        return {
            "source_attribution": [(0.0, 0.0), (0.2, 0.0), (0.2, 0.15), (0.0, 0.15)],
            "headline_body": [(0.0, 0.15), (1.0, 0.15), (1.0, 0.4), (0.0, 0.4)]
        }

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get("rois", {})
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load ROI config: {e}")
        raise

def is_point_in_roi(point: Tuple[float, float], roi_polygon: List[Tuple[float, float]]) -> bool:
    """
    Determine if a 2D point lies inside a polygon using the Ray Casting algorithm.

    Args:
        point: (x, y) coordinates of the gaze point.
        roi_polygon: List of (x, y) vertices defining the ROI polygon.

    Returns:
        True if the point is inside the polygon, False otherwise.
    """
    x, y = point
    inside = False
    n = len(roi_polygon)
    if n < 3:
        return False

    p1x, p1y = roi_polygon[0]
    for i in range(n + 1):
        p2x, p2y = roi_polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not p1x, p2x
        p1x, p1y = p2x, p2y

    return inside

def map_single_point_to_roi(point: Tuple[float, float], rois: Dict[str, List[Tuple[float, float]]]) -> Optional[str]:
    """
    Map a single gaze point to the first matching ROI.

    Args:
        point: (x, y) gaze coordinates.
        rois: Dictionary of ROI definitions.

    Returns:
        The name of the ROI containing the point, or None if no match.
    """
    for roi_name, polygon in rois.items():
        if is_point_in_roi(point, polygon):
            return roi_name
    return None

def map_gaze_to_rois(df: pd.DataFrame, rois: Optional[Dict[str, List[Tuple[float, float]]]] = None) -> pd.DataFrame:
    """
    Assign ROI types to a DataFrame of gaze points.

    Adds a 'roi_type' column to the input DataFrame.

    Args:
        df: DataFrame containing 'x' and 'y' columns for gaze coordinates.
        rois: Optional dictionary of ROI definitions. If None, loads from config.

    Returns:
        DataFrame with an added 'roi_type' column.
    """
    if rois is None:
        rois = load_roi_config()

    if 'x' not in df.columns or 'y' not in df.columns:
        raise ValueError("Input DataFrame must contain 'x' and 'y' columns for ROI mapping.")

    logger.info(f"Mapping {len(df)} gaze points to {len(rois)} ROIs...")

    # Vectorized approach might be faster for huge datasets, but point-in-polygon
    # is complex to vectorize without shapely. For standard pandas, apply is robust.
    # We assume coordinates are normalized 0.0-1.0 or match the config scale.

    def apply_mapping(row):
        return map_single_point_to_roi((row['x'], row['y']), rois)

    df['roi_type'] = df.apply(apply_mapping, axis=1)
    
    # Log statistics
    roi_counts = df['roi_type'].value_counts()
    logger.info(f"ROI mapping complete. Distribution:\n{roi_counts}")
    
    return df

def aggregate_fixation_roi_stats(fixations_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Aggregate statistics for fixations mapped to ROIs.

    Args:
        fixations_df: DataFrame with fixation data including 'roi_type'.

    Returns:
        Dictionary with counts and durations per ROI.
    """
    if 'roi_type' not in fixations_df.columns:
        raise ValueError("DataFrame must contain 'roi_type' column.")

    stats = {}
    for roi in fixations_df['roi_type'].dropna().unique():
        subset = fixations_df[fixations_df['roi_type'] == roi]
        stats[roi] = {
            "count": len(subset),
            "total_duration_ms": subset.get('duration', pd.Series([0])).sum(),
            "avg_duration_ms": subset.get('duration', pd.Series([0])).mean()
        }
    return stats

def handle_zero_fixation_roi(df: pd.DataFrame, target_roi: str = "source_attribution") -> pd.DataFrame:
    """
    Ensure trials with zero fixations on the target ROI are represented with duration 0.

    This function identifies (participant_id, headline_id) pairs that exist in the data
    but have no rows where roi_type == target_roi, and inserts a placeholder row
    with duration 0 for that ROI.

    Args:
        df: Preprocessed gaze/fixation DataFrame.
        target_roi: The ROI name to check for zero fixations.

    Returns:
        DataFrame with zero-duration rows inserted where missing.
    """
    if 'participant_id' not in df.columns or 'headline_id' not in df.columns:
        logger.warning("Cannot handle zero fixations: missing participant_id or headline_id columns.")
        return df

    # Identify all unique combinations
    all_combinations = df[['participant_id', 'headline_id']].drop_duplicates()
    
    # Filter for existing target_roi fixations
    existing_target = df[df['roi_type'] == target_roi][['participant_id', 'headline_id']].drop_duplicates()
    
    # Find missing combinations
    missing = all_combinations.merge(existing_target, on=['participant_id', 'headline_id'], how='left', indicator=True)
    missing = missing[missing['_merge'] == 'left_only'][['participant_id', 'headline_id']]
    
    if len(missing) == 0:
        logger.info("No missing target ROI fixations found.")
        return df

    # Create placeholder rows
    placeholders = missing.copy()
    placeholders['roi_type'] = target_roi
    placeholders['duration'] = 0
    # Preserve other necessary columns if they exist, set to NaN or 0
    for col in df.columns:
        if col not in placeholders.columns:
            placeholders[col] = 0 if df[col].dtype in [np.int64, np.float64] else None
    
    logger.info(f"Inserting {len(placeholders)} zero-duration rows for missing {target_roi} ROI.")
    return pd.concat([df, placeholders], ignore_index=True)

def main():
    """Main entry point for testing ROI mapping logic."""
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    rois = load_roi_config()
    logger.info(f"Loaded ROI definitions: {list(rois.keys())}")
    
    # Create dummy data
    data = {
        'x': [0.1, 0.5, 0.8, 0.05],
        'y': [0.05, 0.2, 0.5, 0.1],
        'participant_id': [1, 1, 1, 1],
        'headline_id': [101, 101, 101, 101]
    }
    df = pd.DataFrame(data)
    
    # Map ROIs
    result = map_gaze_to_rois(df, rois)
    print(result[['x', 'y', 'roi_type']])
    
    # Test zero fixation handling
    # Simulate a case where one combo is missing the target ROI
    result = handle_zero_fixation_roi(result, "source_attribution")
    print("After zero-fixation handling:")
    print(result[['participant_id', 'headline_id', 'roi_type', 'duration']])

if __name__ == "__main__":
    main()