"""
Solver module for CPU-based perspective inversion.
Implements solvePnP using iterative method with no GPU dependencies.
"""
import os
import json
import logging
import csv
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project utilities
from geometry.utils import (
    WorldGridModel,
    get_grid_points_as_object_points,
    WorldGridModel
)
from data.models import GridFrame, CameraPose, ReconstructedBox
from config import get_path, get_config

# Configure logging
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def parse_grid_points_2d(grid_points_str: str) -> np.ndarray:
    """
    Parse grid_points_2d from CSV string format back to numpy array.
    Expected format: [[x1,y1],[x2,y2],...]
    """
    if not grid_points_str or grid_points_str.strip() == '':
        return np.array([])
    try:
        # Remove outer brackets and split by inner brackets
        clean = grid_points_str.strip()[1:-1]  # Remove [ and ]
        if not clean:
            return np.array([])
        points = []
        for point in clean.split('],['):
            coords = [float(x) for x in point.replace('[', '').replace(']', '').split(',')]
            if len(coords) == 2:
                points.append(coords)
        return np.array(points, dtype=np.float32)
    except Exception as e:
        logger.error(f"Error parsing grid points: {e}")
        return np.array([])

def parse_matrix_column(matrix_str: str) -> np.ndarray:
    """
    Parse a matrix column from CSV string format.
    Expected format: [[val1],[val2],[val3]] or [val1,val2,val3]
    """
    if not matrix_str or matrix_str.strip() == '':
        return np.array([])
    try:
        clean = matrix_str.strip()
        # Handle nested list format [[x],[y],[z]]
        if clean.startswith('[[') and clean.endswith(']]'):
            clean = clean[1:-1]
            rows = []
            for row in clean.split('],['):
                row = row.strip('[]')
                if row:
                    rows.append(float(row))
            return np.array(rows, dtype=np.float32)
        # Handle flat list format [x,y,z]
        elif clean.startswith('[') and clean.endswith(']'):
            clean = clean[1:-1]
            return np.array([float(x) for x in clean.split(',')], dtype=np.float32)
        else:
            return np.array([])
    except Exception as e:
        logger.error(f"Error parsing matrix column: {e}")
        return np.array([])

def interpolate_missing_points(points: np.ndarray, max_gap: int = 3) -> np.ndarray:
    """
    Simple linear interpolation for missing grid points.
    Returns interpolated points or original if no gaps detected.
    """
    if len(points) < 2:
        return points
    
    # Check for NaN or zero rows that might indicate missing data
    valid_mask = ~np.isnan(points).any(axis=1)
    if not valid_mask.any():
        return np.zeros_like(points)
    
    # If all valid, return as is
    if valid_mask.all():
        return points
    
    # Interpolate missing values
    indices = np.arange(len(points))
    valid_indices = indices[valid_mask]
    valid_points = points[valid_mask]
    
    try:
        interp_points = np.interp(indices, valid_indices, valid_points)
        return interp_points
    except Exception as e:
        logger.warning(f"Interpolation failed: {e}, returning original")
        return points

def calculate_perspective_distortion_score(R: np.ndarray, t: np.ndarray) -> float:
    """
    Calculate a score indicating the degree of perspective distortion.
    Higher values indicate more extreme distortion.
    """
    if len(R) == 0 or len(t) == 0:
        return 0.0
    
    try:
        # Use rotation matrix to estimate camera tilt
        # The Z-component of the third column of R indicates forward/backward tilt
        tilt_z = abs(R[2, 2]) if R.shape == (3, 3) else 1.0
        
        # Use translation to estimate depth variation
        depth_variation = np.linalg.norm(t)
        
        # Combined score: higher tilt and depth variation = more distortion
        score = (1.0 - tilt_z) * depth_variation
        return float(score)
    except Exception as e:
        logger.error(f"Error calculating distortion score: {e}")
        return 0.0

def solve_pnp_frame(
    image_points: np.ndarray,
    object_points: np.ndarray,
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], bool]:
    """
    CPU-only solvePnP implementation using cv2.solvePnP with SOLVEPNP_ITERATIVE.
    
    Args:
        image_points: 2D image points (N, 2)
        object_points: 3D object points (N, 3)
        camera_matrix: Camera intrinsic matrix (3, 3)
        dist_coeffs: Distortion coefficients (4, 1) or (5, 1)
    
    Returns:
        Tuple of (rotation_vector, translation_vector, success)
    """
    try:
        import cv2
    except ImportError:
        logger.error("OpenCV not installed. Cannot run solvePnP.")
        return None, None, False

    # Ensure points are float32 for OpenCV
    image_points = image_points.astype(np.float32)
    object_points = object_points.astype(np.float32)

    # Validate input shapes
    if len(image_points) < 4 or len(object_points) < 4:
        logger.warning("Insufficient points for solvePnP (need at least 4)")
        return None, None, False

    # CPU-only solvePnP with ITERATIVE method
    # Explicitly using SOLVEPNP_ITERATIVE to ensure CPU execution
    # No GPU flags or CUDA dependencies are used
    success, rvec, tvec = cv2.solvePnP(
        object_points,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        logger.warning("solvePnP failed to converge")
        return None, None, False

    return rvec, tvec, True

def process_filtered_sequences(
    input_csv_path: str,
    output_json_path: str,
    camera_matrix: Optional[np.ndarray] = None,
    dist_coeffs: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Process filtered sequences from CSV and estimate poses using CPU-only solvePnP.
    
    Args:
        input_csv_path: Path to filtered_sequences.csv
        output_json_path: Path to output poses_estimated.json
        camera_matrix: Camera intrinsic matrix (optional, uses default if not provided)
        dist_coeffs: Distortion coefficients (optional, uses zeros if not provided)
    
    Returns:
        Dictionary with processing statistics
    """
    # Default camera parameters (assuming 640x480 image)
    if camera_matrix is None:
        camera_matrix = np.array([
            [320.0, 0.0, 320.0],
            [0.0, 320.0, 240.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
    
    if dist_coeffs is None:
        dist_coeffs = np.zeros((4, 1), dtype=np.float32)

    results = []
    stats = {
        "total_frames": 0,
        "successful_poses": 0,
        "failed_poses": 0,
        "high_distortion_count": 0
    }

    try:
        with open(input_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                stats["total_frames"] += 1
                
                # Parse grid points
                grid_points = parse_grid_points_2d(row.get('grid_points_2d', '[]'))
                if len(grid_points) < 4:
                    stats["failed_poses"] += 1
                    continue
                
                # Interpolate if needed
                grid_points = interpolate_missing_points(grid_points)
                
                # Get ground truth R and t for object points
                # In this implementation, we derive object points from WorldGridModel
                # and use the provided R/t as ground truth for comparison
                r_matrix_str = row.get('R_matrix', '[]')
                t_vector_str = row.get('t_vector', '[]')
                
                # For solvePnP, we need 3D object points
                # Using WorldGridModel to generate canonical object points
                world_grid = WorldGridModel()
                object_points = get_grid_points_as_object_points(world_grid, len(grid_points))
                
                if len(object_points) < 4:
                    stats["failed_poses"] += 1
                    continue
                
                # Solve PnP (CPU-only)
                rvec, tvec, success = solve_pnp_frame(
                    grid_points,
                    object_points,
                    camera_matrix,
                    dist_coeffs
                )
                
                if not success:
                    stats["failed_poses"] += 1
                    continue
                
                stats["successful_poses"] += 1
                
                # Calculate distortion score
                R_est, _ = cv2.Rodrigues(rvec)
                distortion_score = calculate_perspective_distortion_score(R_est, tvec)
                
                if distortion_score > 10.0:  # Threshold for high distortion
                    stats["high_distortion_count"] += 1
                
                # Store result
                result = {
                    "sequence_id": row.get('sequence_id', ''),
                    "frame_id": row.get('frame_id', ''),
                    "rotation_vector": rvec.flatten().tolist(),
                    "translation_vector": tvec.flatten().tolist(),
                    "distortion_score": distortion_score,
                    "success": True
                }
                results.append(result)

        # Write results to JSON
        output_path = Path(output_json_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_json_path, 'w') as f:
            json.dump({
                "results": results,
                "statistics": stats
            }, f, indent=2)
        
        logger.info(f"Processed {stats['total_frames']} frames. "
                   f"Successful: {stats['successful_poses']}, "
                   f"Failed: {stats['failed_poses']}")
        
        return stats

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_csv_path}")
        return stats
    except Exception as e:
        logger.error(f"Error processing sequences: {e}")
        return stats

def main():
    """Main entry point for the solver module."""
    config = get_config()
    input_path = get_path("filtered_sequences_csv")
    output_path = get_path("poses_estimated_json")
    
    logger.info(f"Starting CPU-only solvePnP processing...")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    stats = process_filtered_sequences(input_path, output_path)
    
    print(f"Processing complete. Stats: {stats}")

if __name__ == "__main__":
    main()