"""
Synthetic Halo Data Generator (Controlled Deviations)

This module generates synthetic dark matter halo data as a conditional fallback
when real data acquisition fails. It implements controlled deviations from the
standard NFW profile as mandated by the project plan.

Output: HDF5 file at data/raw/synthetic_halos.h5

NOTE: Per Constitution VII and Project Plan, this generator is ONLY to be used
as a fallback when real data APIs fail. It is NOT for primary execution unless
explicitly mandated by the current stage (which it is for this specific task).
"""
import os
import h5py
import numpy as np
from utils.logging import get_logger
import sys
from pathlib import Path

# Ensure code/data exists in path for imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration constants (matching T004 config.py style)
RANDOM_SEED = 42
NUM_HALOS = 1000
BOX_SIZE = 100.0  # Mpc/h
MIN_PARTICLES = 300
MAX_PARTICLES = 10000
PARTICLE_MASS = 1e9  # Solar masses
BASE_CONCENTRATION_MEAN = 10.0
BASE_CONCENTRATION_STD = 2.0
DEVIATION_OFFSET = 1.5  # Small magnitude offset for controlled deviation

logger = get_logger(__name__)

def generate_halo_properties(n_halos: int, seed: int = RANDOM_SEED) -> dict:
    """
    Generate synthetic halo properties with controlled deviations.

    Args:
        n_halos: Number of halos to generate
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing arrays of halo properties
    """
    rng = np.random.default_rng(seed)

    # Generate halo IDs
    halo_ids = np.arange(n_halos)

    # Generate particle counts (log-uniform distribution between min and max)
    log_min = np.log10(MIN_PARTICLES)
    log_max = np.log10(MAX_PARTICLES)
    log_counts = rng.uniform(log_min, log_max, n_halos)
    particle_counts = np.round(10**log_counts).astype(int)

    # Generate masses based on particle counts
    masses = particle_counts * PARTICLE_MASS + rng.normal(0, 1e8, n_halos)
    masses = np.maximum(masses, MIN_PARTICLES * PARTICLE_MASS)  # Ensure minimum

    # Generate positions (uniform in box)
    positions = rng.uniform(0, BOX_SIZE, size=(n_halos, 3))

    # Generate velocities (Gaussian, zero mean)
    velocity_dispersion = 200.0  # km/s
    velocities = rng.normal(0, velocity_dispersion, size=(n_halos, 3))

    # Generate NFW concentration parameters with controlled deviation
    # Standard NFW would be centered at BASE_CONCENTRATION_MEAN
    # We add a small offset (DEVIATION_OFFSET) to simulate deviation
    concentrations = rng.normal(
        BASE_CONCENTRATION_MEAN + DEVIATION_OFFSET,
        BASE_CONCENTRATION_STD,
        n_halos
    )
    # Ensure concentrations are positive and physically reasonable
    concentrations = np.clip(concentrations, 1.0, 50.0)

    # Generate spin parameters (log-normal distribution, typical range 0.01-0.1)
    spin_log_mean = np.log(0.04)
    spin_log_std = 0.2
    spins = rng.lognormal(np.exp(spin_log_mean), spin_log_std, n_halos)
    spins = np.clip(spins, 0.001, 0.5)

    # Generate shape parameters (s = c/a, typically 0.5-1.0)
    shapes = rng.uniform(0.5, 1.0, n_halos)

    return {
        'halo_id': halo_ids,
        'particle_count': particle_counts,
        'mass': masses,
        'position_x': positions[:, 0],
        'position_y': positions[:, 1],
        'position_z': positions[:, 2],
        'velocity_x': velocities[:, 0],
        'velocity_y': velocities[:, 1],
        'velocity_z': velocities[:, 2],
        'concentration': concentrations,
        'spin': spins,
        'shape': shapes
    }

def save_to_hdf5(data: dict, output_path: str) -> None:
    """
    Save synthetic halo data to HDF5 format.

    Args:
        data: Dictionary of arrays to save
        output_path: Path to output HDF5 file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"Saving synthetic halo data to {output_path}")

    with h5py.File(output_path, 'w') as f:
        f.attrs['generator'] = 'synthetic_generator'
        f.attrs['seed'] = RANDOM_SEED
        f.attrs['deviation_offset'] = DEVIATION_OFFSET
        f.attrs['num_halos'] = len(data['halo_id'])
        f.attrs['box_size'] = BOX_SIZE
        f.attrs['description'] = 'Synthetic dark matter halos with controlled NFW concentration deviation'

        for key, value in data.items():
            if isinstance(value, np.ndarray):
                f.create_dataset(key, data=value)
            else:
                f.create_dataset(key, data=[value])

    logger.info(f"Successfully saved {len(data['halo_id'])} halos to {output_path}")

def generate_synthetic_halos(output_path: str = None) -> str:
    """
    Main entry point for generating synthetic halo data.

    This function is the primary execution path for this stage as per Plan mandate,
    but is designed to be called as a fallback when real data APIs fail.

    Args:
        output_path: Optional custom output path. Defaults to data/raw/synthetic_halos.h5

    Returns:
        Path to the generated file
    """
    if output_path is None:
        output_path = "data/raw/synthetic_halos.h5"

    logger.info(f"Generating {NUM_HALOS} synthetic halos with seed {RANDOM_SEED}")
    logger.info(f"Applying controlled deviation offset of {DEVIATION_OFFSET} to NFW concentration")

    data = generate_halo_properties(NUM_HALOS, seed=RANDOM_SEED)
    save_to_hdf5(data, output_path)

    return output_path

if __name__ == "__main__":
    logger.info("Running synthetic halo generator")
    output_file = generate_synthetic_halos()
    logger.info(f"Synthetic data generation complete: {output_file}")