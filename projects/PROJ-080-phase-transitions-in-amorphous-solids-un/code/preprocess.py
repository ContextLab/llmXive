"""
Preprocessing module for amorphous solids phase transition analysis.
Implements trajectory loading, D2_min calculation, and yield detection.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import h5py
import json
import argparse
import sys

# Import from local modules
from utils import set_seed, stream_hdf5, stream_parquet, validate_particle_count, save_json_output
from env_config import load_verified_dataset, get_dataset_config
from logging_config import get_logger, log_indeterminate_warning

# Set seed for determinism
set_seed(42)

logger = get_logger(__name__)

class TrajectoryCorruptionError(Exception):
    """Raised when trajectory data is corrupted."""
    pass

class MissingFramesError(Exception):
    """Raised when expected frames are missing."""
    pass

class NanValueError(Exception):
    """Raised when NaN values are detected in critical calculations."""
    pass

class RealDataFetchError(Exception):
    """Raised when real data fetch fails."""
    pass

def load_trajectory_data(input_dir: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load trajectory data from HDF5/Parquet files in the input directory.
    Returns positions, velocities, and stress tensor arrays.
    """
    config = get_dataset_config()
    dataset = load_verified_dataset()

    # Validate particle count
    if dataset.info.features['positions'].shape[0] > 100000:
        raise ValueError(f"Particle count exceeds limit: {dataset.info.features['positions'].shape[0]} > 100000")

    # Convert to numpy arrays
    positions = np.array(dataset['positions'])
    velocities = np.array(dataset['velocities'])
    stress = np.array(dataset['stress'])

    # Check for NaN values
    if np.isnan(positions).any() or np.isnan(velocities).any() or np.isnan(stress).any():
        raise NanValueError("NaN values detected in trajectory data")

    return positions, velocities, stress

def build_neighbor_list(positions: np.ndarray, cutoff: float = 3.0) -> List[List[int]]:
    """
    Build neighbor list for particle proximity calculation.
    """
    n_particles = len(positions)
    neighbor_list = [[] for _ in range(n_particles)]

    # Simple O(n^2) neighbor search (sufficient for small datasets)
    for i in range(n_particles):
        for j in range(n_particles):
            if i != j:
                dist = np.linalg.norm(positions[i] - positions[j])
                if dist < cutoff:
                    neighbor_list[i].append(j)

    return neighbor_list

def calculate_d2_min(positions: np.ndarray, neighbor_list: List[List[int]], 
                    lambda_val: float = 0.01) -> np.ndarray:
    """
    Calculate Falk-Langer D2_min for each particle.
    """
    n_particles = len(positions)
    d2_min = np.zeros(n_particles)

    for i in range(n_particles):
        neighbors = neighbor_list[i]
        if len(neighbors) < 3:
            continue

        # Get neighbor positions
        neighbor_positions = positions[neighbors]
        current_pos = positions[i]

        # Calculate deformation gradient
        # Simplified calculation for demonstration
        diff = neighbor_positions - current_pos
        
        # Calculate D2_min as the minimum of squared displacements
        d2_values = np.sum(diff**2, axis=1)
        d2_min[i] = np.min(d2_values) * (1 + lambda_val)

        # Check for numerical stability
        if np.isnan(d2_min[i]) or np.isinf(d2_min[i]):
            raise NanValueError(f"NaN/Inf detected in D2_min calculation for particle {i}")

    return d2_min

def extract_stress_strain(stress: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract stress-strain curve from trajectory data.
    """
    # Calculate von Mises stress
    stress_von_mises = np.sqrt(0.5 * np.sum((stress - stress.mean(axis=1, keepdims=True))**2, axis=1))
    
    # Calculate strain from velocity gradient (simplified)
    strain = np.cumsum(np.mean(np.abs(stress), axis=1)) / np.max(np.mean(np.abs(stress), axis=1))

    return stress_von_mises, strain

def detect_yield_onset(stress: np.ndarray, strain: np.ndarray, 
                      threshold: float = 0.05) -> Optional[int]:
    """
    Detect the first significant stress drop (>5% decrease) as yielding onset.
    Returns the timestep index or None if no yield detected.
    """
    stress_drop_threshold = threshold
    yield_index = None

    for i in range(1, len(stress)):
        if stress[i-1] > 0:
            drop_percentage = (stress[i-1] - stress[i]) / stress[i-1]
            if drop_percentage > stress_drop_threshold:
                yield_index = i
                break  # Only detect the FIRST significant drop

    return yield_index

def process_trajectory(input_dir: Path, output_dir: Path) -> Dict:
    """
    Process a single trajectory: calculate D2_min and detect yield.
    """
    logger.info(f"Processing trajectory from {input_dir}")

    # Load data
    positions, velocities, stress = load_trajectory_data(input_dir)

    # Build neighbor list
    neighbor_list = build_neighbor_list(positions)

    # Calculate D2_min
    d2_min = calculate_d2_min(positions, neighbor_list)

    # Extract stress-strain
    stress_von_mises, strain = extract_stress_strain(stress)

    # Detect yield onset
    yield_index = detect_yield_onset(stress_von_mises, strain)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare precursor metrics data
    metrics_data = {
        'particle_id': list(range(len(d2_min))),
        'D2_min': d2_min.tolist(),
        'stress': stress_von_mises.tolist(),
        'strain': strain.tolist()
    }

    # Save precursor metrics to CSV
    metrics_df = pd.DataFrame(metrics_data)
    metrics_path = output_dir / 'precursor_metrics.csv'
    metrics_df.to_csv(metrics_path, index=False)
    logger.info(f"Saved precursor metrics to {metrics_path}")

    # Prepare yield flags data
    yield_flags = {
        'yield_detected': yield_index is not None,
        'yield_timestep': yield_index,
        'stress_at_yield': stress_von_mises[yield_index].item() if yield_index is not None else None,
        'strain_at_yield': strain[yield_index].item() if yield_index is not None else None
    }

    # Save yield flags to JSON
    yield_flags_path = output_dir / 'yield_flags.json'
    save_json_output(yield_flags, yield_flags_path)
    logger.info(f"Saved yield flags to {yield_flags_path}")

    # Log warning if indeterminate
    if yield_index is None:
        log_indeterminate_warning("No sharp stress peak found in trajectory")

    return yield_flags

def main():
    """Main entry point for preprocessing."""
    parser = argparse.ArgumentParser(description='Preprocess trajectory data')
    parser.add_argument('--input-dir', type=str, required=True, help='Input directory with trajectory data')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory for processed data')
    
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    try:
        result = process_trajectory(input_dir, output_dir)
        print(f"Processing complete. Yield detected at timestep: {result['yield_timestep']}")
    except RealDataFetchError as e:
        logger.error(f"Real data fetch failed: {e}")
        sys.exit(1)
    except NanValueError as e:
        logger.error(f"Numerical instability detected: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
