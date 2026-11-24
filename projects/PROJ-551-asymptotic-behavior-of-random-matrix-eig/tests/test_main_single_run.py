"""
Integration test for the single‑run mode of ``code/main.py``.

The test executes the script twice with identical arguments and verifies
that:

1. The JSON output file ``data/processed/single_run_results.json`` is
   created.
2. The file contains the required top‑level keys.
3. The list ``eigenvalues`` contains at least one entry.
4. The top eigenvalue (index 1) is reproducible to within 1e‑6 across
   independent runs, satisfying the deterministic reproducibility check
   required by task T001.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Path to the script under test
SCRIPT = Path(__file__).resolve().parents[2] / "code" / "main.py"
OUTPUT_JSON = Path(__file__).resolve().parents[2] / "data" / "processed" / "single_run_results.json"

@pytest.fixture(autouse=True)
def clean_output():
    """Remove any stale output before each test."""
    if OUTPUT_JSON.exists():
        OUTPUT_JSON.unlink()
    yield
    # Clean up after the test to keep the repository tidy
    if OUTPUT_JSON.exists():
        OUTPUT_JSON.unlink()

def run_main() -> Path:
    """Run ``code/main.py`` in single‑run mode and return the path to the JSON file."""
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--mode",
        "single",
        "--N",
        "1000",
        "--seed",
        "42",
        "--theta",
        "2.5",
        "--k",
        "1",
        "--pattern",
        "diagonal",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    # The script prints the JSON to stdout; we ignore it here.
    assert OUTPUT_JSON.exists(), f"Expected output file {OUTPUT_JSON} was not created."
    return OUTPUT_JSON

def test_single_run_creates_valid_json():
    """Execute the script once and validate the JSON structure."""
    json_path = run_main()
    data = json.loads(json_path.read_text())

    # Required top‑level keys (a subset sufficient for the test)
    required_keys = {
        "run_id",
        "timestamp",
        "seed",
        "N",
        "k",
        "theta",
        "pattern_type",
        "support_density",
        "computation_time_ms",
        "empirical_bulk_edge",
        "eigenvalues",
    }
    missing = required_keys - data.keys()
    assert not missing, f"Missing required keys in JSON output: {missing}"

    # ``eigenvalues`` must be a non‑empty list of dicts
    eigen_list = data["eigenvalues"]
    assert isinstance(eigen_list, list) and len(eigen_list) > 0, "Eigenvalue list is empty or not a list."

    # Each entry should contain the fields described in the contract
    entry_keys = {
        "run_id",
        "eigenvalue_index",
        "value",
        "is_outlier",
        "theoretical_bbp",
        "deviation",
    }
    for entry in eigen_list:
        missing_entry = entry_keys - entry.keys()
        assert not missing_entry, f"Eigenvalue entry missing keys: {missing_entry}"

def test_deterministic_reproducibility():
    """
    Run the script twice with the same arguments and ensure the top eigenvalue
    matches within 1e‑6.
    """
    json_path_1 = run_main()
    top1 = json.loads(json_path_1.read_text())["eigenvalues"][0]["value"]

    # Run a second time (the script overwrites the same file)
    json_path_2 = run_main()
    top2 = json.loads(json_path_2.read_text())["eigenvalues"][0]["value"]

    assert abs(top1 - top2) < 1e-6, f"Top eigenvalue not reproducible: {top1} vs {top2}"
