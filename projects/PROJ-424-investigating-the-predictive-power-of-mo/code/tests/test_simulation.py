"""
Smoke test for the simulation runner.

The test builds a tiny water box and runs a 1 ns production
simulation (≈5 ps per step with a 20 fs timestep → 50 000 steps).
It then checks that the expected ``.xtc`` trajectory and ``.log``
files have been created in ``data/raw/simulations``.
"""

import os
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from config import Solvent, DEFAULT_SIMULATION_CONFIG
from simulations.run_simulation import run_simulation

@pytest.mark.timeout(300)
def test_water_1ns_simulation():
    """Run a minimal water simulation and verify output files."""
    # Ensure a clean output directory
    out_dir = paths.data("raw", "simulations")
    if out_dir.exists():
        # Remove any leftover files from previous runs
        for f in out_dir.iterdir():
            if f.is_file():
                f.unlink()
    else:
        out_dir.mkdir(parents=True, exist_ok=True)

    result = run_simulation(
        Solvent.WATER,
        DEFAULT_SIMULATION_CONFIG,
        duration_ns=1.0,
        seed=0,
    )

    traj_path = Path(result["trajectory"])
    log_path = Path(result["log"])

    assert traj_path.exists(), f"Trajectory file missing: {traj_path}"
    assert log_path.exists(), f"Log file missing: {log_path}"

    # Basic sanity checks on file size (non‑empty)
    assert traj_path.stat().st_size > 0, "Trajectory file is empty"
    assert log_path.stat().st_size > 0, "Log file is empty"
