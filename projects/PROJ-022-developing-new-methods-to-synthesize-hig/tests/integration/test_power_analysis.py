"""
Integration test for power analysis report generation (T028).

This test verifies that the power analysis script:
1. Successfully executes without error.
2. Generates the required output file at data/reports/power_analysis_report.json.
3. Produces a valid JSON structure with expected keys (sample_size, power, alpha, effect_size, standard_deviation).
4. Validates that the calculated effect size is a reasonable positive float.
"""
import os
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# Define paths relative to the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "code" / "screening" / "power_analysis.py"
OUTPUT_PATH = PROJECT_ROOT / "data" / "reports" / "power_analysis_report.json"


@pytest.fixture(autouse=True)
def setup_environment():
    """Ensure the output directory exists before the test runs."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Ensure the script exists
    if not SCRIPT_PATH.exists():
        pytest.fail(f"Script not found at {SCRIPT_PATH}. Ensure T033 is implemented or this script is created as part of this task.")
    yield
    # Cleanup is optional for integration tests, but we can remove the output if desired.
    # For this test, we verify the file was created.


def test_power_analysis_report_generation():
    """
    Integration test: Run the power analysis script and verify the output report.
    """
    # Ensure the output file does not exist before running (clean state)
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

    # Run the script
    # We use the project's python environment
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    # Assert script execution was successful
    assert result.returncode == 0, (
        f"Script execution failed with code {result.returncode}.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Assert the output file was created
    assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} was not created."

    # Load and validate the JSON content
    with open(OUTPUT_PATH, 'r') as f:
        report = json.load(f)

    # Validate structure and content
    required_keys = ['sample_size', 'power', 'alpha', 'effect_size', 'standard_deviation']
    for key in required_keys:
        assert key in report, f"Missing required key '{key}' in power analysis report."

    # Validate types and values
    assert isinstance(report['sample_size'], int), "sample_size must be an integer."
    assert report['sample_size'] == 30, f"Expected sample_size=30, got {report['sample_size']}."

    assert isinstance(report['power'], float), "power must be a float."
    assert report['power'] == 0.8, f"Expected power=0.8, got {report['power']}."

    assert isinstance(report['alpha'], float), "alpha must be a float."
    assert report['alpha'] == 0.05, f"Expected alpha=0.05, got {report['alpha']}."

    assert isinstance(report['effect_size'], float), "effect_size must be a float."
    assert report['effect_size'] > 0, f"effect_size must be positive, got {report['effect_size']}."

    assert isinstance(report['standard_deviation'], float), "standard_deviation must be a float."
    assert report['standard_deviation'] > 0, "standard_deviation must be positive."

    # Optional: Verify the logic consistency (Effect Size = (Mean1 - Mean2) / StdDev)
    # Since we don't have the means, we just verify the formula holds if we assume a detectable difference.
    # The script should have calculated this based on the inputs.
    # We assert that the file is valid JSON and contains the expected data.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])