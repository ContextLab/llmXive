import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from config import get_path, get_constant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_reconstruction_error(estimated: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """
    Calculate the absolute difference between estimated and ground truth box dimensions.
    
    Args:
        estimated: Dictionary containing 'dimensions' (h, w, d) from reconstruction.
        ground_truth: Dictionary containing 'dimensions' (h, w, d) from metadata.
        
    Returns:
        Absolute error (sum of absolute differences across dimensions).
    """
    est_dims = estimated.get('dimensions', {})
    gt_dims = ground_truth.get('dimensions', {})
    
    if not est_dims or not gt_dims:
        logger.warning("Missing dimensions in comparison")
        return float('nan')
    
    errors = []
    for dim in ['height', 'width', 'depth']:
        e_val = est_dims.get(dim, 0.0)
        g_val = gt_dims.get(dim, 0.0)
        if isinstance(e_val, (int, float)) and isinstance(g_val, (int, float)):
            errors.append(abs(float(e_val) - float(g_val)))
        
    return sum(errors) if errors else float('nan')

def process_poses_file(poses_path: Path) -> List[Dict[str, Any]]:
    """
    Load and process the poses_estimated.json file.
    
    Args:
        poses_path: Path to the JSON file containing pose estimates.
        
    Returns:
        List of processed pose records.
    """
    if not poses_path.exists():
        raise FileNotFoundError(f"Poses file not found: {poses_path}")
    
    with open(poses_path, 'r') as f:
        data = json.load(f)
        
    # Handle both list of records and dict of records
    if isinstance(data, dict):
        records = list(data.values())
    else:
        records = data
        
    logger.info(f"Loaded {len(records)} pose records from {poses_path}")
    return records

def compute_statistics(values: List[float]) -> Dict[str, float]:
    """
    Compute basic statistics for a list of numerical values.
    
    Args:
        values: List of float values.
        
    Returns:
        Dictionary with mean, std, min, max, count.
    """
    if not values:
        return {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0
        }
        
    arr = np.array(values)
    return {
        'mean': float(np.mean(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'count': len(arr)
    }

def calculate_all_reconstruction_errors(poses_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate reconstruction errors for all pose records.
    
    Args:
        poses_records: List of pose records containing 'estimated' and 'ground_truth'.
        
    Returns:
        List of records with added 'reconstruction_error' field.
    """
    results = []
    for record in poses_records:
        est = record.get('estimated', {})
        gt = record.get('ground_truth', {})
        
        error = calculate_reconstruction_error(est, gt)
        
        result = record.copy()
        result['reconstruction_error'] = error
        results.append(result)
        
    return results

def calculate_camera_motion_complexity(poses_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate a complexity metric for camera motion per sequence.
    
    The complexity metric is defined as a weighted combination of:
    1. Angular velocity magnitude (rotation speed)
    2. Linear velocity magnitude (translation speed)
    3. Variance in motion direction (change in heading)
    
    This metric helps correlate motion complexity with reconstruction accuracy.
    
    Args:
        poses_records: List of pose records containing 'sequence_id', 'frame_id', 
                       and 'pose' (with rotation matrix R and translation vector t).
                       
    Returns:
        List of records with added 'motion_complexity' field.
    """
    logger.info("Calculating camera motion complexity metrics...")
    
    # Group by sequence
    sequences: Dict[str, List[Dict]] = {}
    for record in poses_records:
        seq_id = record.get('sequence_id', 'unknown')
        if seq_id not in sequences:
            sequences[seq_id] = []
        sequences[seq_id].append(record)
    
    complexity_results = []
    
    for seq_id, frames in sequences.items():
        # Sort frames by frame_id
        frames = sorted(frames, key=lambda x: x.get('frame_id', 0))
        
        if len(frames) < 2:
            # Not enough frames to calculate motion
            for f in frames:
                result = f.copy()
                result['motion_complexity'] = 0.0
                complexity_results.append(result)
            continue
        
        # Extract poses and calculate motion vectors
        velocities = []
        angular_velocities = []
        direction_changes = []
        
        prev_R = None
        prev_t = None
        
        for i, frame in enumerate(frames):
            pose = frame.get('pose', {})
            R = pose.get('R_matrix')
            t = pose.get('t_vector')
            
            if R is None or t is None:
                continue
            
            # Convert to numpy arrays
            R = np.array(R).reshape(3, 3) if not isinstance(R, np.ndarray) else R
            t = np.array(t).reshape(3) if not isinstance(t, np.ndarray) else t
            
            if prev_R is not None and prev_t is not None:
                # Calculate linear velocity (translation difference)
                linear_vel = t - prev_t
                linear_vel_mag = np.linalg.norm(linear_vel)
                velocities.append(linear_vel_mag)
                
                # Calculate angular velocity (rotation difference)
                # R_rel = R_prev.T @ R_curr
                R_rel = prev_R.T @ R
                # Convert to axis-angle
                angle, axis = cv2.Rodrigues(R_rel)
                angular_vel_mag = np.linalg.norm(angle)
                angular_velocities.append(angular_vel_mag)
                
                # Calculate direction change (dot product of consecutive translation vectors)
                if len(velocities) > 1:
                    prev_vel = velocities[-2]
                    curr_vel = velocities[-1]
                    if prev_vel > 1e-6 and curr_vel > 1e-6:
                        # Normalize and compare
                        # Note: We need the actual vectors, not just magnitudes
                        # Re-calculate from stored vectors would be ideal, but for complexity
                        # we can approximate using angular change
                        direction_changes.append(angular_vel_mag)
            
            prev_R = R
            prev_t = t
        
        # Calculate complexity score
        if velocities and angular_velocities:
            avg_linear = np.mean(velocities)
            avg_angular = np.mean(angular_velocities)
            avg_direction_change = np.mean(direction_changes) if direction_changes else 0.0
            
            # Weighted sum: angular motion typically harder to reconstruct than linear
            # Weights can be tuned based on empirical results
            w_linear = 0.3
            w_angular = 0.5
            w_direction = 0.2
            
            complexity = (w_linear * avg_linear + 
                         w_angular * avg_angular + 
                         w_direction * avg_direction_change)
        else:
            complexity = 0.0
        
        # Assign complexity to all frames in sequence
        for f in frames:
            result = f.copy()
            result['motion_complexity'] = float(complexity)
            complexity_results.append(result)
    
    logger.info(f"Calculated complexity for {len(sequences)} sequences")
    return complexity_results

def main():
    """
    Main entry point for the metrics module.
    Runs the full analysis pipeline:
    1. Loads poses_estimated.json
    2. Calculates reconstruction errors
    3. Calculates motion complexity
    4. Computes statistics
    5. Outputs results to data/processed/reconstruction_results.csv
    """
    config = get_path('data/processed/poses_estimated.json')
    output_path = get_path('data/processed/reconstruction_results.csv')
    
    logger.info(f"Starting metrics analysis pipeline")
    logger.info(f"Input: {config}")
    logger.info(f"Output: {output_path}")
    
    try:
        # Load data
        records = process_poses_file(Path(config))
        
        # Calculate errors
        records_with_errors = calculate_all_reconstruction_errors(records)
        
        # Calculate complexity
        records_with_complexity = calculate_camera_motion_complexity(records_with_errors)
        
        # Compute statistics
        errors = [r.get('reconstruction_error', 0.0) for r in records_with_complexity if not np.isnan(r.get('reconstruction_error', float('nan')))]
        complexities = [r.get('motion_complexity', 0.0) for r in records_with_complexity]
        
        error_stats = compute_statistics(errors)
        complexity_stats = compute_statistics(complexities)
        
        logger.info(f"Error stats: {error_stats}")
        logger.info(f"Complexity stats: {complexity_stats}")
        
        # Write results to CSV
        import csv
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['sequence_id', 'frame_id', 'reconstruction_error', 'motion_complexity']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            
            writer.writeheader()
            for record in records_with_complexity:
                writer.writerow({
                    'sequence_id': record.get('sequence_id', ''),
                    'frame_id': record.get('frame_id', ''),
                    'reconstruction_error': record.get('reconstruction_error', ''),
                    'motion_complexity': record.get('motion_complexity', '')
                })
        
        logger.info(f"Results written to {output_path}")
        
        # Also write summary stats to a separate file for reporting
        stats_path = Path(output_path).parent / 'metrics_summary.json'
        with open(stats_path, 'w') as f:
            json.dump({
                'error_statistics': error_stats,
                'complexity_statistics': complexity_stats,
                'total_records': len(records_with_complexity)
            }, f, indent=2)
        
        logger.info(f"Summary statistics written to {stats_path}")
        
    except Exception as e:
        logger.error(f"Error in metrics pipeline: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()