import json
import os
from pathlib import Path

import pytest

# Import the main function from the script we just created
from data.run_md_sim import main as run_md_sim_main

def test_md_simulation_creates_outputs(tmp_path, monkeypatch):
    """
    Verify that the MD simulation script creates the expected
    trajectory directory and JSON log file without actually invoking
    LAMMPS. The script falls back to a dummy trajectory writer when LAMMPS
    is not present, which is sufficient for the verification step.
    """
    # Patch configuration to point to a temporary data directory
    from config import Config, PathConfig, reset_config

    # Build a minimal configuration object that mimics the real one
    class DummyPathConfig:
        def __init__(self, root):
            self.root = root
            self.data_raw = str(root / "data" / "raw")
            self.data_logs = str(root / "data" / "logs")

    dummy_root = tmp_path
    dummy_paths = DummyPathConfig(dummy_root)

    # Monkey‑patch the get_paths() function to return our dummy paths
    from config import get_paths
    monkeypatch.setattr('config.get_paths', lambda: dummy_paths)

    # Create the required pilot composition CSV
    pilot_dir = Path(dummy_paths.data_raw)
    pilot_dir.mkdir(parents=True, exist_ok=True)
    pilot_csv = pilot_dir / "pilot_compositions.csv"
    pilot_csv.write_text("composition_id\\ncomp_A\\ncomp_B\\ncomp_C\\n")

    # Run the script
    exit_code = run_md_sim_main()
    assert exit_code == 0

    # Check that trajectory files exist
    traj_dir = Path(dummy_paths.data_raw) / "md_trajectories"
    assert traj_dir.is_dir()
    for comp in ["comp_A", "comp_B", "comp_C"]:
        assert (traj_dir / f"{comp}.xyz").exists()

    # Check that the JSON log exists and has the right structure
    log_file = Path(dummy_paths.data_logs) / "simulation_times.json"
    assert log_file.is_file()
    data = json.load(open(log_file))
    assert "simulations" in data
    assert len(data["simulations"]) == 3
    for entry in data["simulations"]:
        assert entry["status"] in {"complete", "truncated", "failed"}
        assert isinstance(entry["duration_seconds"], float)

# Ensure the test runs in isolation and does not interfere with the real project files
# The monkeypatch of get_paths guarantees that the script writes to the temporary directory only.