"""
Integration test for single GPE simulation run completion.

This test verifies that the split-step Fourier GPE solver can complete
a full simulation run for a single parameter set without numerical
instabilities or GPU errors, producing valid output files.

Task: T011 [US1]
"""

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from simulation.gpe_solver import run_gpe_simulation
from simulation.initial_conditions import create_thomas_fermi_initial
from config.grid_config import create_grid_config, get_grid_resolution
from utils.seed_manager import set_global_seed, initialize_random_state
from utils.io_helpers import save_array, load_array
from utils.logger import get_logger, configure_logging


@pytest.fixture(scope="module")
def test_config():
    """
    Create a minimal valid configuration for a single run test.
    Uses 64x64 grid as per T017b specification for full batch/verification.
    """
    # Set a fixed seed for reproducibility
    set_global_seed(42)
    initialize_random_state(42)

    # Define parameters for a stable-ish test case
    params = {
        "Omega": 0.5,           # Rotation frequency
        "epsilon_dd": 0.5,      # Dipolar interaction strength
        "N": 10000,             # Particle number (scaled)
        "a_s": 5.0,             # s-wave scattering length
        "grid_size": 64,        # 64x64 as per T017b for verification
        "L": 20.0,              # Domain size
        "dt": 0.001,            # Time step
        "max_time": 0.1,        # Short run time for CI limits
        "output_interval": 0.05,
    }

    # Create grid configuration
    config = create_grid_config(
        Nx=params["grid_size"],
        Ny=params["grid_size"],
        Lx=params["L"],
        Ly=params["L"],
        dt=params["dt"],
        max_time=params["max_time"],
    )

    return {
        "config": config,
        "params": params,
    }


@pytest.fixture(scope="module")
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_single_run_completes(test_config, temp_output_dir):
    """
    Integration test: test_single_run_completes

    Verifies that:
    1. The GPE solver runs to completion for a single parameter set.
    2. Output files (density and phase snapshots) are created.
    3. Output files contain valid numerical data (no NaNs/Infs).
    4. The final state is physically plausible (norm is preserved within tolerance).
    """
    config = test_config["config"]
    params = test_config["params"]
    output_dir = temp_output_dir

    logger = get_logger(__name__)
    logger.info(f"Starting single run integration test with Omega={params['Omega']}, "
                f"epsilon_dd={params['epsilon_dd']}, N={params['N']}")

    # 1. Generate initial condition
    psi_0 = create_thomas_fermi_initial(
        config,
        N=params["N"],
        a_s=params["a_s"],
        Omega=params["Omega"],
    )

    # Verify initial state is valid
    initial_norm = np.sum(np.abs(psi_0) ** 2) * (config.Lx * config.Ly) / (config.Nx * config.Ny)
    assert not np.isnan(initial_norm), "Initial condition contains NaN"
    assert initial_norm > 0.0, "Initial condition has zero norm"

    # 2. Run the simulation
    try:
        result = run_gpe_simulation(
            psi_0=psi_0,
            config=config,
            Omega=params["Omega"],
            epsilon_dd=params["epsilon_dd"],
            N=params["N"],
            a_s=params["a_s"],
            output_dir=str(output_dir),
            output_interval=params["output_interval"],
        )
    except Exception as e:
        logger.error(f"Simulation failed with exception: {e}")
        raise

    # 3. Verify output files exist
    expected_files = [
        "density_snapshot_0.npy",
        "phase_snapshot_0.npy",
        "density_snapshot_1.npy",
        "phase_snapshot_1.npy",
        "simulation_metadata.json",
    ]

    for fname in expected_files:
        fpath = output_dir / fname
        assert fpath.exists(), f"Expected output file {fname} was not created"

    # 4. Verify data integrity
    # Load first density snapshot
    dens_0 = load_array(str(output_dir / "density_snapshot_0.npy"))
    dens_1 = load_array(str(output_dir / "density_snapshot_1.npy"))

    assert dens_0 is not None, "Failed to load density snapshot 0"
    assert dens_1 is not None, "Failed to load density snapshot 1"

    # Check for NaNs/Infs
    assert not np.any(np.isnan(dens_0)), "Density snapshot 0 contains NaN"
    assert not np.any(np.isnan(dens_1)), "Density snapshot 1 contains NaN"
    assert not np.any(np.isinf(dens_0)), "Density snapshot 0 contains Inf"
    assert not np.any(np.isinf(dens_1)), "Density snapshot 1 contains Inf"

    # Check physical plausibility (density should be non-negative)
    assert np.all(dens_0 >= 0), "Density snapshot 0 contains negative values"
    assert np.all(dens_1 >= 0), "Density snapshot 1 contains negative values"

    # 5. Verify norm conservation (within tolerance for split-step method)
    norm_0 = np.sum(dens_0) * (config.Lx * config.Ly) / (config.Nx * config.Ny)
    norm_1 = np.sum(dens_1) * (config.Lx * config.Ly) / (config.Nx * config.Ny)

    # Allow 5% tolerance for numerical drift in short test
    tolerance = 0.05
    relative_change = abs(norm_1 - norm_0) / norm_0
    assert relative_change < tolerance, (
        f"Norm conservation violated: relative change {relative_change:.4f} > {tolerance}"
    )

    logger.info(
        f"Test passed: Single run completed successfully. "
        f"Initial norm: {norm_0:.4f}, Final norm: {norm_1:.4f}, "
        f"Relative change: {relative_change:.4f}"
    )

    # 6. Verify metadata file
    import json
    metadata_path = output_dir / "simulation_metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    assert "Omega" in metadata, "Metadata missing Omega"
    assert "epsilon_dd" in metadata, "Metadata missing epsilon_dd"
    assert metadata["Omega"] == params["Omega"], "Omega mismatch in metadata"
    assert metadata["epsilon_dd"] == params["epsilon_dd"], "epsilon_dd mismatch in metadata"

    logger.info("All integration checks passed for single run completion.")