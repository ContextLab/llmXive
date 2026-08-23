"""
Simple sanity test for the power‑analysis script.

The test runs the ``run_power_analysis.py`` script and checks that the expected
JSON file is created and contains the required keys.
"""

import json
from pathlib import Path
import subprocess
import sys

# Import the project configuration to locate the processed data directory
from config import get_processed_data_dir

def test_power_analysis_results_file():
    # Execute the script in a subprocess to emulate real‑world usage
    script_path = Path(__file__).resolve().parents[1] / "code" / "run_power_analysis.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify output file exists
    out_file = get_processed_data_dir() / "power_analysis_results.json"
    assert out_file.is_file(), f"{out_file} was not created"

    # Load and validate JSON contents
    data = json.loads(out_file.read_text())
    assert "estimated_power" in data, "Missing 'estimated_power' key"
    assert "target_N" in data, "Missing 'target_N' key"
    # Basic sanity checks on the values
    assert isinstance(data["estimated_power"], float), "'estimated_power' is not a float"
    assert 0.0 <= data["estimated_power"] <= 1.0, "'estimated_power' out of bounds"
    assert isinstance(data["target_N"], int), "'target_N' is not an int"
    assert data["target_N"] > 0, "'target_N' must be positive"