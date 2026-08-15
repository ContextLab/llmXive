"""
Convergence detection logic for Green-Kubo thermal conductivity simulations.

This module implements the logic to detect convergence of the heat current
autocorrelation function (HCACF) by checking the relative change in the final
segment of the simulation.

Convergence criterion: relative change in HCACF integral < 1% in the final segment.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_hcacf_relative_change(hcacf_data: Dict[str, Any]) -> float:
    """
    Calculate the relative change in the HCACF integral over the final segment.

    The HCACF data is expected to contain time series data of the heat current
    autocorrelation function. We compute the integral (cumulative sum) and
    check the relative change between the last two segments.

    Args:
        hcacf_data: Dictionary containing HCACF time series data.
                    Expected keys: 'time', 'hcacf_values', 'integral' (optional)

    Returns:
        float: The relative change in the integral over the final segment.
               Returns np.inf if insufficient data.
    """
    time = np.array(hcacf_data.get('time', []))
    hcacf_values = np.array(hcacf_data.get('hcacf_values', []))

    if len(time) < 2 or len(hcacf_values) < 2:
        logger.warning("Insufficient HCACF data points for convergence check.")
        return np.inf

    # Compute the integral (cumulative trapezoidal integration)
    # Using simple cumulative sum scaled by time step for efficiency
    dt = np.mean(np.diff(time))
    integral = np.cumsum(hcacf_values) * dt

    # Define the final segment as the last 10% of the data
    n_segments = 10
    segment_size = max(1, len(integral) // n_segments)
    final_segment_start = len(integral) - 2 * segment_size
    penultimate_segment_start = len(integral) - 3 * segment_size

    if final_segment_start <= 0 or penultimate_segment_start <= 0:
        logger.warning("Not enough data points to define final segments.")
        return np.inf

    # Get integral values at the end of each segment
    integral_final = integral[-1]
    integral_penultimate = integral[final_segment_start - 1]
    integral_earlier = integral[penultimate_segment_start - 1]

    # Calculate the change in the final segment
    change_final = integral_final - integral_penultimate
    change_penultimate = integral_penultimate - integral_earlier

    # Avoid division by zero
    if abs(change_penultimate) < 1e-10:
        if abs(change_final) < 1e-10:
            return 0.0
        return np.inf

    # Relative change
    relative_change = abs(change_final - change_penultimate) / abs(change_penultimate)

    return relative_change


def check_convergence(hcacf_data: Dict[str, Any], threshold: float = 0.01) -> Tuple[bool, float]:
    """
    Check if the HCACF has converged based on the relative change criterion.

    Args:
        hcacf_data: Dictionary containing HCACF time series data.
        threshold: Convergence threshold (default 0.01 for 1%).

    Returns:
        Tuple[bool, float]: (is_converged, relative_change)
    """
    relative_change = calculate_hcacf_relative_change(hcacf_data)
    is_converged = relative_change < threshold

    return is_converged, relative_change


def update_thermal_sample_metadata(
    sample_path: Path,
    is_converged: bool,
    relative_change: float,
    threshold: float = 0.01
) -> Dict[str, Any]:
    """
    Update the metadata of a ThermalSample object with convergence information.

    Args:
        sample_path: Path to the serialized ThermalSample pickle file.
        is_converged: Whether the simulation converged.
        relative_change: The calculated relative change in HCACF integral.
        threshold: The threshold used for convergence check.

    Returns:
        Dict[str, Any]: The updated sample metadata dictionary.
    """
    with open(sample_path, 'rb') as f:
        sample = pickle.load(f)

    # Ensure metadata exists
    if 'metadata' not in sample:
        sample['metadata'] = {}

    # Update convergence information
    sample['metadata']['converged'] = is_converged
    sample['metadata']['convergence'] = {
        'relative_change': float(relative_change),
        'threshold': float(threshold),
        'status': 'converged' if is_converged else 'not_converged'
    }

    # Save the updated sample
    with open(sample_path, 'wb') as f:
        pickle.dump(sample, f)

    logger.info(
        f"Updated convergence metadata for {sample_path.name}: "
        f"converged={is_converged}, relative_change={relative_change:.6f}"
    )

    return sample.get('metadata', {})


def process_convergence_for_sample(
    sample_path: Path,
    hcacf_data_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Process a single thermal sample to check convergence and update metadata.

    Args:
        sample_path: Path to the ThermalSample pickle file.
        hcacf_data_path: Optional path to the HCACF data file. If not provided,
                         attempts to infer from sample_path.

    Returns:
        Dict[str, Any]: The updated metadata dictionary.
    """
    config = get_config()
    threshold = config.get('convergence', {}).get('hcacf_threshold', 0.01)

    # Infer HCACF data path if not provided
    if hcacf_data_path is None:
        sample_id = sample_path.stem
        hcacf_data_path = sample_path.parent / f"{sample_id}_hcacf.json"

    # Load HCACF data
    if not hcacf_data_path.exists():
        logger.warning(f"HCACF data file not found: {hcacf_data_path}. "
                       f"Marking sample as not converged.")
        # Update metadata to indicate not converged due to missing data
        with open(sample_path, 'rb') as f:
            sample = pickle.load(f)
        if 'metadata' not in sample:
            sample['metadata'] = {}
        sample['metadata']['converged'] = False
        sample['metadata']['convergence'] = {
            'relative_change': float('inf'),
            'threshold': float(threshold),
            'status': 'missing_hcacf_data'
        }
        with open(sample_path, 'wb') as f:
            pickle.dump(sample, f)
        return sample['metadata']

    with open(hcacf_data_path, 'r') as f:
        hcacf_data = json.load(f)

    # Check convergence
    is_converged, relative_change = check_convergence(hcacf_data, threshold)

    # Update sample metadata
    metadata = update_thermal_sample_metadata(
        sample_path, is_converged, relative_change, threshold
    )

    return metadata


def main():
    """
    Main entry point for processing convergence for all thermal samples.
    """
    config = get_config()
    paths = get_paths()

    conductivities_dir = paths['data_processed_conductivities']
    if not conductivities_dir.exists():
        logger.error(f"Conductivities directory not found: {conductivities_dir}")
        sys.exit(1)

    logger.info(f"Processing convergence for samples in {conductivities_dir}")

    results = []
    sample_files = list(conductivities_dir.glob('*.pkl'))

    if not sample_files:
        logger.warning(f"No sample files found in {conductivities_dir}")
        return

    for sample_file in sample_files:
        try:
            metadata = process_convergence_for_sample(sample_file)
            results.append({
                'sample_id': sample_file.stem,
                'converged': metadata.get('converged', False),
                'relative_change': metadata.get('convergence', {}).get('relative_change', None),
                'status': metadata.get('convergence', {}).get('status', 'unknown')
            })
        except Exception as e:
            logger.error(f"Error processing {sample_file}: {e}")
            results.append({
                'sample_id': sample_file.stem,
                'converged': False,
                'error': str(e)
            })

    # Save summary results
    summary_path = conductivities_dir / 'convergence_summary.json'
    with open(summary_path, 'w') as f:
        json.dump({
            'total_samples': len(results),
            'converged_count': sum(1 for r in results if r.get('converged', False)),
            'results': results
        }, f, indent=2)

    logger.info(f"Convergence summary saved to {summary_path}")
    logger.info(f"Total samples: {len(results)}, Converged: {sum(1 for r in results if r.get('converged', False))}")


if __name__ == '__main__':
    import sys
    main()