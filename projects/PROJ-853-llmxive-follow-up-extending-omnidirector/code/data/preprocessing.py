"""
Preprocessing module for extracting grid frames and pairing ground truth.
Handles conversion from dataframe to GridFrame objects and CSV output.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd

from config import get_path, get_config
from data.models import GridFrame
from data.writer import write_filtered_dataset, serialize_grid_points, serialize_matrix, serialize_vector

logger = logging.getLogger(__name__)

def parse_grid_points_2d(grid_points_str: str) -> List[List[float]]:
    """
    Parse grid points from string representation back to list of lists.
    
    Args:
        grid_points_str: JSON string of grid points.
        
    Returns:
        List of [x, y] coordinate pairs.
    """
    if not grid_points_str or grid_points_str == "[]":
        return []
    return json.loads(grid_points_str)

def parse_matrix_column(matrix_str: str) -> np.ndarray:
    """
    Parse rotation matrix from string representation.
    
    Args:
        matrix_str: JSON string of 3x3 matrix.
        
    Returns:
        3x3 numpy array.
    """
    if not matrix_str or matrix_str == "[]":
        return np.eye(3)
    return np.array(json.loads(matrix_str))

def parse_vector_column(vector_str: str) -> np.ndarray:
    """
    Parse translation vector from string representation.
    
    Args:
        vector_str: JSON string of 3-element vector.
        
    Returns:
        3-element numpy array.
    """
    if not vector_str or vector_str == "[]":
        return np.zeros(3)
    return np.array(json.loads(vector_str))

def extract_grid_frames_from_dataframe(df: pd.DataFrame) -> List[GridFrame]:
    """
    Convert a pandas DataFrame to a list of GridFrame objects.
    
    Args:
        df: DataFrame with columns matching the filtered dataset schema.
        
    Returns:
        List of GridFrame objects.
    """
    grid_frames = []
    
    for _, row in df.iterrows():
        grid_points = parse_grid_points_2d(str(row['grid_points_2d']))
        R_matrix = parse_matrix_column(str(row['R_matrix']))
        t_vector = parse_vector_column(str(row['t_vector']))
        
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

def pair_ground_truth(grid_frames: List[GridFrame]) -> List[GridFrame]:
    """
    Ensure ground truth is properly paired with grid frames.
    This function validates that R_matrix and t_vector are valid.
    
    Args:
        grid_frames: List of GridFrame objects.
        
    Returns:
        Validated list of GridFrame objects.
    """
    validated_frames = []
    
    for frame in grid_frames:
        # Validate rotation matrix (should be 3x3)
        if frame.R_matrix.shape != (3, 3):
            logger.warning(f"Invalid R_matrix shape for frame {frame.frame_id}: {frame.R_matrix.shape}")
            frame.R_matrix = np.eye(3)
        
        # Validate translation vector (should be 3x1 or 1x3)
        if frame.t_vector.shape not in [(3,), (3, 1)]:
            logger.warning(f"Invalid t_vector shape for frame {frame.frame_id}: {frame.t_vector.shape}")
            frame.t_vector = np.zeros(3)
        
        # Flatten t_vector if needed
        if frame.t_vector.ndim == 2:
            frame.t_vector = frame.t_vector.flatten()
        
        validated_frames.append(frame)
    
    return validated_frames

def save_grid_frames_to_csv(
    grid_frames: List[GridFrame],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save grid frames to CSV file with checksums.
    
    Args:
        grid_frames: List of GridFrame objects to save.
        output_path: Optional path override. Uses config default if not provided.
        
    Returns:
        Dictionary with output path, row count, and checksum.
    """
    if output_path is None:
        output_path = get_path('filtered_sequences_csv')
    
    logger.info(f"Saving {len(grid_frames)} grid frames to {output_path}")
    
    result = write_filtered_dataset(grid_frames, output_path)
    return result

def main():
    """
    Main entry point for preprocessing and writing filtered dataset.
    Reads from intermediate data, validates, and writes final CSV.
    """
    from config import get_config
    config = get_config()
    
    # In a real pipeline, data would come from previous steps
    # For this implementation, we assume the ingestion step has already
    # produced a filtered dataset in memory or intermediate storage
    
    # This main function is a placeholder that demonstrates the module's
    # capability to write the final filtered_sequences.csv
    logger.info("Preprocessing module ready to write filtered dataset")
    return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
