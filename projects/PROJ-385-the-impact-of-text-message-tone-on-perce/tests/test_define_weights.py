"""
Test for T090: Define cue-intensity weighting schemes.

This test runs the `code/00_define_weights.py` script and verifies that it creates
the expected JSON file with the exact weighting schemes required by the specification.
"""

import json
import subprocess
import sys
from pathlib import Path

# Import the project's configuration utilities to locate the processed data directory.
# The config module is part of the project's codebase and provides the path helpers.
from config import get_processed_data_dir


def _run_define_weights_script() -> subprocess.CompletedProcess:
    """
    Execute the `00_define_weights.py` script as a subprocess.

    Returns:
        subprocess.CompletedProcess: The result of the subprocess execution.
    """
    script_path = Path(__file__).resolve().parents[2] / "code" / "00_define_weights.py"
    # Ensure the script exists before attempting to run it.
    assert script_path.is_file(), f"Script not found at {script_path}"
    return subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_define_weights_creates_file():
    """
    Verify that running the weighting‑scheme script creates the JSON file with the
    exact expected content.
    """
    # Run the script.
    result = _run_define_weights_script()
    # The script should exit cleanly.
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Determine the expected output location.
    output_path = get_processed_data_dir() / "cue_intensity_weights.json"

    # The file must exist.
    assert output_path.is_file(), f"Expected output file not found: {output_path}"

    # Load and validate its contents.
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    expected = {
        "equal_weight": {"emoji": 0.333, "punctuation": 0.333, "length": 0.333},
        "emoji_dominant": {"emoji": 0.6, "punctuation": 0.2, "length": 0.2},
        "punctuation_dominant": {"emoji": 0.2, "punctuation": 0.6, "length": 0.2},
    }

    assert data == expected, f"Weighting schemes do not match expected values.\nGot: {data}\nExpected: {expected}"