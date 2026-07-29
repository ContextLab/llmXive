import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import csv

from config import get_path, get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_reconstruction_error(estimated: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """
    Calculate absolute difference between estimated and ground truth dimensions.
    Args:
        estimated: Dict containing 'dimensions' key with [w, h, d] list.
        ground_truth: Dict containing 'dimensions' key with [w, h, d] list.
    Returns:
        float: Absolute error magnitude (L2 norm of difference).
    """
    est_dims = np.array(estimated.get('dimensions', [0, 0, 0]))
    gt_dims = np.array(ground_truth.get('dimensions', [0, 0, 0]))
    
    if np.any(gt_dims == 0):
        return 0.0
        
    error_vec = est_dims - gt_dims
    return float(np.linalg.norm(error_vec))

def process_poses_file(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load poses_estimated.json and return a list of sequence records.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Poses file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'sequences' in data:
        return data['sequences']
    else:
        # Assume flat list or single record wrapped
        return [data] if isinstance(data, dict) else []

def compute_statistics(errors: List[float]) -> Dict[str, float]:
    """
    Compute mean, std, min, max, median of errors.
    """
    if not errors:
        return {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'median': 0.0,
            'count': 0
        }
    
    arr = np.array(errors)
    return {
        'mean': float(np.mean(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'median': float(np.median(arr)),
        'count': len(arr)
    }

def calculate_all_reconstruction_errors(poses_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate reconstruction error for each sequence in poses_data.
    Expects each record to have 'estimated' and 'ground_truth' keys.
    Returns list of dicts: {sequence_id, error, estimated_dims, gt_dims}
    """
    results = []
    for record in poses_data:
        seq_id = record.get('sequence_id', 'unknown')
        est = record.get('estimated', {})
        gt = record.get('ground_truth', {})
        
        err = calculate_reconstruction_error(est, gt)
        
        results.append({
            'sequence_id': seq_id,
            'error': err,
            'estimated_dimensions': est.get('dimensions'),
            'ground_truth_dimensions': gt.get('dimensions')
        })
    return results

def calculate_camera_motion_complexity(poses_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate a complexity metric for each sequence based on camera motion.
    Complexity is defined as the sum of absolute radial motion and Z-velocity magnitude
    derived from the pose estimation or metadata if available.
    
    Since T027 is completed, we assume the 'poses_estimated.json' contains a 'complexity'
    field calculated by the geometry/solver or metrics pipeline, OR we derive it from
    the camera pose deltas (rotation + translation) if not present.
    
    For this implementation, we look for a pre-calculated 'complexity' score in the record.
    If missing, we compute a proxy based on translation magnitude (|t|) and rotation angle.
    """
    results = []
    for record in poses_data:
        seq_id = record.get('sequence_id', 'unknown')
        
        # Try to get pre-calculated complexity first
        complexity = record.get('complexity')
        
        if complexity is None:
            # Fallback: derive from pose data if available
            # Assume record has 'poses' list of {R, t} or similar
            poses = record.get('poses', [])
            if poses:
                total_trans = 0.0
                total_rot = 0.0
                for p in poses:
                    t_vec = p.get('t_vector', [0,0,0])
                    r_mat = p.get('R_matrix', [[1,0,0],[0,1,0],[0,0,1]])
                    
                    # Translation magnitude
                    total_trans += np.linalg.norm(t_vec)
                    
                    # Rotation angle (trace method: cos(theta) = (trace(R)-1)/2)
                    trace_r = np.trace(r_mat)
                    cos_theta = (trace_r - 1) / 2
                    cos_theta = np.clip(cos_theta, -1.0, 1.0)
                    angle = np.arccos(cos_theta)
                    total_rot += np.degrees(angle)
                
                # Normalize or weight as needed. 
                # Using a simple weighted sum: 0.5 * trans + 0.5 * rot (scaled)
                complexity = float(0.5 * total_trans + 0.5 * total_rot / 100.0)
            else:
                complexity = 0.0
        
        results.append({
            'sequence_id': seq_id,
            'complexity': complexity,
            'has_complexity_metric': record.get('complexity') is not None
        })
    return results

def calculate_pearson_correlation(complexities: List[float], errors: List[float]) -> Tuple[float, float]:
    """
    Calculate Pearson's r correlation coefficient between complexity and error.
    Returns (r, p_value).
    """
    if len(complexities) < 2 or len(errors) < 2:
        logger.warning("Insufficient data for correlation analysis.")
        return 0.0, 1.0
    
    x = np.array(complexities)
    y = np.array(errors)
    
    # Remove NaNs if any
    mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
    x = x[mask]
    y = y[mask]
    
    if len(x) < 2:
        return 0.0, 1.0
    
    r, p = np.corrcoef(x, y)
    return float(r), float(p)

def run_correlation_analysis(poses_file: Path, output_file: Path) -> Dict[str, Any]:
    """
    Main entry point for T028: Perform Pearson's r correlation analysis.
    1. Load poses_estimated.json
    2. Calculate complexity for each sequence (if not present)
    3. Calculate reconstruction error for each sequence
    4. Compute Pearson's r between complexity and error
    5. Save results to output_file (JSON)
    """
    logger.info(f"Loading poses from {poses_file}")
    poses_data = process_poses_file(poses_file)
    
    if not poses_data:
        logger.warning("No data found in poses file.")
        return {'error': 'No data', 'r': 0.0, 'p': 1.0}
    
    logger.info("Calculating camera motion complexity...")
    complexity_results = calculate_camera_motion_complexity(poses_data)
    
    logger.info("Calculating reconstruction errors...")
    error_results = calculate_all_reconstruction_errors(poses_data)
    
    # Align by sequence_id
    complexity_map = {r['sequence_id']: r['complexity'] for r in complexity_results}
    error_map = {r['sequence_id']: r['error'] for r in error_results}
    
    common_ids = set(complexity_map.keys()) & set(error_map.keys())
    
    if not common_ids:
        logger.error("No common sequence IDs found between complexity and error results.")
        return {'error': 'No common IDs', 'r': 0.0, 'p': 1.0}
    
    complexities = [complexity_map[sid] for sid in common_ids]
    errors = [error_map[sid] for sid in common_ids]
    
    logger.info(f"Computing Pearson correlation for {len(common_ids)} sequences...")
    r, p = calculate_pearson_correlation(complexities, errors)
    
    results = {
        'analysis_type': 'Pearson Correlation: Complexity vs Accuracy',
        'sequence_count': len(common_ids),
        'pearson_r': r,
        'p_value': p,
        'interpretation': 'Strong positive' if r > 0.7 else ('Moderate positive' if r > 0.4 else ('Weak positive' if r > 0.1 else ('No correlation' if abs(r) <= 0.1 else ('Weak negative' if r > -0.1 else ('Moderate negative' if r > -0.4 else ('Strong negative')))))),
        'details': {
            'mean_complexity': float(np.mean(complexities)),
            'mean_error': float(np.mean(errors)),
            'std_complexity': float(np.std(complexities)),
            'std_error': float(np.std(errors))
        }
    }
    
    logger.info(f"Correlation r={r:.4f}, p={p:.4f}")
    
    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_file}")
    return results

def main():
    """
    CLI entry point for T028.
    Reads from data/processed/poses_estimated.json and writes to data/processed/correlation_analysis.json
    """
    config = get_config()
    poses_path = get_path('POSES_ESTIMATED')
    output_path = get_path('CORRELATION_ANALYSIS')
    
    if not poses_path.exists():
        logger.error(f"Input file not found: {poses_path}")
        return
    
    results = run_correlation_analysis(poses_path, output_path)
    print(f"Analysis complete. R={results['pearson_r']:.4f}, p={results['p_value']:.4f}")

if __name__ == '__main__':
    main()
