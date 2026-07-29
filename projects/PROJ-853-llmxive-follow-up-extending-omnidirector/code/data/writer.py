"""
Writer module for serializing and writing filtered dataset to CSV.
Handles serialization of complex types (lists, matrices) and checksum calculation.
"""
import os
import json
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import numpy as np

from config import get_path, ensure_paths_exist
from data.models import GridFrame

logger = logging.getLogger(__name__)

def serialize_grid_points(grid_points: List[List[float]]) -> str:
    """
    Serialize a list of 2D grid points to a JSON string.
    
    Args:
        grid_points: List of [x, y] coordinate pairs.
        
    Returns:
        JSON string representation of the grid points.
    """
    if grid_points is None:
        return "[]"
    return json.dumps(grid_points)

def serialize_matrix(matrix: Union[np.ndarray, List[List[float]]]) -> str:
    """
    Serialize a 3x3 rotation matrix to a JSON string.
    
    Args:
        matrix: 3x3 numpy array or list of lists.
        
    Returns:
        JSON string representation of the matrix.
    """
    if isinstance(matrix, np.ndarray):
        matrix = matrix.tolist()
    if matrix is None:
        return "[]"
    return json.dumps(matrix)

def serialize_vector(vector: Union[np.ndarray, List[float]]) -> str:
    """
    Serialize a 3D translation vector to a JSON string.
    
    Args:
        vector: 3-element numpy array or list.
        
    Returns:
        JSON string representation of the vector.
    """
    if isinstance(vector, np.ndarray):
        vector = vector.tolist()
    if vector is None:
        return "[]"
    return json.dumps(vector)

def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_filtered_dataset(
    grid_frames: List[GridFrame],
    output_path: str,
    include_checksum: bool = True
) -> Dict[str, Any]:
    """
    Write filtered dataset to CSV with schema:
    sequence_id, frame_id, radial_motion_deg, z_velocity, grid_points_2d, 
    R_matrix, t_vector, randomized_depth
    
    Args:
        grid_frames: List of GridFrame objects to write.
        output_path: Path to the output CSV file.
        include_checksum: Whether to calculate and record SHA256 checksum.
        
    Returns:
        Dictionary with output path and checksum (if calculated).
    """
    ensure_paths_exist([output_path])
    
    fieldnames = [
        'sequence_id', 'frame_id', 'radial_motion_deg', 'z_velocity',
        'grid_points_2d', 'R_matrix', 't_vector', 'randomized_depth'
    ]
    
    rows_written = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for frame in grid_frames:
            row = {
                'sequence_id': frame.sequence_id,
                'frame_id': frame.frame_id,
                'radial_motion_deg': frame.radial_motion_deg,
                'z_velocity': frame.z_velocity,
                'grid_points_2d': serialize_grid_points(frame.grid_points_2d),
                'R_matrix': serialize_matrix(frame.R_matrix),
                't_vector': serialize_vector(frame.t_vector),
                'randomized_depth': frame.randomized_depth
            }
            writer.writerow(row)
            rows_written += 1
    
    logger.info(f"Wrote {rows_written} rows to {output_path}")
    
    result = {
        'output_path': output_path,
        'rows_written': rows_written
    }
    
    if include_checksum:
        checksum = calculate_sha256(output_path)
        result['checksum'] = checksum
        # Also write a checksum file
        checksum_path = f"{output_path}.sha256"
        with open(checksum_path, 'w', encoding='utf-8') as f:
            f.write(f"{checksum}  {os.path.basename(output_path)}\n")
        logger.info(f"Checksum written to {checksum_path}")
    
    return result

def main():
    """
    Main entry point for writing filtered dataset.
    This function is called by the pipeline after filtering and preprocessing.
    """
    from config import get_config
    config = get_config()
    
    # Get paths from config
    filtered_csv_path = get_path('filtered_sequences_csv')
    
    # We expect grid_frames to be available in the pipeline context
    # In a real pipeline, this would be passed from the ingestion/preprocessing step
    # For this module's main, we assume it's called after data is prepared
    logger.info(f"Writing filtered dataset to {filtered_csv_path}")
    
    # Note: In actual usage, grid_frames would be passed as an argument
    # or loaded from intermediate storage. This main is a placeholder
    # for the module's capability.
    logger.warning("main() requires grid_frames data to be passed from pipeline")
    return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
