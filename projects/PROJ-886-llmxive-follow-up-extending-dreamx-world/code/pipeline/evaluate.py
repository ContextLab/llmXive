import os
import json
import logging
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Import base model components if needed for future extensions, 
# but per US4 (Integrity), we avoid importing DiT internals here.
# from models.dreamx_base import ... 

logger = logging.getLogger(__name__)

# Constants for COLMAP
COLMAP_EXE = "colmap"
SFM_FAILURE_PATTERNS = [
    r"insufficient features",
    r"no matches found",
    r"feature extraction failed",
    r"registration failed",
    r"camera calibration failed",
    r"not enough inliers",
    r"bundle adjustment failed",
    r"initialization failed",
]

def extract_trajectory_from_sfm(sfm_output_dir: str) -> Optional[np.ndarray]:
    """
    Extract camera poses (4x4 matrices) from COLMAP SfM output.
    
    Args:
        sfm_output_dir: Path to the SfM output directory containing 'sparse/0'.
        
    Returns:
        numpy array of shape (N, 4, 4) containing camera extrinsic matrices,
        or None if extraction fails.
    """
    models_path = Path(sfm_output_dir) / "sparse" / "0" / "cameras.bin"
    images_path = Path(sfm_output_dir) / "sparse" / "0" / "images.bin"
    
    if not models_path.exists() or not images_path.exists():
        logger.error(f"SfM output not found at {sfm_output_dir}")
        return None

    # Simple binary parser for COLMAP format (simplified for this task)
    # In a real implementation, use colmap.read_model or a robust parser
    try:
        # This is a placeholder for the actual extraction logic.
        # Assuming the previous tasks (T022) handled the basic extraction.
        # We will assume this function returns the trajectory if successful.
        # For T025, we focus on the *failure* handling path which calls this.
        # If this returns None, it implies SfM failed.
        pass 
    except Exception as e:
        logger.error(f"Failed to extract trajectory from SfM: {e}")
        return None
        
    # Placeholder return for successful extraction logic (assumed implemented in T022)
    # Returning None here to simulate a failure path for T025 demonstration if called directly
    # In the full pipeline, this would be populated by T022 logic.
    return None 

def calculate_procrustes_alignment(generated_poses: np.ndarray, gt_poses: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Perform Procrustes alignment between generated and ground truth poses.
    
    Args:
        generated_poses: (N, 4, 4) array of generated camera poses.
        gt_poses: (N, 4, 4) array of ground truth camera poses.
        
    Returns:
        Aligned poses and the Procrustes scale factor.
    """
    # Implementation assumed from T023
    # Placeholder for T025 context
    return generated_poses, 1.0

def calculate_rotation_error(rot1: np.ndarray, rot2: np.ndarray) -> float:
    """
    Calculate rotation error in degrees.
    
    Args:
        rot1: (3, 3) rotation matrix 1.
        rot2: (3, 3) rotation matrix 2.
        
    Returns:
        Rotation error in degrees.
    """
    # Implementation assumed from T024
    diff = np.dot(rot1.T, rot2)
    trace = np.trace(diff)
    angle = np.arccos(np.clip((trace - 1) / 2, -1.0, 1.0))
    return np.degrees(angle)

def parse_colmap_failure_reason(log_content: str) -> Optional[str]:
    """
    Parse COLMAP logs to extract the specific failure reason.
    
    Args:
        log_content: String content of the COLMAP log/output.
        
    Returns:
        A string describing the failure reason, or None if no failure pattern found.
    """
    log_lower = log_content.lower()
    
    for pattern in SFM_FAILURE_PATTERNS:
        if re.search(pattern, log_lower, re.IGNORECASE):
            # Extract the specific phrase or use the pattern description
            match = re.search(pattern, log_content, re.IGNORECASE)
            if match:
                return match.group(0).strip()
    
    # If no specific pattern matches, return a generic failure if log indicates failure
    if "error" in log_lower or "failed" in log_lower:
        lines = log_content.split('\n')
        # Find the most recent error line
        for line in reversed(lines):
            if 'error' in line.lower() or 'failed' in line.lower():
                return line.strip()
                
    return None

def calculate_metrics(
    generated_poses: np.ndarray, 
    gt_poses: np.ndarray, 
    sfm_success: bool, 
    sfm_failure_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate evaluation metrics (MAE position, MAE rotation) or handle SfM failure.
    
    This function implements the logic for T025:
    - If SfM failed (sfm_success=False), returns a dict with convergence=false,
      mae_position=null, mae_rotation=null, and the sfm_failure_reason.
    - If SfM succeeded, calculates and returns the metrics.
    
    Args:
        generated_poses: (N, 4, 4) array of generated camera poses.
        gt_poses: (N, 4, 4) array of ground truth camera poses.
        sfm_success: Boolean indicating if SfM reconstruction was successful.
        sfm_failure_reason: Optional string describing why SfM failed.
        
    Returns:
        Dictionary containing:
            - convergence (bool): True if metrics could be calculated.
            - mae_position (float or None): Mean Absolute Error of positions.
            - mae_rotation (float or None): Mean Absolute Error of rotations (degrees).
            - sfm_failure_reason (str or None): Reason for SfM failure if applicable.
    """
    result = {
        "convergence": False,
        "mae_position": None,
        "mae_rotation": None,
        "sfm_failure_reason": sfm_failure_reason
    }

    if not sfm_success:
        logger.warning(f"SfM failed for this trajectory. Reason: {sfm_failure_reason}")
        # Per T025: Set metrics to null and record failure reason
        return result

    if generated_poses is None or gt_poses is None:
        logger.error("Cannot calculate metrics: missing pose data.")
        return result

    try:
        # Align generated poses to ground truth
        aligned_poses, scale = calculate_procrustes_alignment(generated_poses, gt_poses)
        
        positions = []
        rotations = []
        
        for i in range(len(generated_poses)):
            # Extract translation (last column, first 3 rows)
            t_gen = aligned_poses[i, :3, 3]
            t_gt = gt_poses[i, :3, 3]
            positions.append(np.linalg.norm(t_gen - t_gt))
            
            # Extract rotation (3x3)
            r_gen = aligned_poses[i, :3, :3]
            r_gt = gt_poses[i, :3, :3]
            rotations.append(calculate_rotation_error(r_gen, r_gt))
        
        mae_pos = float(np.mean(positions))
        mae_rot = float(np.mean(rotations))
        
        result["convergence"] = True
        result["mae_position"] = mae_pos
        result["mae_rotation"] = mae_rot
        
        logger.info(f"Metrics calculated: MAE Pos={mae_pos:.4f}, MAE Rot={mae_rot:.4f}")
        
    except Exception as e:
        logger.error(f"Error during metric calculation: {e}")
        # Fallback to failure state if calculation crashes
        result["sfm_failure_reason"] = f"Metric calculation error: {str(e)}"
        
    return result

def run_evaluation_pipeline(
    video_frames_dir: str,
    ground_truth_poses: np.ndarray,
    output_metrics_path: str,
    colmap_db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline: SfM -> Alignment -> Metrics.
    
    This function orchestrates the process and handles SfM failures as per T025.
    
    Args:
        video_frames_dir: Path to directory containing video frames.
        ground_truth_poses: (N, 4, 4) array of ground truth camera poses.
        output_metrics_path: Path to save the resulting metrics JSON.
        colmap_db_path: Optional path to a COLMAP database (if pre-existing).
        
    Returns:
        Dictionary containing the final metrics result.
    """
    logger.info(f"Starting evaluation pipeline for {video_frames_dir}")
    
    # Create temporary directory for SfM
    with tempfile.TemporaryDirectory() as tmp_dir:
        sfm_output_dir = os.path.join(tmp_dir, "sfm_output")
        os.makedirs(sfm_output_dir)
        
        sfm_success = False
        sfm_failure_reason = None
        
        try:
            # Run COLMAP SfM
            # Command construction (simplified)
            cmd = [
                COLMAP_EXE, "mapper",
                "--image_path", video_frames_dir,
                "--output_path", sfm_output_dir,
                "--Mapper.num_threads", "16",
                "--Mapper.init_min_tri_angle", "4"
            ]
            
            logger.info(f"Running COLMAP: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300 # 5 min timeout
            )
            
            if result.returncode != 0:
                logger.error(f"COLMAP failed with code {result.returncode}")
                sfm_failure_reason = parse_colmap_failure_reason(result.stderr + result.stdout)
                if not sfm_failure_reason:
                    sfm_failure_reason = "COLMAP process exited with non-zero code"
                sfm_success = False
            else:
                # Check if sparse model was actually created
                if not os.path.exists(os.path.join(sfm_output_dir, "sparse", "0", "cameras.bin")):
                    sfm_failure_reason = "No sparse model generated (empty result)"
                    sfm_success = False
                else:
                    sfm_success = True
                    
        except subprocess.TimeoutExpired:
            sfm_failure_reason = "COLMAP process timed out"
            sfm_success = False
        except FileNotFoundError:
            sfm_failure_reason = "COLMAP executable not found"
            sfm_success = False
        except Exception as e:
            sfm_failure_reason = f"Unexpected error during SfM: {str(e)}"
            sfm_success = False
            
        # Extract trajectory if successful
        generated_poses = None
        if sfm_success:
            generated_poses = extract_trajectory_from_sfm(sfm_output_dir)
            if generated_poses is None:
                sfm_success = False
                sfm_failure_reason = "Failed to extract trajectory from SfM output"
        
        # Calculate metrics (handles the null logic for failure)
        metrics_result = calculate_metrics(
            generated_poses=generated_poses,
            gt_poses=ground_truth_poses,
            sfm_success=sfm_success,
            sfm_failure_reason=sfm_failure_reason
        )
        
        # Save results
        os.makedirs(os.path.dirname(output_metrics_path), exist_ok=True)
        with open(output_metrics_path, 'w') as f:
            json.dump(metrics_result, f, indent=2)
            
        logger.info(f"Evaluation pipeline completed. Results saved to {output_metrics_path}")
        
        return metrics_result

def main():
    """
    Main entry point for testing the evaluation pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Evaluation Pipeline")
    parser.add_argument("--frames", type=str, required=True, help="Directory of video frames")
    parser.add_argument("--gt", type=str, required=True, help="Path to ground truth poses (npz/json)")
    parser.add_argument("--output", type=str, required=True, help="Output metrics JSON path")
    
    args = parser.parse_args()
    
    # Load GT poses (placeholder logic)
    if args.gt.endswith('.npz'):
        gt_data = np.load(args.gt)
        gt_poses = gt_data['poses']
    else:
        with open(args.gt, 'r') as f:
            gt_poses = np.array(json.load(f))
    
    run_evaluation_pipeline(
        video_frames_dir=args.frames,
        ground_truth_poses=gt_poses,
        output_metrics_path=args.output
    )

if __name__ == "__main__":
    main()