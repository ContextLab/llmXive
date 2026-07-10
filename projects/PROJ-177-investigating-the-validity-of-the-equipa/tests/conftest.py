"""
Pytest configuration and shared fixtures for the Equipartition Theorem investigation.

This module provides:
- Global random seed pinning for reproducibility.
- Fixtures to generate synthetic particle tracking data (CSV) with known physics.
- Fixtures for driving signal logs.
- Fixtures for material configuration.
"""

import os
import random
import tempfile
from pathlib import Path
from typing import Generator

import numpy as np
import pandas as pd
import pytest
import yaml

# Set global random seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)


@pytest.fixture(scope="session", autouse=True)
def set_global_seed():
    """Ensure a fixed random seed is set at the start of the test session."""
    # Seeds are set at module level, but this ensures pytest runs with them
    # if any subprocess or late import relies on the environment.
    pass


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data artifacts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_material_config() -> dict:
    """Return a valid material configuration dictionary matching data/config.yaml structure."""
    return {
        "materials": {
            "steel": {
                "mass_kg": 0.01,
                "inertia_kg_m2": 1.2e-6,
                "roughness_proxy": 0.8
            },
            "polymer": {
                "mass_kg": 0.005,
                "inertia_kg_m2": 6.0e-7,
                "roughness_proxy": 0.4
            }
        },
        "frequency_bins": {
            "low": [0, 10],
            "medium": [10, 50],
            "high": [50, 100]
        }
    }


@pytest.fixture
def sample_config_file(temp_data_dir: Path, sample_material_config: dict) -> Path:
    """Write the sample material config to a temporary YAML file."""
    config_path = temp_data_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(sample_material_config, f)
    return config_path


def _generate_synthetic_tracking_data(
    n_particles: int,
    n_frames: int,
    material_type: str,
    mass_kg: float,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic particle tracking data with known physics properties.

    Generates:
    - Linear position (x, y, z) with drift and noise
    - Angular orientation (theta, phi, psi)
    - Known ground truth velocity/omega for verification if needed.

    Args:
        n_particles: Number of particles to simulate.
        n_frames: Number of time steps.
        material_type: Label for the material.
        mass_kg: Mass of the particle in kg.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: particle_id, timestamp, x, y, z, theta, phi, psi, material_type, mass_kg
    """
    np.random.seed(seed)

    timestamps = np.linspace(0, 1.0, n_frames)
    data = []

    for pid in range(n_particles):
        # Base position with drift
        x0 = np.random.uniform(-0.1, 0.1)
        y0 = np.random.uniform(-0.1, 0.1)
        z0 = np.random.uniform(-0.05, 0.05)

        # Add noise to simulate tracking error
        noise_scale = 1e-4

        for t_idx, t in enumerate(timestamps):
            # Simple kinematic model: x = x0 + v*t + noise
            # We simulate a driven system with some oscillation
            v_x = 0.05 * np.sin(2 * np.pi * 10 * t)
            v_y = 0.05 * np.cos(2 * np.pi * 10 * t)
            v_z = 0.02 * np.sin(2 * np.pi * 20 * t)

            x = x0 + v_x * t + np.random.normal(0, noise_scale)
            y = y0 + v_y * t + np.random.normal(0, noise_scale)
            z = z0 + v_z * t + np.random.normal(0, noise_scale)

            # Orientation (simple rotation)
            theta = 0.1 * np.sin(2 * np.pi * 5 * t)
            phi = 0.1 * np.cos(2 * np.pi * 5 * t)
            psi = 0.05 * np.sin(2 * np.pi * 15 * t)

            data.append({
                "particle_id": pid,
                "timestamp": t,
                "x": x,
                "y": y,
                "z": z,
                "theta": theta,
                "phi": phi,
                "psi": psi,
                "material_type": material_type,
                "mass_kg": mass_kg
            })

    return pd.DataFrame(data)


@pytest.fixture
def synthetic_tracking_csv(temp_data_dir: Path) -> Path:
    """
    Generate a synthetic particle tracking CSV file.

    Creates a file at: temp_data_dir/particles.csv
    Contains data for steel and polymer particles.
    """
    csv_path = temp_data_dir / "particles.csv"

    # Steel particles
    steel_df = _generate_synthetic_tracking_data(
        n_particles=5, n_frames=100,
        material_type="steel", mass_kg=0.01, seed=42
    )

    # Polymer particles
    poly_df = _generate_synthetic_tracking_data(
        n_particles=5, n_frames=100,
        material_type="polymer", mass_kg=0.005, seed=43
    )

    combined_df = pd.concat([steel_df, poly_df], ignore_index=True)
    combined_df.to_csv(csv_path, index=False)

    return csv_path


@pytest.fixture
def synthetic_driving_log(temp_data_dir: Path) -> Path:
    """
    Generate a synthetic driving signal log CSV.

    Creates a file at: temp_data_dir/driving_signal.csv
    Contains timestamp and driving frequency/amplitude.
    """
    csv_path = temp_data_dir / "driving_signal.csv"

    timestamps = np.linspace(0, 1.0, 100)
    # Simulate a driving frequency that changes (chirp) or stays constant
    # For simplicity, use a constant frequency with noise
    freq = 50.0  # Hz
    amplitude = 0.01

    data = []
    for t in timestamps:
        data.append({
            "timestamp": t,
            "driving_frequency_hz": freq,
            "driving_amplitude_m": amplitude + np.random.normal(0, 1e-5)
        })

    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)

    return csv_path


@pytest.fixture
def synthetic_data_pair(temp_data_dir: Path, synthetic_tracking_csv: Path, synthetic_driving_log: Path) -> dict:
    """Return paths to both synthetic tracking and driving data."""
    return {
        "tracking": synthetic_tracking_csv,
        "driving": synthetic_driving_log
    }


@pytest.fixture
def synthetic_missing_frame_csv(temp_data_dir: Path) -> Path:
    """
    Generate a synthetic CSV with intentional missing frames to test interpolation.

    Creates a file at: temp_data_dir/particles_missing.csv
    """
    csv_path = temp_data_dir / "particles_missing.csv"

    n_particles = 2
    n_frames_total = 50
    timestamps = np.linspace(0, 0.5, n_frames_total)

    data = []
    for pid in range(n_particles):
        x0 = 0.0
        for i, t in enumerate(timestamps):
            # Skip every 10th frame to simulate missing data
            if i % 10 == 0 and i > 0:
                continue

            x = x0 + 0.01 * t + np.random.normal(0, 1e-5)
            data.append({
                "particle_id": pid,
                "timestamp": t,
                "x": x,
                "y": 0.0,
                "z": 0.0,
                "theta": 0.0,
                "phi": 0.0,
                "psi": 0.0,
                "material_type": "steel",
                "mass_kg": 0.01
            })

    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)

    return csv_path


@pytest.fixture
def synthetic_no_z_csv(temp_data_dir: Path) -> Path:
    """
    Generate a synthetic CSV lacking the 'z' column to test pot_incomplete logic.

    Creates a file at: temp_data_dir/particles_no_z.csv
    """
    csv_path = temp_data_dir / "particles_no_z.csv"

    n_particles = 2
    n_frames = 50
    timestamps = np.linspace(0, 0.5, n_frames)

    data = []
    for pid in range(n_particles):
        for t in timestamps:
            data.append({
                "particle_id": pid,
                "timestamp": t,
                "x": 0.01 * t,
                "y": 0.0,
                # "z" column intentionally omitted
                "theta": 0.0,
                "phi": 0.0,
                "psi": 0.0,
                "material_type": "steel",
                "mass_kg": 0.01
            })

    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)

    return csv_path