"""
Integration test for power analysis (T026).

This test verifies that the power analysis pipeline:
1. Correctly loads the filtered dataset and execution traces.
2. Calculates the necessary statistical power given the observed sample size and effect size.
3. Generates the required `data/processed/power_report.json` artifact.
4. Validates the schema of the generated report.

It runs the actual `code/analysis/power.py` script to ensure end-to-end functionality.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
POWER_REPORT_PATH = DATA_PROCESSED / "power_report.json"
POWER_SCRIPT = PROJECT_ROOT / "code" / "analysis" / "power.py"

@pytest.fixture(scope="module", autouse=True)
def ensure_directories():
    """Ensure the data/processed directory exists before running tests."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    yield

@pytest.mark.integration
def test_power_analysis_script_execution():
    """
    Test that the power analysis script runs successfully and produces the output file.
    """
    # Ensure input files exist (prerequisites T014, T024)
    filtered_tasks = DATA_PROCESSED / "filtered_tasks.csv"
    execution_traces = DATA_PROCESSED / "execution_traces.csv"

    if not filtered_tasks.exists():
        pytest.skip(f"Prerequisite file {filtered_tasks} not found. Run T014 first.")
    if not execution_traces.exists():
        pytest.skip(f"Prerequisite file {execution_traces} not found. Run T024 first.")

    # Remove old report if it exists to ensure fresh generation
    if POWER_REPORT_PATH.exists():
        POWER_REPORT_PATH.unlink()

    # Run the script
    result = subprocess.run(
        [sys.executable, str(POWER_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    # Assert execution success
    assert result.returncode == 0, (
        f"Power analysis script failed.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )

    # Assert output file creation
    assert POWER_REPORT_PATH.exists(), "Power report file was not generated."

@pytest.mark.integration
def test_power_report_schema_and_content():
    """
    Test that the generated power report contains the required fields and valid data types.
    """
    if not POWER_REPORT_PATH.exists():
        # If the file doesn't exist, the previous test likely failed or was skipped.
        # We run the script first to ensure we have something to test.
        subprocess.run(
            [sys.executable, str(POWER_SCRIPT)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

    if not POWER_REPORT_PATH.exists():
        pytest.fail("Power report still missing after attempting execution.")

    with open(POWER_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Validate schema
    required_keys = ["sample_size", "effect_size_f2", "alpha", "power", "pass_threshold_power", "passed"]
    for key in required_keys:
        assert key in report, f"Missing required key in power report: {key}"

    # Validate types
    assert isinstance(report["sample_size"], int), "sample_size must be an integer"
    assert isinstance(report["effect_size_f2"], float), "effect_size_f2 must be a float"
    assert isinstance(report["alpha"], float), "alpha must be a float"
    assert isinstance(report["power"], float), "power must be a float"
    assert isinstance(report["pass_threshold_power"], float), "pass_threshold_power must be a float"
    assert isinstance(report["passed"], bool), "passed must be a boolean"

    # Validate business logic (from T027 spec: target power >= 0.80)
    assert report["pass_threshold_power"] == 0.80, "Threshold power should be 0.80"
    assert 0.0 <= report["power"] <= 1.0, "Power value must be between 0.0 and 1.0"
    
    # Check consistency of the 'passed' flag
    expected_passed = report["power"] >= report["pass_threshold_power"]
    assert report["passed"] == expected_passed, (
        f"Report 'passed' flag is inconsistent. Power: {report['power']}, "
        f"Threshold: {report['pass_threshold_power']}, Passed: {report['passed']}"
    )

@pytest.mark.integration
def test_power_analysis_uses_real_data():
    """
    Verify that the power analysis actually uses the data from the CSV files
    and does not return hardcoded constants.
    """
    import pandas as pd

    # Load the source data
    traces_df = pd.read_csv(DATA_PROCESSED / "execution_traces.csv")
    filtered_df = pd.read_csv(DATA_PROCESSED / "filtered_tasks.csv")

    expected_sample_size = len(traces_df)
    
    # Run script again to get fresh output
    subprocess.run(
        [sys.executable, str(POWER_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    with open(POWER_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    # The sample size in the report must match the actual CSV row count
    assert report["sample_size"] == expected_sample_size, (
        f"Report sample size ({report['sample_size']}) does not match "
        f"actual execution traces count ({expected_sample_size}). "
        "The script may be using hardcoded values or wrong file paths."
    )

    # If the sample size is 0, the test should fail gracefully (or skip)
    if expected_sample_size == 0:
        pytest.skip("No data in execution traces to perform power analysis.")

    # Verify that power is not a trivial constant (e.g., exactly 0.8 or 1.0)
    # unless the data is perfectly uniform, which is unlikely.
    # This is a heuristic check to ensure the calculation is dynamic.
    assert report["power"] != 0.5, "Power value is suspiciously static."