"""
Integration test for the Primary Simulation Sweep.

The test runs the `code/run_primary_sweep.py` script and
asserts that the required artifacts exist and meet the
minimal size constraints.
"""

import json
from pathlib import Path

def test_primary_sweep_produces_expected_output(tmp_path, monkeypatch):
    """
    Execute the sweep script and verify outputs.

    The test uses the repository's working directory, so we
    simply invoke the script via a subprocess. After it
    finishes, we check that:
      1. `data/results/simulation_raw.json` exists.
      2. It contains at least 2 500 replicate entries.
      3. `data/results/runtime_logs.txt` exists and records
         an elapsed time field.
    """
    import subprocess
    import sys

    # Run the sweep script.
    script_path = Path("code") / "run_primary_sweep.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Sweep script failed: {result.stderr}"

    # Verify simulation output.
    sim_path = Path("data") / "results" / "simulation_raw.json"
    assert sim_path.is_file(), "simulation_raw.json not created"

    with sim_path.open("r", encoding="utf-8") as f:
        sim_data = json.load(f)

    replicates = sim_data.get("replicates", [])
    assert isinstance(replicates, list), "replicates field missing or malformed"
    assert len(replicates) >= 2500, f"Insufficient replicates: {len(replicates)}"

    # Verify runtime log.
    log_path = Path("data") / "results" / "runtime_logs.txt"
    assert log_path.is_file(), "runtime_logs.txt not created"
    with log_path.open("r", encoding="utf-8") as f:
        log = json.load(f)
    assert "elapsed_seconds" in log, "Runtime log missing elapsed_seconds"
    # The actual duration is environment‑dependent; we only assert that the key exists.