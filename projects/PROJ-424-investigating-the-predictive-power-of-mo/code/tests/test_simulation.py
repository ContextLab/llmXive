"""
Smoke test for the simulation runner.
"""
import pytest
from pathlib import Path
from llmxive_toolkit import paths
from config import Solvent, DEFAULT_SIMULATION_CONFIG
from simulations.run_simulation import run_simulation

@pytest.mark.timeout(300)
def test_water_smoke_simulation():
    """Run a minimal water simulation and verify that trajectory and log files are created."""
    # Use a very short duration (10 ps) to keep the test fast
    duration_ns = 0.01  # 10 ps

    result = run_simulation(
        Solvent.WATER,
        DEFAULT_SIMULATION_CONFIG,
        duration_ns=duration_ns,
        seed=42,
    )

    traj_path = Path(result["trajectory"])
    log_path = Path(result["log"])

    assert traj_path.exists(), f"XTC trajectory missing: {traj_path}"
    assert log_path.exists(), f"Log file missing: {log_path}"
    assert traj_path.stat().st_size > 0, "XTC file is empty"
    assert log_path.stat().st_size > 0, "Log file is empty"