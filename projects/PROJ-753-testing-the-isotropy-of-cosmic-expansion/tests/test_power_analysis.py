import json
import subprocess
import sys
from pathlib import Path

import pytest

# Helper to run the power analysis script
def run_power_analysis(tmp_path: Path):
    # Ensure the script runs with default arguments
    result = subprocess.run(
        [sys.executable, "code/power_analysis.py"],
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )
    return result

def test_power_analysis_execution(tmp_path: Path):
    """The script should exit cleanly and produce the expected JSON file."""
    result = run_power_analysis(tmp_path)
    # The script must exit with status 0
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    # Verify that the output file exists
    power_json_path = Path(__file__).parents[2] / "data" / "processed" / "power_analysis.json"
    assert power_json_path.is_file(), "power_analysis.json was not created"
    # Load and check essential keys
    with open(power_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    required_keys = {
        "dataset_version",
        "source_url",
        "sha256",
        "analytic_min_detectable_dipole_mag",
        "empirical_power",
        "min_detectable_dipole_mag",
        "num_mocks",
        "num_supernovae",
        "typical_muerr",
    }
    assert required_keys.issubset(data.keys()), "Missing expected keys in power_analysis.json"
    # Basic sanity checks on numeric values
    assert data["num_supernovae"] > 0, "No supernovae were processed"
    assert 0.0 <= data["empirical_power"] <= 1.0, "Empirical power out of bounds"
    assert data["analytic_min_detectable_dipole_mag"] > 0.0, "Analytic dipole amplitude should be positive"