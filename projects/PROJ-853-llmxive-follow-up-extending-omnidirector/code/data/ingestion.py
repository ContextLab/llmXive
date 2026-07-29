"""
Ingestion module for loading and filtering the OmniDirector dataset.
Handles dataset loading, schema validation, geometric filtering, and
coordinate parsing for grid frames.
"""
import os
import json
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, BinaryIO
import numpy as np
import pandas as pd

from config import get_path, get_config
from data.models import GridFrame

logger = logging.getLogger(__name__)

def ensure_output_directory(path: str) -> Path:
    """Ensure the directory for a given path exists."""
    dir_path = Path(path).parent
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def load_dataset_from_zip(zip_path: str) -> pd.DataFrame:
    """
    Load dataset from a zip file containing CSV data.
    
    Args:
        zip_path: Path to the zip file.
        
    Returns:
        DataFrame with dataset contents.
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Assume the zip contains a single CSV file or a specific structure
        csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
        if not csv_files:
            raise ValueError(f"No CSV files found in {zip_path}")
        
        # Load the first CSV found
        with zf.open(csv_files[0]) as f:
            df = pd.read_csv(f)
            logger.info(f"Loaded dataset with {len(df)} rows from {csv_files[0]}")
            return df

def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that DataFrame has required columns.
    
    Args:
        df: DataFrame to validate.
        required_columns: List of required column names.
        
    Returns:
        True if schema is valid.
        
    Raises:
        ValueError: If schema is invalid.
    """
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

def parse_grid_points_2d(grid_points_str: str) -> List[List[float]]:
    """Parse grid points from string representation."""
    if not grid_points_str or grid_points_str == "[]":
        return []
    return json.loads(grid_points_str)

def parse_matrix_column(matrix_str: str) -> np.ndarray:
    """Parse rotation matrix from string representation."""
    if not matrix_str or matrix_str == "[]":
        return np.eye(3)
    return np.array(json.loads(matrix_str))

def interpolate_missing_points(grid_points: List[List[float]]) -> List[List[float]]:
    """
    Interpolate missing grid points using linear interpolation.
    
    Args:
        grid_points: List of [x, y] points, potentially with None values.
        
    Returns:
        Interpolated list of points.
    """
    if not grid_points:
        return []
    
    # Simple linear interpolation for missing points
    interpolated = []
    for i, point in enumerate(grid_points):
        if point is None or len(point) == 0:
            # Use previous point if available, else next, else default
            if i > 0 and grid_points[i-1]:
                interpolated.append(grid_points[i-1])
            elif i < len(grid_points) - 1 and grid_points[i+1]:
                interpolated.append(grid_points[i+1])
            else:
                interpolated.append([0.0, 0.0])
        else:
            interpolated.append(point)
    
    return interpolated

def create_grid_frames(df: pd.DataFrame) -> List[GridFrame]:
    """
    Create GridFrame objects from DataFrame rows.
    
    Args:
        df: DataFrame with dataset rows.
        
    Returns:
        List of GridFrame objects.
    """
    grid_frames = []
    
    for _, row in df.iterrows():
        grid_points = parse_grid_points_2d(str(row['grid_points_2d']))
        R_matrix = parse_matrix_column(str(row['R_matrix']))
        t_vector = parse_matrix_column(str(row['t_vector'])) # Assuming same parse logic
        
        # Ensure t_vector is 1D
        if t_vector.ndim == 2:
            t_vector = t_vector.flatten()
        
        grid_frame = GridFrame(
            sequence_id=row['sequence_id'],
            frame_id=row['frame_id'],
            radial_motion_deg=row['radial_motion_deg'],
            z_velocity=row['z_velocity'],
            grid_points_2d=grid_points,
            R_matrix=R_matrix,
            t_vector=t_vector,
            randomized_depth=bool(row['randomized_depth'])
        )
        grid_frames.append(grid_frame)
    
    return grid_frames

def extract_grid_video_pairs(grid_frames: List[GridFrame]) -> Dict[str, List[GridFrame]]:
    """
    Group grid frames by sequence_id for video processing.
    
    Args:
        grid_frames: List of GridFrame objects.
        
    Returns:
        Dictionary mapping sequence_id to list of GridFrames.
    """
    pairs = {}
    for frame in grid_frames:
        if frame.sequence_id not in pairs:
            pairs[frame.sequence_id] = []
        pairs[frame.sequence_id].append(frame)
    return pairs

def apply_geometric_filter(
    df: pd.DataFrame,
    radial_threshold: float = 15.0,
    z_velocity_threshold: float = 0.1
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply geometric filtering heuristics to the dataset.
    Retains sequences where radial_motion > 15° OR z_velocity > 0.1.
    
    Args:
        df: Input DataFrame.
        radial_threshold: Threshold for radial motion in degrees.
        z_velocity_threshold: Threshold for Z-axis velocity.
        
    Returns:
        Tuple of (retained_df, excluded_df).
    """
    # Filter: radial_motion_deg > 15 OR z_velocity > 0.1
    mask = (df['radial_motion_deg'] > radial_threshold) | (df['z_velocity'] > z_velocity_threshold)
    retained = df[mask].copy()
    excluded = df[~mask].copy()
    
    logger.info(f"Geometric filter: {len(retained)} retained, {len(excluded)} excluded")
    return retained, excluded

def load_and_extract_dataset(
    zip_path: Optional[str] = None,
    filter_data: bool = True
) -> pd.DataFrame:
    """
    Main pipeline function to load, validate, and filter the dataset.
    
    Args:
        zip_path: Path to the dataset zip file.
        filter_data: Whether to apply geometric filtering.
        
    Returns:
        Filtered DataFrame ready for output.
    """
    if zip_path is None:
        zip_path = get_path('omnidirector_raw_zip')
    
    # Load dataset
    df = load_dataset_from_zip(zip_path)
    
    # Validate schema
    required_cols = ['sequence_id', 'frame_id', 'radial_motion_deg', 'z_velocity', 
                    'grid_points_2d', 'R_matrix', 't_vector', 'randomized_depth']
    validate_schema(df, required_cols)
    
    # Apply geometric filter if requested
    if filter_data:
        retained, _ = apply_geometric_filter(df)
        return retained
    
    return df

def main():
    """
    Main entry point for dataset ingestion.
    Loads data, applies filters, and prepares for output.
    """
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    
    zip_path = get_path('omnidirector_raw_zip')
    if not os.path.exists(zip_path):
        logger.error(f"Dataset not found at {zip_path}")
        return None
    
    df = load_and_extract_dataset(zip_path, filter_data=True)
    logger.info(f"Final dataset size: {len(df)} rows")
    return df

if __name__ == "__main__":
    main()
