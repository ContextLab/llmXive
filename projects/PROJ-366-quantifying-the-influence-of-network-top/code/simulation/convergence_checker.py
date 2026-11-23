import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from config import get_config, get_paths

logger = logging.getLogger(__name__)

def calculate_hcacf_relative_change(hcacf: np.ndarray, window_fraction: float = 0.2) -> float:
    """
    Calculate the relative change in the Heat Current Autocorrelation Function (HCACF)
    over the final segment of the trajectory.

    Definition: 'Final segment' is the last `window_fraction` (e.g., 20%) of the trajectory steps.
    Metric: Relative change = |mean(last_segment) - mean(first_half_of_last_segment)| / |mean(last_segment)|

    Args:
        hcacf: 1D numpy array of HCACF values.
        window_fraction: Fraction of the trajectory to consider as the 'final segment'.

    Returns:
        float: The calculated relative change. Returns 0.0 if the array is too short.
    """
    if len(hcacf) < 4:
        logger.warning("HCACF array too short to calculate convergence.")
        return 0.0

    n_points = len(hcacf)
    segment_size = int(n_points * window_fraction)

    if segment_size < 2:
        logger.warning("Final segment size too small (< 2 points) for relative change calculation.")
        return 0.0

    final_segment = hcacf[-segment_size:]
    
    # Split the final segment into two halves to measure change
    half_segment_size = segment_size // 2
    if half_segment_size == 0:
       half_segment_size = 1
    
    first_half = final_segment[:half_segment_size]
    second_half = final_segment[half_segment_size:]

    mean_first = np.mean(first_half)
    mean_second = np.mean(second_half)

    # Avoid division by zero if the signal is flat near zero
    denominator = np.abs(mean_second)
    if denominator < 1e-12:
        return 0.0

    relative_change = np.abs(mean_second - mean_first) / denominator
    return relative_change

def check_convergence(relative_change: float, threshold: float = 0.01) -> bool:
    """
    Check if the relative change is below the convergence threshold (1%).

    Args:
        relative_change: The calculated relative change.
        threshold: The threshold for convergence (default 0.01 for 1%).

    Returns:
        bool: True if converged, False otherwise.
    """
    return relative_change < threshold

def update_thermal_sample_metadata(sample_data: Dict[str, Any], is_converged: bool, relative_change: float) -> Dict[str, Any]:
    """
    Update the thermal sample dictionary with convergence status and metrics.

    Args:
        sample_data: The dictionary containing sample data.
        is_converged: Boolean result of convergence check.
        relative_change: The calculated relative change value.

    Returns:
        Dict[str, Any]: Updated sample data.
    """
    if 'metadata' not in sample_data:
        sample_data['metadata'] = {}
    
    sample_data['metadata']['convergence_status'] = is_converged
    sample_data['metadata']['convergence_relative_change'] = float(relative_change)
    
    # Update top-level converged flag if present
    if 'converged' in sample_data:
        sample_data['converged'] = is_converged
        
    return sample_data

def process_convergence_for_sample(sample_id: str, hcacf_path: Optional[Path] = None, hcacf_data: Optional[np.ndarray] = None) -> Tuple[str, bool, float]:
    """
    Process a single sample to determine convergence.
    
    Args:
        sample_id: Identifier for the sample.
        hcacf_path: Path to the HCACF data file (if available).
        hcacf_data: Direct numpy array of HCACF data (if available).
    
    Returns:
        Tuple of (sample_id, is_converged, relative_change).
    """
    config = get_config()
    threshold = config.get('simulation', {}).get('convergence_threshold', 0.01)
    window_fraction = config.get('simulation', {}).get('convergence_window_fraction', 0.2)
    
    hcacf = None
    
    if hcacf_data is not None:
        hcacf = hcacf_data
    elif hcacf_path and hcacf_path.exists():
        try:
            # Try loading as pickle or numpy
            if hcacf_path.suffix == '.npy':
                hcacf = np.load(hcacf_path)
            elif hcacf_path.suffix == '.pkl':
                with open(hcacf_path, 'rb') as f:
                    data = pickle.load(f)
                    # Handle if loaded data is a dict containing the array
                    if isinstance(data, dict) and 'hcacf' in data:
                        hcacf = data['hcacf']
                    elif isinstance(data, np.ndarray):
                        hcacf = data
                    else:
                        # Fallback: assume it's the array directly
                        hcacf = np.array(data)
            else:
                logger.warning(f"Unknown HCACF file format for {sample_id}: {hcacf_path.suffix}")
                return sample_id, False, 0.0
        except Exception as e:
            logger.error(f"Failed to load HCACF for {sample_id} from {hcacf_path}: {e}")
            return sample_id, False, 0.0
    else:
        logger.warning(f"No HCACF data or path provided for {sample_id}. Assuming not converged.")
        return sample_id, False, 0.0

    if hcacf is None or len(hcacf) == 0:
        logger.error(f"Empty HCACF data for {sample_id}.")
        return sample_id, False, 0.0

    relative_change = calculate_hcacf_relative_change(hcacf, window_fraction)
    is_converged = check_convergence(relative_change, threshold)
    
    logger.info(f"Sample {sample_id}: Relative change = {relative_change:.4f}, Converged = {is_converged}")
    return sample_id, is_converged, relative_change

def main():
    """
    Main entry point to process all thermal samples and write convergence status.
    Reads from data/processed/conductivities/ (if serialized samples exist) or
    expects HCACF files to be present.
    """
    config = get_config()
    paths = get_paths()
    output_dir = paths['data_processed_conductivities']
    output_file = paths['data_processed_conductivities'].parent / 'convergence_status.json'
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting convergence detection for samples in {output_dir}")
    
    # Strategy: Look for existing thermal sample files (pkl) which might contain HCACF
    # or look for explicit HCACF files if the pipeline structure changed.
    # We will scan for .pkl files in the conductivities directory.
    
    sample_files = list(output_dir.glob("*.pkl"))
    if not sample_files:
        logger.warning(f"No .pkl files found in {output_dir}. Checking for .json files...")
        sample_files = list(output_dir.glob("*.json"))
    
    convergence_results: Dict[str, bool] = {}
    
    if not sample_files:
        logger.error(f"No sample files found in {output_dir}. Cannot determine convergence.")
        # Write empty result to indicate failure to process
        with open(output_file, 'w') as f:
            json.dump({}, f, indent=2)
        return

    for file_path in sample_files:
        sample_id = file_path.stem
        try:
            with open(file_path, 'rb') as f:
                sample_data = pickle.load(f)
            
            # Attempt to extract HCACF from the sample data
            # The structure depends on how green_kubo.py saves data.
            # Assuming 'hcacf' key or similar.
            hcacf_data = None
            
            if 'hcacf' in sample_data:
                hcacf_data = np.array(sample_data['hcacf'])
            elif 'metadata' in sample_data and 'hcacf' in sample_data['metadata']:
                hcacf_data = np.array(sample_data['metadata']['hcacf'])
            else:
                # Check if it's a numpy file saved alongside
                npy_path = file_path.with_suffix('.npy')
                if npy_path.exists():
                    hcacf_data = np.load(npy_path)
                
            if hcacf_data is None:
                logger.warning(f"Could not find HCACF data in {file_path}. Marking as not converged.")
                convergence_results[sample_id] = False
                continue
            
            _, is_converged, _ = process_convergence_for_sample(sample_id, hcacf_data=hcacf_data)
            convergence_results[sample_id] = is_converged
            
            # Optionally update the sample file with metadata (if writable)
            # This is a side effect, but ensures the source of truth is updated
            if 'metadata' not in sample_data:
                sample_data['metadata'] = {}
            sample_data['metadata']['convergence_status'] = is_converged
            with open(file_path, 'wb') as f:
                pickle.dump(sample_data, f)
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            convergence_results[sample_id] = False

    # Write the final status file
    with open(output_file, 'w') as f:
        json.dump(convergence_results, f, indent=2)
    
    logger.info(f"Convergence status written to {output_file}")
    logger.info(f"Results: {convergence_results}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
