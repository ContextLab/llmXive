"""
Synthetic Halo Data Generator (Controlled Deviations)

This module generates synthetic dark matter halo data as a fallback when
real data acquisition fails.  It now accepts explicit arguments for the
number of halos, random seed and the deviation offset so that the
integration test can control the generation process.
"""
import os
import h5py
import numpy as np
from utils.logging import get_logger
import sys
from pathlib import Path

# Ensure sibling imports work when the module is executed as a script.
sys.path.insert(0, str(Path(__file__).parent.parent))

# ----------------------------------------------------------------------
# Default configuration values – these match the defaults used elsewhere
# in the project and can be overridden by the caller.
# ----------------------------------------------------------------------
DEFAULT_RANDOM_SEED = 42
DEFAULT_NUM_HALOS = 1000
DEFAULT_BOX_SIZE = 100.0          # Mpc/h
DEFAULT_MIN_PARTICLES = 300
DEFAULT_MAX_PARTICLES = 10000
PARTICLE_MASS = 1e9                # Solar masses
BASE_CONCENTRATION_MEAN = 10.0
BASE_CONCENTRATION_STD = 2.0
DEFAULT_DEVIATION_OFFSET = 1.5    # Small magnitude offset for controlled deviation

logger = get_logger(__name__)


def generate_halo_properties(
    n_halos: int,
    seed: int = DEFAULT_RANDOM_SEED,
    deviation_offset: float = DEFAULT_DEVIATION_OFFSET,
) -> dict:
    """
    Generate synthetic halo properties with controlled deviations.

    Parameters
    ----------
    n_halos : int
        Number of halos to generate.
    seed : int, optional
        Random seed for reproducibility.
    deviation_offset : float, optional
        Offset added to the mean NFW concentration to create a controlled
        deviation from the canonical profile.

    Returns
    -------
    dict
        Dictionary containing arrays of halo properties.
    """
    rng = np.random.default_rng(seed)

    # Halo identifiers
    halo_ids = np.arange(n_halos)

    # Particle counts – log‑uniform distribution between the configured limits
    log_min = np.log10(DEFAULT_MIN_PARTICLES)
    log_max = np.log10(DEFAULT_MAX_PARTICLES)
    log_counts = rng.uniform(log_min, log_max, n_halos)
    particle_counts = np.round(10**log_counts).astype(int)

    # Masses derived from particle counts
    masses = particle_counts * PARTICLE_MASS + rng.normal(0, 1e8, n_halos)
    masses = np.maximum(masses, DEFAULT_MIN_PARTICLES * PARTICLE_MASS)

    # Positions uniformly distributed in the simulation box
    positions = rng.uniform(0, DEFAULT_BOX_SIZE, size=(n_halos, 3))

    # Velocities – Gaussian with zero mean
    velocity_dispersion = 200.0  # km/s
    velocities = rng.normal(0, velocity_dispersion, size=(n_halos, 3))

    # Concentrations – base NFW mean plus the controlled offset
    concentrations = rng.normal(
        BASE_CONCENTRATION_MEAN + deviation_offset,
        BASE_CONCENTRATION_STD,
        n_halos,
    )
    concentrations = np.clip(concentrations, 1.0, 50.0)

    # Spin parameters – log‑normal distribution typical for ΛCDM halos
    spin_log_mean = np.log(0.04)
    spin_log_std = 0.2
    spins = rng.lognormal(np.exp(spin_log_mean), spin_log_std, n_halos)
    spins = np.clip(spins, 0.001, 0.5)

    # Shape parameters (c/a) uniformly between 0.5 and 1.0
    shapes = rng.uniform(0.5, 1.0, n_halos)

    return {
        "halo_id": halo_ids,
        "particle_count": particle_counts,
        "mass": masses,
        "position_x": positions[:, 0],
        "position_y": positions[:, 1],
        "position_z": positions[:, 2],
        "velocity_x": velocities[:, 0],
        "velocity_y": velocities[:, 1],
        "velocity_z": velocities[:, 2],
        "concentration": concentrations,
        "spin": spins,
        "shape": shapes,
    }


def save_to_hdf5(data: dict, output_path: str) -> None:
    """
    Persist the synthetic halo catalogue to an HDF5 file.

    Parameters
    ----------
    data : dict
        Mapping of column names to ``numpy.ndarray`` objects.
    output_path : str
        Destination file path.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Saving synthetic halo data to {output_path}")

    with h5py.File(output_path, "w") as f:
        f.attrs["generator"] = "synthetic_generator"
        f.attrs["seed"] = data.get("seed", DEFAULT_RANDOM_SEED)
        f.attrs["deviation_offset"] = data.get(
            "deviation_offset", DEFAULT_DEVIATION_OFFSET
        )
        f.attrs["num_halos"] = len(data["halo_id"])
        f.attrs["box_size"] = DEFAULT_BOX_SIZE
        f.attrs[
            "description"
        ] = "Synthetic dark matter halos with controlled NFW concentration deviation"

        for key, value in data.items():
            if isinstance(value, np.ndarray):
                f.create_dataset(key, data=value)
            else:
                # Ensure scalar values are stored as a one‑element array
                f.create_dataset(key, data=[value])

    logger.info(f"Successfully saved {len(data['halo_id'])} halos to {output_path}")


def generate_synthetic_halos(
    num_halos: int = DEFAULT_NUM_HALOS,
    output_path: str = None,
    seed: int = DEFAULT_RANDOM_SEED,
    deviation_offset: float = DEFAULT_DEVIATION_OFFSET,
) -> str:
    """
    Public entry point used by the data‑pipeline and the integration test.

    Parameters
    ----------
    num_halos : int, optional
        Number of halos to generate (default: 1000).
    output_path : str, optional
        Destination HDF5 file.  If omitted, defaults to
        ``data/raw/synthetic_halos.h5``.
    seed : int, optional
        Random seed for reproducibility.
    deviation_offset : float, optional
        Controlled offset applied to the NFW concentration mean.

    Returns
    -------
    str
        Path to the generated HDF5 file.
    """
    if output_path is None:
        output_path = os.path.join("data", "raw", "synthetic_halos.h5")

    logger.info(
        f"Generating {num_halos} synthetic halos (seed={seed}, deviation_offset={deviation_offset})"
    )

    data = generate_halo_properties(
        n_halos=num_halos,
        seed=seed,
        deviation_offset=deviation_offset,
    )
    # Attach the generation parameters for provenance
    data["seed"] = seed
    data["deviation_offset"] = deviation_offset

    save_to_hdf5(data, output_path)
    return output_path


if __name__ == "__main__":
    logger.info("Running synthetic halo generator as a script")
    output_file = generate_synthetic_halos()
    logger.info(f"Synthetic data generation complete: {output_file}")
