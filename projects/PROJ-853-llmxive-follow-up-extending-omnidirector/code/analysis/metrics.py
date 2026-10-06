import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from config import get_path

logger = logging.getLogger(__name__)

def calculate_reconstruction_error(estimated_value: float, ground_truth_value: float) -> float:
    """
    Calculate the absolute difference (reconstruction error) between an estimated
    value and a ground truth value.

    Args:
        estimated_value: The value estimated by the solver.
        ground_truth_value: The known ground truth value.

    Returns:
        The absolute difference (error).
    """
    if not isinstance(estimated_value, (int, float)) or not isinstance(ground_truth_value, (int, float)):
        raise TypeError("Both estimated and ground truth values must be numeric.")
    
    return abs(float(estimated_value) - float(ground_truth_value))

def process_poses_file(poses_path: Path) -> List[Dict[str, Any]]:
    """
    Load the poses_estimated.json file and return the list of pose entries.

    Args:
        poses_path: Path to the poses_estimated.json file.

    Returns:
        List of dictionaries containing pose data.

    Raises:
        FileNotFoundError: If the poses file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not poses_path.exists():
        raise FileNotFoundError(f"Poses file not found: {poses_path}")

    with open(poses_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # The file is expected to be a list of entries. If it's a dict with a key,
    # we assume the key holds the list (common pattern in some outputs).
    if isinstance(data, dict):
        # Try common keys
        for key in ['poses', 'results', 'data', 'entries']:
            if key in data:
                data = data[key]
                break
        else:
            # If no known key, take the first value that is a list
            for val in data.values():
                if isinstance(val, list):
                    data = val
                    break
    
    if not isinstance(data, list):
        logger.warning(f"Expected a list in {poses_path}, got {type(data)}. Wrapping in list.")
        data = [data]

    return data

def compute_statistics(errors: List[float]) -> Dict[str, float]:
    """
    Compute basic statistics for a list of errors.

    Args:
        errors: List of error values.

    Returns:
        Dictionary with mean, median, std, min, max.
    """
    if not errors:
        return {
            'mean': 0.0,
            'median': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0
        }

    arr = np.array(errors)
    return {
        'mean': float(np.mean(arr)),
        'median': float(np.median(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'count': len(errors)
    }

def calculate_all_reconstruction_errors(poses_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Iterate through the poses data, calculate reconstruction errors for dimensions
    where both estimated and ground truth values are present.

    Expected keys in each pose dict:
        - 'sequence_id', 'frame_id' (identifiers)
        - 'estimated_box': {'width', 'height', 'depth'}
        - 'ground_truth_box': {'width', 'height', 'depth'}

    Args:
        poses_data: List of pose dictionaries.

    Returns:
        List of dictionaries containing errors for each dimension per frame.
    """
    results = []
    for entry in poses_data:
        seq_id = entry.get('sequence_id', 'unknown')
        frame_id = entry.get('frame_id', 'unknown')
        
        est_box = entry.get('estimated_box', {})
        gt_box = entry.get('ground_truth_box', {})

        if not est_box or not gt_box:
            # Log warning if data is missing but continue
            logger.debug(f"Missing box data for {seq_id}/{frame_id}. Skipping error calc.")
            continue

        dims = ['width', 'height', 'depth']
        for dim in dims:
            est_val = est_box.get(dim)
            gt_val = gt_box.get(dim)

            if est_val is not None and gt_val is not None:
                error = calculate_reconstruction_error(est_val, gt_val)
                results.append({
                    'sequence_id': seq_id,
                    'frame_id': frame_id,
                    'dimension': dim,
                    'estimated': est_val,
                    'ground_truth': gt_val,
                    'error': error
                })
            else:
                logger.debug(f"Missing {dim} for {seq_id}/{frame_id}. Skipping.")

    return results

def calculate_camera_motion_complexity(poses_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate a complexity metric based on the variance of motion vectors or
    the magnitude of rotation/translation changes between frames.
    
    For this implementation, we use the sum of absolute differences in 
    rotation (rvec) and translation (tvec) magnitudes compared to the previous frame.
    
    Args:
        poses_data: List of pose dictionaries containing 'rvec' and 'tvec'.

    Returns:
        List of dictionaries with complexity metrics per sequence.
    """
    # Group by sequence
    sequences: Dict[str, List[Dict]] = {}
    for entry in poses_data:
        seq_id = entry.get('sequence_id', 'unknown')
        if seq_id not in sequences:
            sequences[seq_id] = []
        sequences[seq_id].append(entry)

    complexities = []
    for seq_id, frames in sequences.items():
        # Sort frames if possible, otherwise process in order
        # Assuming frames are ordered in the list for now
        total_complexity = 0.0
        prev_rvec = None
        prev_tvec = None

        for frame in frames:
            rvec = frame.get('rvec')
            tvec = frame.get('tvec')

            if rvec is None or tvec is None:
                continue

            if isinstance(rvec, list):
                rvec = np.array(rvec)
            if isinstance(tvec, list):
                tvec = np.array(tvec)

            if prev_rvec is not None:
                # Calculate change in rotation and translation
                delta_r = np.linalg.norm(rvec - prev_rvec)
                delta_t = np.linalg.norm(tvec - prev_tvec)
                total_complexity += delta_r + delta_t

            prev_rvec = rvec
            prev_tvec = tvec

        complexities.append({
            'sequence_id': seq_id,
            'complexity_score': total_complexity,
            'frame_count': len(frames)
        })

    return complexities

def calculate_pearson_correlation(x: List[float], y: List[float]) -> float:
    """
    Calculate Pearson's correlation coefficient between two lists.

    Args:
        x: List of values (e.g., complexity scores).
        y: List of values (e.g., reconstruction errors).

    Returns:
        Pearson correlation coefficient.
    """
    if len(x) != len(y) or len(x) < 2:
        logger.warning("Insufficient data for correlation calculation.")
        return 0.0

    x_arr = np.array(x)
    y_arr = np.array(y)

    # Handle constant arrays
    if np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return 0.0

    correlation = np.corrcoef(x_arr, y_arr)[0, 1]
    if np.isnan(correlation):
        return 0.0
    return float(correlation)

def run_correlation_analysis(poses_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run the full correlation analysis:
    1. Calculate complexity for each sequence.
    2. Calculate mean error for each sequence.
    3. Correlate complexity vs mean error.

    Args:
        poses_data: List of pose dictionaries.

    Returns:
        Dictionary containing correlation results and summary stats.
    """
    # 1. Get complexity per sequence
    complexity_data = calculate_camera_motion_complexity(poses_data)
    complexity_map = {item['sequence_id']: item['complexity_score'] for item in complexity_data}

    # 2. Calculate mean error per sequence
    all_errors = calculate_all_reconstruction_errors(poses_data)
    error_by_seq: Dict[str, List[float]] = {}
    for item in all_errors:
        seq_id = item['sequence_id']
        if seq_id not in error_by_seq:
            error_by_seq[seq_id] = []
        error_by_seq[seq_id].append(item['error'])
    
    mean_error_map = {seq_id: np.mean(errors) for seq_id, errors in error_by_seq.items()}

    # 3. Prepare lists for correlation
    x_vals = []
    y_vals = []
    for seq_id in complexity_map:
        if seq_id in mean_error_map:
            x_vals.append(complexity_map[seq_id])
            y_vals.append(mean_error_map[seq_id])

    if not x_vals:
        return {
            'pearson_r': 0.0,
            'p_value': 0.0,
            'sample_size': 0,
            'error': "No overlapping data for correlation."
        }

    r = calculate_pearson_correlation(x_vals, y_vals)
    
    # Simple p-value approximation (two-tailed) using scipy if available, else 0
    try:
        from scipy import stats
        _, p_value = stats.pearsonr(x_vals, y_vals)
        p_value = float(p_value)
    except ImportError:
        logger.warning("scipy not found. P-value set to 0.0.")
        p_value = 0.0

    return {
        'pearson_r': r,
        'p_value': p_value,
        'sample_size': len(x_vals),
        'complexity_stats': compute_statistics(x_vals),
        'error_stats': compute_statistics(y_vals)
    }

def main():
    """
    Main entry point to run reconstruction error analysis.
    Reads poses_estimated.json, calculates errors, and prints summary statistics.
    """
    config = get_path('project_root')
    poses_path = config / 'data' / 'processed' / 'poses_estimated.json'
    
    logger.info(f"Loading poses from {poses_path}")
    
    try:
        poses_data = process_poses_file(poses_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in poses file: {e}")
        return

    if not poses_data:
        logger.warning("No poses data found.")
        return

    # Calculate all errors
    errors = calculate_all_reconstruction_errors(poses_data)
    
    if not errors:
        logger.warning("No reconstruction errors could be calculated (missing ground truth?).")
        return

    # Flatten errors to a list of values for summary
    error_values = [e['error'] for e in errors]
    stats = compute_statistics(error_values)

    logger.info("--- Reconstruction Error Summary ---")
    logger.info(f"Total error entries: {stats['count']}")
    logger.info(f"Mean Error: {stats['mean']:.4f}")
    logger.info(f"Median Error: {stats['median']:.4f}")
    logger.info(f"Std Dev: {stats['std']:.4f}")
    logger.info(f"Min Error: {stats['min']:.4f}")
    logger.info(f"Max Error: {stats['max']:.4f}")
    logger.info("------------------------------------")

    # Run correlation analysis
    corr_results = run_correlation_analysis(poses_data)
    logger.info("--- Correlation Analysis ---")
    logger.info(f"Pearson's r: {corr_results['pearson_r']:.4f}")
    logger.info(f"P-value: {corr_results['p_value']:.4f}")
    logger.info(f"Sample size: {corr_results['sample_size']}")
    logger.info("----------------------------")

    # Optionally save results to a file
    output_dir = config / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'error_analysis_results.json'
    
    results_payload = {
        'error_statistics': stats,
        'correlation_analysis': corr_results,
        'raw_errors': errors
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_payload, f, indent=2)
    
    logger.info(f"Results written to {output_file}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()