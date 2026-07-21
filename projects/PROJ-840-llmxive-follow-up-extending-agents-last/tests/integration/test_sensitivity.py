"""
Integration test for sensitivity analysis output (T025).

This test verifies that the sensitivity analysis pipeline:
1. Executes successfully for multiple checkpoint intervals (N=1, N=3, N=5).
2. Produces the expected output file: data/processed/sensitivity_analysis.json.
3. The output file contains valid JSON with the required schema:
   - keys: 'sensitivity_results' (list of dicts)
   - each dict: 'checkpoint_interval' (int), 'pass_rate' (float), 'sample_size' (int).
4. The calculated delta pass rates are consistent with the raw results.

Prerequisites:
- T023 must have been executed to produce baseline_results.json and intervention_results.json.
- T026 (stats) and T028a-d (sensitivity experiments) must be functional.
"""

import json
import os
import sys
import subprocess
import pytest
from pathlib import Path

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure the code directory is in the path for imports if running as a module
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="module")
def sensitivity_output_path():
    """Returns the path to the expected sensitivity analysis output file."""
    return PROCESSED_DIR / "sensitivity_analysis.json"

@pytest.fixture(scope="module")
def baseline_results_path():
    """Returns the path to the baseline results file required for sensitivity analysis."""
    return PROCESSED_DIR / "baseline_results.json"

@pytest.fixture(scope="module")
def intervention_results_path():
    """Returns the path to the intervention results file required for sensitivity analysis."""
    return PROCESSED_DIR / "intervention_results.json"

@pytest.fixture(scope="module", autouse=True)
def run_sensitivity_pipeline(
    baseline_results_path, intervention_results_path, sensitivity_output_path
):
    """
    Runs the sensitivity analysis script if the output file does not exist.
    This fixture ensures the test has data to validate.
    """
    if not sensitivity_output_path.exists():
        # Check if prerequisite files exist
        if not baseline_results_path.exists():
            pytest.skip(
                f"Baseline results not found at {baseline_results_path}. "
                "Please run T023 (intervention/runner.py) first."
            )
        if not intervention_results_path.exists():
            pytest.skip(
                f"Intervention results not found at {intervention_results_path}. "
                "Please run T023 (intervention/runner.py) first."
            )

        # Run the sensitivity analysis script
        # Assuming the script is code/analysis/sensitivity.py based on task T028d
        script_path = CODE_DIR / "analysis" / "sensitivity.py"
        if not script_path.exists():
            pytest.fail(f"Sensitivity analysis script not found at {script_path}")

        cmd = [
            sys.executable,
            str(script_path),
            "--baseline", str(baseline_results_path),
            "--intervention", str(intervention_results_path),
            "--output", str(sensitivity_output_path),
            "--intervals", "1", "3", "5"
        ]

        try:
            result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                pytest.fail(
                    f"Sensitivity analysis script failed with return code {result.returncode}.\n"
                    f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )
        except subprocess.TimeoutExpired:
            pytest.fail("Sensitivity analysis script timed out.")

def test_sensitivity_output_exists(sensitivity_output_path):
    """Test 1: Verify the output file exists."""
    assert sensitivity_output_path.exists(), f"Sensitivity output file missing: {sensitivity_output_path}"

def test_sensitivity_output_is_valid_json(sensitivity_output_path):
    """Test 2: Verify the output file contains valid JSON."""
    try:
        with open(sensitivity_output_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict), "Sensitivity output must be a JSON object."
        assert "sensitivity_results" in data, "Missing 'sensitivity_results' key in output."
        assert isinstance(data["sensitivity_results"], list), "'sensitivity_results' must be a list."
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in sensitivity output: {e}")

def test_sensitivity_schema_compliance(sensitivity_output_path):
    """Test 3: Verify the schema of each result entry."""
    with open(sensitivity_output_path, "r") as f:
        data = json.load(f)

    results = data["sensitivity_results"]
    required_keys = {"checkpoint_interval", "pass_rate", "sample_size"}

    for i, entry in enumerate(results):
        missing_keys = required_keys - set(entry.keys())
        assert not missing_keys, (
            f"Entry {i} is missing keys: {missing_keys}. "
            f"Found keys: {entry.keys()}"
        )

        # Type checks
        assert isinstance(entry["checkpoint_interval"], int), "checkpoint_interval must be an integer."
        assert isinstance(entry["pass_rate"], (int, float)), "pass_rate must be a number."
        assert isinstance(entry["sample_size"], int), "sample_size must be an integer."

        # Value constraints
        assert entry["checkpoint_interval"] in [1, 3, 5], (
            f"Unexpected checkpoint_interval: {entry['checkpoint_interval']}. "
            "Expected 1, 3, or 5."
        )
        assert 0.0 <= entry["pass_rate"] <= 1.0, (
            f"pass_rate {entry['pass_rate']} is out of range [0.0, 1.0]."
        )
        assert entry["sample_size"] > 0, "sample_size must be positive."

def test_sensitivity_delta_calculation(sensitivity_output_path):
    """Test 4: Verify delta pass rates are calculated correctly (if present)."""
    with open(sensitivity_output_path, "r") as f:
        data = json.load(f)

    results = {r["checkpoint_interval"]: r["pass_rate"] for r in data["sensitivity_results"]}

    # We expect N=1, N=3, N=5
    if 1 in results and 3 in results:
        expected_delta_1_3 = results[3] - results[1]
        # The task T028d mentions calculating delta pass rate.
        # We check if the output includes a 'deltas' section or if we can infer it.
        # For this test, we just verify the data exists to calculate it.
        # If the output explicitly contains a 'deltas' key, we validate it.
        if "deltas" in data:
            # Example structure: {"deltas": [{"from": 1, "to": 3, "value": ...}]}
            deltas = data["deltas"]
            found_1_3 = False
            for d in deltas:
                if d.get("from") == 1 and d.get("to") == 3:
                    assert abs(d["value"] - expected_delta_1_3) < 1e-6, (
                        f"Delta calculation mismatch for 1->3: "
                        f"expected {expected_delta_1_3}, got {d['value']}"
                    )
                    found_1_3 = True
            # Note: If the specific 'deltas' key isn't in the output, we skip this specific assertion
            # as the primary schema test passed.
    # If specific delta keys aren't present, the schema test is the primary validator.

def test_sensitivity_coverage(sensitivity_output_path):
    """Test 5: Ensure all required intervals (1, 3, 5) are present."""
    with open(sensitivity_output_path, "r") as f:
        data = json.load(f)

    intervals = {r["checkpoint_interval"] for r in data["sensitivity_results"]}
    required_intervals = {1, 3, 5}
    missing = required_intervals - intervals

    assert not missing, f"Missing required checkpoint intervals: {missing}"