import os
import json
import logging
import csv
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_path
from data.models import CameraPose, ReconstructedBox
from geometry.utils import WorldGridModel, get_grid_points_as_object_points
from geometry.reconstruction import calculate_box_dimensions
from geometry.writer import write_poses_and_boxes

logger = logging.getLogger(__name__)

# Constants for solvePnP
CAM_FOCAL = 1000.0  # Placeholder, should come from config or metadata
CAM_PRINCIPAL = (512, 512)  # Placeholder


def parse_grid_points_2d(points_str: str) -> np.ndarray:
    """
    Parses a string representation of grid points into a numpy array.
    Expected format: "[[x1, y1], [x2, y2], ...]"
    """
    if not points_str or points_str.strip() == "":
        return np.array([])
    try:
        # Handle stringified list of lists
        cleaned = points_str.replace("'", '"')
        points_list = json.loads(cleaned)
        return np.array(points_list, dtype=np.float32)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse grid points: {points_str}. Error: {e}")
        return np.array([])


def parse_matrix_column(matrix_str: str) -> np.ndarray:
    """
    Parses a string representation of a 3x3 matrix into a numpy array.
    Expected format: "[[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]]"
    """
    if not matrix_str or matrix_str.strip() == "":
        return np.eye(3)
    try:
        cleaned = matrix_str.replace("'", '"')
        matrix_list = json.loads(cleaned)
        return np.array(matrix_list, dtype=np.float32)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse matrix: {matrix_str}. Error: {e}")
        return np.eye(3)


def interpolate_missing_points(points: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Interpolates missing points based on valid neighbors.
    Simple linear interpolation for demonstration.
    """
    if len(points) == 0:
        return points
    
    # Placeholder implementation: just return points if valid
    # A real implementation would use np.interp or similar on valid indices
    return points


def calculate_perspective_distortion_score(points_2d: np.ndarray) -> float:
    """
    Calculates a score indicating the severity of perspective distortion.
    Returns a float where higher values indicate more distortion.
    """
    if len(points_2d) < 4:
        return 0.0
    
    # Calculate area ratios or corner angles to estimate distortion
    # Simple heuristic: variance of triangle areas formed by points
    try:
        # Form triangles from first point to consecutive pairs
        p0 = points_2d[0]
        areas = []
        for i in range(1, len(points_2d) - 1):
            p1 = points_2d[i]
            p2 = points_2d[i+1]
            # Cross product magnitude / 2 for area
            area = 0.5 * abs((p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1]))
            areas.append(area)
        
        if not areas:
            return 0.0
        
        return float(np.std(areas))
    except Exception as e:
        logger.warning(f"Could not calculate distortion score: {e}")
        return 0.0


def solve_pnp_frame(
    frame_id: int,
    grid_points_2d_str: str,
    R_matrix_str: str,
    t_vector_str: str,
    sequence_id: str
) -> Dict[str, Any]:
    """
    Solves PnP for a single frame to estimate camera pose and reconstruct box.
    
    Args:
        frame_id: Frame identifier
        grid_points_2d_str: String of 2D grid points
        R_matrix_str: String of ground truth rotation matrix (used to derive object points)
        t_vector_str: String of ground truth translation vector
        sequence_id: Sequence identifier
    
    Returns:
        Dictionary with pose estimates and box dimensions.
    """
    result = {
        "sequence_id": sequence_id,
        "frame_id": frame_id,
        "status": "pending",
        "camera_pose": None,
        "reconstructed_box": None,
        "error_metrics": {}
    }

    # Parse inputs
    points_2d = parse_grid_points_2d(grid_points_2d_str)
    R_gt = parse_matrix_column(R_matrix_str)
    t_gt = parse_matrix_column(t_vector_str).flatten()

    if len(points_2d) < 4:
        result["status"] = "failed_insufficient_points"
        logger.warning(f"Frame {frame_id} in {sequence_id}: Insufficient grid points ({len(points_2d)})")
        return result

    # Check distortion
    distortion_score = calculate_perspective_distortion_score(points_2d)
    if distortion_score > 1000.0: # Threshold heuristic
        result["status"] = "failed_high_distortion"
        result["error_metrics"]["distortion_score"] = distortion_score
        logger.warning(f"Frame {frame_id} in {sequence_id}: High distortion ({distortion_score})")
        return result

    try:
        # Generate object points from WorldGridModel
        # We assume the ground truth R/t defines the grid orientation in world space
        # For this task, we derive object points from the canonical grid model
        object_points = get_grid_points_as_object_points(points_2d.shape[0])
        
        # If object_points is empty or invalid, fallback to canonical unit grid
        if object_points is None or len(object_points) == 0:
            world_model = WorldGridModel()
            object_points = world_model.points

        # Prepare camera matrix
        K = np.array([
            [CAM_FOCAL, 0, CAM_PRINCIPAL[0]],
            [0, CAM_FOCAL, CAM_PRINCIPAL[1]],
            [0, 0, 1]
        ], dtype=np.float32)
        
        dist_coeffs = np.zeros(5) # Assuming no distortion for simplicity

        # Solve PnP
        success, rvec, tvec = cv2.solvePnP(
            object_points,
            points_2d,
            K,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            result["status"] = "failed_solvepnp"
            logger.error(f"Frame {frame_id} in {sequence_id}: solvePnP failed")
            return result

        # Convert rvec to R matrix
        R_est, _ = cv2.Rodrigues(rvec)
        t_est = tvec.flatten()

        # Calculate box dimensions (simplified: assume unit grid, scale from t)
        # In a real scenario, this would use the reconstructed geometry
        box_dims = calculate_box_dimensions(R_est, t_est, points_2d, object_points)

        result["status"] = "success"
        result["camera_pose"] = {
            "R": R_est.tolist(),
            "t": t_est.tolist()
        }
        result["reconstructed_box"] = box_dims
        result["error_metrics"]["distortion_score"] = distortion_score

    except Exception as e:
        result["status"] = "failed_exception"
        result["error_metrics"]["exception"] = str(e)
        logger.error(f"Frame {frame_id} in {sequence_id}: Exception during solve: {e}", exc_info=True)

    return result


def process_filtered_sequences(input_path: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Processes the filtered sequences CSV, solves PnP for each frame,
    and writes the results to poses_estimated.json.
    """
    if input_path is None:
        input_path = get_path("FILTERED_SEQUENCES_CSV")
    
    if output_path is None:
        output_path = get_path("POSES_ESTIMATED_JSON")

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    logger.info(f"Processing filtered sequences from {input_file}")

    all_poses = []
    failed_count = 0
    success_count = 0

    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                frame_id = int(row['frame_id'])
                seq_id = row['sequence_id']
                grid_points = row['grid_points_2d']
                r_mat = row['R_matrix']
                t_vec = row['t_vector']

                pose_result = solve_pnp_frame(
                    frame_id=frame_id,
                    grid_points_2d_str=grid_points,
                    R_matrix_str=r_mat,
                    t_vector_str=t_vec,
                    sequence_id=seq_id
                )
                
                all_poses.append(pose_result)
                if pose_result["status"] == "success":
                    success_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing row: {row}. Error: {e}")
                failed_count += 1

    logger.info(f"Processed {len(all_poses)} frames. Success: {success_count}, Failed: {failed_count}")

    write_poses_and_boxes(all_poses, output_path)
    return output_path


def main():
    """
    Main entry point to run the solver pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        output_file = process_filtered_sequences()
        logger.info(f"Pipeline complete. Output written to {output_file}")
    except FileNotFoundError as e:
        logger.error(f"Pipeline failed: {e}")
        # In a real CI/CD, this would exit with code 1
        # raise e
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
        # raise e


if __name__ == "__main__":
    main()
