import os
import json
import logging
import subprocess
import tempfile
import shutil
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from utils.config import ensure_directories
from utils.io import log_operation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/evaluate.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants for COLMAP failure detection
COLMAP_FAILURE_PATTERNS = {
    'insufficient_features': r"(ERROR|WARNING).*?(insufficient_features|no_matches_found|feature_matching_failed)",
    'optimization_divergence': r"(ERROR|WARNING).*?(optimization_divergence|bundle_adjustment_failed|non_convergent)",
    'sparse_reconstruction': r"(ERROR|WARNING).*?(sparse_reconstruction_failed|no_initialization|reconstruction_empty)",
    'image_loading_error': r"(ERROR|WARNING).*?(image_loading_failed|corrupt_image|unsupported_format)",
    'memory_error': r"(ERROR|WARNING).*?(memory_exhausted|out_of_memory|allocation_failed)",
    'camera_calibration_error': r"(ERROR|WARNING).*?(camera_calibration_failed|intrinsics_invalid)",
    'generic_error': r"(ERROR|WARNING).*?(ERROR|CRITICAL)"
}

def extract_frames_from_video(video_path: str, output_dir: str) -> List[str]:
    """
    Extract frames from a video file using OpenCV or ffmpeg.
    
    Args:
        video_path: Path to the input video file
        output_dir: Directory to save extracted frames
        
    Returns:
        List of paths to extracted frame files
    """
    import cv2
    
    ensure_directories([output_dir])
    frames = []
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_path = os.path.join(output_dir, f"frame_{frame_count:06d}.png")
        cv2.imwrite(frame_path, frame)
        frames.append(frame_path)
        frame_count += 1
    
    cap.release()
    
    if len(frames) == 0:
        raise ValueError(f"No frames extracted from video: {video_path}")
    
    logger.info(f"Extracted {len(frames)} frames from {video_path}")
    return frames

def run_colmap_sfm(frame_dir: str, output_dir: str) -> Tuple[bool, Optional[str]]:
    """
    Run COLMAP SfM pipeline on extracted frames.
    
    Args:
        frame_dir: Directory containing extracted frames
        output_dir: Directory for SfM output
        
    Returns:
        Tuple of (success, failure_reason)
    """
    ensure_directories([output_dir])
    
    # Create temporary database and feature extraction directory
    db_path = os.path.join(output_dir, "database.db")
    feature_dir = os.path.join(output_dir, "features")
    match_dir = os.path.join(output_dir, "matches")
    sparse_dir = os.path.join(output_dir, "sparse")
    
    ensure_directories([feature_dir, match_dir, sparse_dir])
    
    try:
        # Feature extraction
        logger.info("Running COLMAP feature extraction...")
        feature_cmd = [
            "colmap", "feature_extractor",
            "--database_path", db_path,
            "--image_path", frame_dir,
            "--ImageReader.single_camera", "1",
            "--SiftExtraction.max_num_features", "16384"
        ]
        
        result = subprocess.run(
            feature_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"Feature extraction failed: {result.stderr}")
            failure_reason = parse_colmap_failure_reason(result.stderr)
            return False, failure_reason
        
        # Feature matching
        logger.info("Running COLMAP feature matching...")
        match_cmd = [
            "colmap", "exhaustive_matcher",
            "--database_path", db_path
        ]
        
        result = subprocess.run(
            match_cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            logger.error(f"Feature matching failed: {result.stderr}")
            failure_reason = parse_colmap_failure_reason(result.stderr)
            return False, failure_reason
        
        # Mapper (SfM)
        logger.info("Running COLMAP mapper...")
        mapper_cmd = [
            "colmap", "mapper",
            "--database_path", db_path,
            "--image_path", frame_dir,
            "--output_path", sparse_dir,
            "--Mapper.num_threads", "4",
            "--Mapper.min_num_matches", "15"
        ]
        
        result = subprocess.run(
            mapper_cmd,
            capture_output=True,
            text=True,
            timeout=1200
        )
        
        if result.returncode != 0:
            logger.error(f"SfM reconstruction failed: {result.stderr}")
            failure_reason = parse_colmap_failure_reason(result.stderr)
            return False, failure_reason
        
        # Check if reconstruction is empty
        recon_files = [f for f in os.listdir(sparse_dir) if f.startswith("cameras")]
        if len(recon_files) == 0:
            logger.warning("SfM reconstruction produced no cameras")
            return False, "sparse_reconstruction"
        
        logger.info("COLMAP SfM completed successfully")
        return True, None
        
    except subprocess.TimeoutExpired:
        logger.error("COLMAP SfM timed out")
        return False, "optimization_divergence"
    except FileNotFoundError as e:
        logger.error(f"COLMAP executable not found: {e}")
        return False, "generic_error"
    except Exception as e:
        logger.error(f"COLMAP SfM failed with exception: {e}")
        return False, "generic_error"

def parse_colmap_failure_reason(colmap_output: str) -> str:
    """
    Parse COLMAP error output to extract standardized failure reason.
    
    Args:
        colmap_output: Raw stderr/stdout from COLMAP execution
        
    Returns:
        Standardized failure reason string
    """
    if not colmap_output:
        return "unknown_error"
    
    # Try each pattern in order of specificity
    for reason, pattern in COLMAP_FAILURE_PATTERNS.items():
        if reason == 'generic_error':
            continue  # Skip generic until end
        
        match = re.search(pattern, colmap_output, re.IGNORECASE | re.DOTALL)
        if match:
            logger.info(f"Detected COLMAP failure reason: {reason}")
            return reason
    
    # Check for generic error patterns
    generic_match = re.search(COLMAP_FAILURE_PATTERNS['generic_error'], colmap_output, re.IGNORECASE)
    if generic_match:
        return "generic_error"
    
    # Default to insufficient_features if we can't determine the cause
    logger.warning(f"Could not parse specific failure reason from COLMAP output: {colmap_output[:200]}")
    return "insufficient_features"

def extract_trajectory_from_sfm(sparse_dir: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract camera trajectory from COLMAP sparse reconstruction.
    
    Args:
        sparse_dir: Directory containing COLMAP sparse reconstruction
        
    Returns:
        List of camera poses (rotation, translation) or None if reconstruction failed
    """
    import numpy as np
    
    cameras_path = os.path.join(sparse_dir, "cameras.bin")
    images_path = os.path.join(sparse_dir, "images.bin")
    points3D_path = os.path.join(sparse_dir, "points3D.bin")
    
    if not os.path.exists(images_path):
        logger.error(f"Images.bin not found in {sparse_dir}")
        return None
    
    # Parse COLMAP binary format (simplified for common cases)
    # This is a basic parser - in production, use colmap.read_model()
    try:
        from colmap.read_write_model import read_model
        cameras, images, points = read_model(sparse_dir, ext=".bin")
        
        trajectory = []
        for image_id, image in images.items():
            # Extract rotation and translation
            q = image.qvec  # Quaternion
            t = image.tvec  # Translation
            
            # Convert quaternion to rotation matrix
            from scipy.spatial.transform import Rotation as R
            rot_matrix = R.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
            
            trajectory.append({
                'image_id': image_id,
                'rotation': rot_matrix.tolist(),
                'translation': t.tolist(),
                'camera_id': image.camera_id
            })
        
        logger.info(f"Extracted {len(trajectory)} camera poses from SfM")
        return trajectory
        
    except ImportError:
        logger.warning("COLMAP Python bindings not available, using fallback parser")
        # Fallback: try to parse text format if available
        return None
    except Exception as e:
        logger.error(f"Failed to extract trajectory from SfM: {e}")
        return None

def calculate_procrustes_alignment(gt_trajectory: List[np.ndarray], 
                                  pred_trajectory: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Procrustes alignment between ground truth and predicted trajectories.
    
    Args:
        gt_trajectory: List of ground truth camera positions
        pred_trajectory: List of predicted camera positions
        
    Returns:
        Tuple of (scale, rotation_matrix, translation_vector)
    """
    from scipy.spatial.transform import Rotation as R
    
    if len(gt_trajectory) != len(pred_trajectory) or len(gt_trajectory) == 0:
        raise ValueError("Trajectories must have same length and be non-empty")
    
    gt_positions = np.array([gt['translation'] for gt in gt_trajectory])
    pred_positions = np.array([pred['translation'] for pred in pred_trajectory])
    
    # Center both trajectories
    gt_center = np.mean(gt_positions, axis=0)
    pred_center = np.mean(pred_positions, axis=0)
    
    gt_centered = gt_positions - gt_center
    pred_centered = pred_positions - pred_center
    
    # Calculate optimal scale
    scale = np.sum(gt_centered * gt_centered) / np.sum(pred_centered * pred_centered)
    scale = np.sqrt(scale)
    
    # Scale predicted trajectory
    pred_scaled = pred_centered * scale
    
    # Calculate optimal rotation using SVD
    H = np.dot(pred_scaled.T, gt_centered)
    U, S, Vt = np.linalg.svd(H)
    R_matrix = np.dot(Vt.T, U.T)
    
    # Ensure right-handed coordinate system
    if np.linalg.det(R_matrix) < 0:
        Vt[-1, :] *= -1
        R_matrix = np.dot(Vt.T, U.T)
    
    # Calculate translation
    t = gt_center - np.dot(scale * R_matrix, pred_center)
    
    logger.info(f"Procrustes alignment: scale={scale:.4f}, rotation det={np.linalg.det(R_matrix):.4f}")
    return scale, R_matrix, t

def calculate_rotation_error(gt_rot: np.ndarray, pred_rot: np.ndarray) -> float:
    """
    Calculate rotation error between two rotation matrices.
    
    Args:
        gt_rot: Ground truth rotation matrix
        pred_rot: Predicted rotation matrix
        
    Returns:
        Rotation error in degrees
    """
    from scipy.spatial.transform import Rotation as R
    
    # Convert to quaternions
    gt_q = R.from_matrix(gt_rot).as_quat()
    pred_q = R.from_matrix(pred_rot).as_quat()
    
    # Calculate angular distance
    dot_product = np.abs(np.dot(gt_q, pred_q))
    angle = 2 * np.arccos(min(dot_product, 1.0))
    
    return np.degrees(angle)

def calculate_scale_drift(gt_depth: float, pred_depth: float) -> float:
    """
    Calculate scale drift as ratio of mean depths.
    
    Args:
        gt_depth: Mean depth of ground truth trajectory
        pred_depth: Mean depth of predicted trajectory
        
    Returns:
        Scale drift ratio
    """
    if gt_depth == 0 or pred_depth == 0:
        return float('inf')
    
    return pred_depth / gt_depth

def calculate_metrics(gt_trajectory: List[Dict[str, Any]], 
                    pred_trajectory: List[Dict[str, Any]],
                    sfm_success: bool) -> Dict[str, Any]:
    """
    Calculate evaluation metrics between ground truth and predicted trajectories.
    
    Args:
        gt_trajectory: Ground truth camera poses
        pred_trajectory: Predicted camera poses
        sfm_success: Whether SfM reconstruction was successful
        
    Returns:
        Dictionary containing MAE position, MAE rotation, scale drift, and convergence status
    """
    if not sfm_success or len(gt_trajectory) == 0 or len(pred_trajectory) == 0:
        return {
            'mae_position': None,
            'mae_rotation': None,
            'scale_drift': None,
            'convergence': False
        }
    
    # Extract positions
    gt_positions = np.array([gt['translation'] for gt in gt_trajectory])
    pred_positions = np.array([pred['translation'] for pred in pred_trajectory])
    
    # Apply Procrustes alignment
    scale, R_matrix, t = calculate_procrustes_alignment(gt_trajectory, pred_trajectory)
    
    # Align predicted positions
    aligned_pred = np.dot(pred_positions * scale, R_matrix.T) + t
    
    # Calculate position MAE
    position_errors = np.linalg.norm(gt_positions - aligned_pred, axis=1)
    mae_position = float(np.mean(position_errors))
    
    # Calculate rotation MAE
    rotation_errors = []
    for gt, pred in zip(gt_trajectory, pred_trajectory):
        gt_rot = np.array(gt['rotation'])
        pred_rot = np.array(pred['rotation'])
        rot_error = calculate_rotation_error(gt_rot, pred_rot)
        rotation_errors.append(rot_error)
    
    mae_rotation = float(np.mean(rotation_errors))
    
    # Calculate scale drift
    gt_mean_depth = np.mean(np.linalg.norm(gt_positions, axis=1))
    pred_mean_depth = np.mean(np.linalg.norm(pred_positions, axis=1))
    scale_drift = calculate_scale_drift(gt_mean_depth, pred_mean_depth)
    
    logger.info(f"Metrics: MAE_pos={mae_position:.4f}, MAE_rot={mae_rotation:.4f}, scale_drift={scale_drift:.4f}")
    
    return {
        'mae_position': mae_position,
        'mae_rotation': mae_rotation,
        'scale_drift': scale_drift,
        'convergence': True
    }

def write_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write metrics to CSV file with proper handling of null values.
    
    Args:
        metrics_list: List of metric dictionaries
        output_path: Path to output CSV file
    """
    ensure_directories([os.path.dirname(output_path)])
    
    fieldnames = [
        'trajectory_id', 'model', 'mae_position', 'mae_rotation', 
        'convergence', 'sfm_failure_reason', 'scale_drift'
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for metrics in metrics_list:
            row = {
                'trajectory_id': metrics.get('trajectory_id', ''),
                'model': metrics.get('model', ''),
                'mae_position': metrics.get('mae_position'),
                'mae_rotation': metrics.get('mae_rotation'),
                'convergence': metrics.get('convergence', False),
                'sfm_failure_reason': metrics.get('sfm_failure_reason', ''),
                'scale_drift': metrics.get('scale_drift')
            }
            writer.writerow(row)
    
    logger.info(f"Wrote {len(metrics_list)} metrics to {output_path}")

def run_evaluation_pipeline(video_path: str, 
                           gt_trajectory: List[Dict[str, Any]],
                           trajectory_id: str,
                           model_name: str = "dreamx_lite") -> Dict[str, Any]:
    """
    Run complete evaluation pipeline for a single trajectory.
    
    Args:
        video_path: Path to generated video
        gt_trajectory: Ground truth camera poses
        trajectory_id: Identifier for this trajectory
        model_name: Name of the model being evaluated
        
    Returns:
        Dictionary containing evaluation results
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        frames_dir = os.path.join(temp_dir, "frames")
        sfm_dir = os.path.join(temp_dir, "sfm")
        
        # Extract frames
        logger.info(f"Extracting frames from {video_path}")
        try:
            frames = extract_frames_from_video(video_path, frames_dir)
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            return {
                'trajectory_id': trajectory_id,
                'model': model_name,
                'mae_position': None,
                'mae_rotation': None,
                'convergence': False,
                'sfm_failure_reason': 'frame_extraction_failed',
                'scale_drift': None
            }
        
        # Run COLMAP SfM
        logger.info("Running COLMAP SfM")
        sfm_success, failure_reason = run_colmap_sfm(frames_dir, sfm_dir)
        
        if not sfm_success:
            logger.warning(f"SfM failed for {trajectory_id}: {failure_reason}")
            return {
                'trajectory_id': trajectory_id,
                'model': model_name,
                'mae_position': None,
                'mae_rotation': None,
                'convergence': False,
                'sfm_failure_reason': failure_reason,
                'scale_drift': None
            }
        
        # Extract trajectory from SfM
        pred_trajectory = extract_trajectory_from_sfm(sfm_dir)
        if pred_trajectory is None:
            logger.warning(f"Failed to extract trajectory from SfM for {trajectory_id}")
            return {
                'trajectory_id': trajectory_id,
                'model': model_name,
                'mae_position': None,
                'mae_rotation': None,
                'convergence': False,
                'sfm_failure_reason': 'trajectory_extraction_failed',
                'scale_drift': None
            }
        
        # Calculate metrics
        metrics = calculate_metrics(gt_trajectory, pred_trajectory, sfm_success)
        metrics['trajectory_id'] = trajectory_id
        metrics['model'] = model_name
        metrics['sfm_failure_reason'] = ''
        
        logger.info(f"Evaluation completed for {trajectory_id}: convergence={metrics['convergence']}")
        return metrics

def main():
    """Main entry point for evaluation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate DreamX-Lite trajectories")
    parser.add_argument("--video_dir", type=str, required=True, help="Directory containing generated videos")
    parser.add_argument("--gt_dir", type=str, required=True, help="Directory containing ground truth trajectories")
    parser.add_argument("--output_csv", type=str, default="data/derived/metrics.csv", help="Output metrics CSV path")
    parser.add_argument("--model_name", type=str, default="dreamx_lite", help="Model name for reporting")
    
    args = parser.parse_args()
    
    ensure_directories([os.path.dirname(args.output_csv)])
    
    # Load ground truth trajectories (simplified - in production, load from actual files)
    # This is a placeholder for the actual GT loading logic
    gt_trajectories = {}
    for gt_file in os.listdir(args.gt_dir):
        if gt_file.endswith(".json"):
            traj_id = gt_file.replace(".json", "")
            with open(os.path.join(args.gt_dir, gt_file), 'r') as f:
                gt_trajectories[traj_id] = json.load(f)
    
    metrics_list = []
    
    # Process each video
    for video_file in os.listdir(args.video_dir):
        if video_file.endswith(".mp4"):
            traj_id = video_file.replace(".mp4", "")
            video_path = os.path.join(args.video_dir, video_file)
            
            if traj_id not in gt_trajectories:
                logger.warning(f"No ground truth for {traj_id}, skipping")
                continue
            
            gt_traj = gt_trajectories[traj_id]
            
            # Run evaluation
            metrics = run_evaluation_pipeline(video_path, gt_traj, traj_id, args.model_name)
            metrics_list.append(metrics)
    
    # Write results to CSV
    write_metrics_to_csv(metrics_list, args.output_csv)
    
    logger.info(f"Evaluation pipeline completed. Results written to {args.output_csv}")
    return metrics_list

if __name__ == "__main__":
    main()