"""
Convergence detection logic for Green-Kubo simulations.

This module implements the logic to detect convergence of the heat current
autocorrelation function (HCACF) by checking the relative change in the
final segment of the simulation data.

Convergence Criterion:
The simulation is considered converged if the relative change in the
integrated HCACF (thermal conductivity estimate) over the final segment
is less than 1%.
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

def calculate_hcacf_relative_change(hcacf_data: np.ndarray, window_fraction: float = 0.2) -> float:
    """
    Calculate the relative change in the integrated HCACF over the final segment.

    Args:
        hcacf_data: Array of HCACF values (typically the integrated values or the raw data
                    from which the integral is computed).
        window_fraction: Fraction of the total data points to use for the final segment check.

    Returns:
        The relative change (absolute value) between the mean of the final segment
        and the mean of the preceding segment.
    """
    if len(hcacf_data) < 10:
        logger.warning("HCACF data too short for convergence check. Returning large change.")
        return 1.0  # Force non-convergence

    n_points = len(hcacf_data)
    window_size = max(1, int(n_points * window_fraction))

    # Define the final segment and the segment immediately preceding it
    final_segment = hcacf_data[-window_size:]
    prev_segment = hcacf_data[-(window_size * 2):-window_size]

    if len(prev_segment) == 0:
        logger.warning("Not enough data points for a preceding segment.")
        return 1.0

    # Calculate the mean of the integrated values (or the values themselves if already integrated)
    # Assuming hcacf_data represents the running integral of the autocorrelation (thermal conductivity estimate)
    # If it's raw autocorrelation, we would integrate it here, but typically post_process_hcacf
    # returns the running integral.
    mean_final = np.mean(final_segment)
    mean_prev = np.mean(prev_segment)

    if abs(mean_prev) < 1e-12:
        # Avoid division by zero if the previous value is effectively zero
        return 1.0 if abs(mean_final) > 1e-12 else 0.0

    relative_change = abs(mean_final - mean_prev) / abs(mean_prev)
    return relative_change

def check_convergence(relative_change: float, threshold: float = 0.01) -> bool:
    """
    Check if the relative change is below the convergence threshold.

    Args:
        relative_change: The calculated relative change in the HCACF integral.
        threshold: The threshold for convergence (default 1% or 0.01).

    Returns:
        True if converged (relative_change < threshold), False otherwise.
    """
    return relative_change < threshold

def update_thermal_sample_metadata(thermal_sample: Dict[str, Any], is_converged: bool, relative_change: float) -> Dict[str, Any]:
    """
    Update the thermal sample metadata with convergence status.

    Args:
        thermal_sample: The dictionary representing the ThermalSample object.
        is_converged: Boolean indicating if the simulation converged.
        relative_change: The calculated relative change value.

    Returns:
        The updated thermal sample dictionary.
    """
    if 'metadata' not in thermal_sample:
        thermal_sample['metadata'] = {}

    thermal_sample['metadata']['converged'] = is_converged
    thermal_sample['metadata']['convergence_relative_change'] = float(relative_change)
    thermal_sample['converged'] = is_converged  # Also set at top level as per schema requirement

    return thermal_sample

def process_convergence_for_sample(sample_path: Path, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single thermal sample file to check convergence.

    Args:
        sample_path: Path to the serialized ThermalSample file (pickle).
        config: Configuration dictionary containing convergence parameters.

    Returns:
        The updated thermal sample dictionary if successful, None otherwise.
    """
    try:
        with open(sample_path, 'rb') as f:
            thermal_sample = pickle.load(f)

        # Extract HCACF data. This depends on how green_kubo.py stores it.
        # Assuming it's stored under 'hcacf_data' or similar in the sample.
        # If the green_kubo.py outputs the integrated values, use those directly.
        # If it outputs raw HCACF, we need to integrate.
        # Based on typical Green-Kubo implementation, we expect the running integral.
        hcacf_data = thermal_sample.get('hcacf_data')

        if hcacf_data is None:
            logger.error(f"HCACF data not found in {sample_path}. Skipping convergence check.")
            return None

        # Convert to numpy array if it isn't already
        hcacf_array = np.array(hcacf_data)

        # Calculate relative change
        window_fraction = config.get('convergence_window_fraction', 0.2)
        relative_change = calculate_hcacf_relative_change(hcacf_array, window_fraction)

        # Check convergence
        threshold = config.get('convergence_threshold', 0.01)
        is_converged = check_convergence(relative_change, threshold)

        logger.info(f"Sample {sample_path.stem}: Relative change = {relative_change:.4f}, Converged = {is_converged}")

        # Update metadata
        updated_sample = update_thermal_sample_metadata(thermal_sample, is_converged, relative_change)

        return updated_sample

    except Exception as e:
        logger.error(f"Error processing convergence for {sample_path}: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point to process all thermal samples for convergence.
    Outputs:
        data/processed/conductivities/convergence_status.json
    """
    config = get_config()
    paths = get_paths()

    conductivities_dir = paths['processed_conductivities']
    output_file = conductivities_dir / 'convergence_status.json'

    if not conductivities_dir.exists():
        logger.error(f"Conductivities directory not found: {conductivities_dir}")
        return

    # Find all pickle files in the directory
    sample_files = list(conductivities_dir.glob('*.pkl')) + list(conductivities_dir.glob('*.pickle'))

    if not sample_files:
        logger.warning(f"No thermal sample files found in {conductivities_dir}")
        # Create an empty status file if no samples exist
        with open(output_file, 'w') as f:
            json.dump({}, f, indent=2)
        return

    convergence_status = {}

    for sample_file in sample_files:
        logger.info(f"Processing convergence for: {sample_file.name}")
        updated_sample = process_convergence_for_sample(sample_file, config)

        if updated_sample:
            sample_id = updated_sample.get('graph_id', sample_file.stem)
            converged = updated_sample.get('converged', False)
            convergence_status[sample_id] = converged

            # Save the updated sample back to disk with new metadata
            with open(sample_file, 'wb') as f:
                pickle.dump(updated_sample, f)
            logger.info(f"Updated and saved {sample_file.name}")

    # Write the summary status file
    with open(output_file, 'w') as f:
        json.dump(convergence_status, f, indent=2)

    logger.info(f"Convergence status written to {output_file}")
    logger.info(f"Total samples processed: {len(convergence_status)}")
    logger.info(f"Converged samples: {sum(convergence_status.values())}")

if __name__ == '__main__':
    main()