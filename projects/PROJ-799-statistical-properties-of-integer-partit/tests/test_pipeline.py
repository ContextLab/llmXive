"""
Pipeline integration and time-budget tests for PROJ-799.

This module contains tests that verify the entire pipeline executes within
the specified time budgets defined in SC-004.
"""

import os
import sys
import time
import subprocess
import tempfile
import pytest
from pathlib import Path

# Add the project root to the path so we can import from code/
# Assuming this file is at tests/test_pipeline.py
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

# Constants for time budgets (in seconds)
# Derived from SC-004 total budget of 6 hours (21600 seconds)
DP_PHASE_BUDGET = 1.5 * 3600  # 1.5 hours = 5400 seconds
MODELING_PHASE_BUDGET = 3.5 * 3600  # 3.5 hours = 12600 seconds
VISUALIZATION_PHASE_BUDGET = 1.0 * 3600  # 1 hour = 3600 seconds
TOTAL_PIPELINE_BUDGET = 6.0 * 3600  # 6 hours = 21600 seconds

# Expected output paths
PARTITIONS_RAW_CSV = project_root / "data" / "raw" / "partitions_raw.csv"
FEATURES_CSV = project_root / "data" / "processed" / "features.csv"
MODEL_RESULTS_JSON = project_root / "data" / "processed" / "model_results.json"
RESIDUAL_PNG = project_root / "data" / "processed" / "residual_convergence.png"


def run_script(script_name: str, args: list = None, timeout: int = None) -> tuple:
    """
    Run a Python script from the code/ directory.

    Args:
        script_name: Name of the script in code/ (e.g., 'generate_partitions.py')
        args: Optional list of command-line arguments
        timeout: Optional timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    script_path = code_dir / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(code_dir),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Script timed out after {timeout} seconds"


@pytest.mark.timeout(DP_PHASE_BUDGET)
def test_dp_phase_time_budget():
    """
    T010b: Verify that the DP generation phase completes within 1.5 hours.

    This test runs generate_partitions.py and ensures it finishes within
    the allocated time budget. The actual execution time is logged.
    """
    start_time = time.time()

    # Run the DP generation script
    returncode, stdout, stderr = run_script(
        "generate_partitions.py",
        timeout=int(DP_PHASE_BUDGET * 0.9)  # 90% of budget to allow for logging
    )

    elapsed_time = time.time() - start_time

    # Assert the script completed successfully
    assert returncode == 0, f"generate_partitions.py failed with code {returncode}\nStdout: {stdout}\nStderr: {stderr}"

    # Assert the output file was created
    assert PARTITIONS_RAW_CSV.exists(), f"Output file {PARTITIONS_RAW_CSV} was not created"

    # Log the actual time taken
    print(f"DP phase completed in {elapsed_time:.2f} seconds (budget: {DP_PHASE_BUDGET:.2f}s)")

    # Assert we are within budget (with a small margin for test overhead)
    assert elapsed_time < DP_PHASE_BUDGET, (
        f"DP phase took {elapsed_time:.2f}s, exceeding budget of {DP_PHASE_BUDGET:.2f}s"
    )


@pytest.mark.timeout(MODELING_PHASE_BUDGET)
def test_modeling_phase_time_budget():
    """
    T010c: Verify that the feature engineering and modeling phase completes within 3.5 hours.

    This test runs feature_engineering.py and regression_model.py sequentially
    and ensures the total time is within the allocated budget.
    """
    start_time = time.time()

    # Run feature engineering
    print("Running feature engineering...")
    returncode, stdout, stderr = run_script(
        "feature_engineering.py",
        timeout=int(MODELING_PHASE_BUDGET * 0.4)  # Allocate 40% of budget
    )
    assert returncode == 0, f"feature_engineering.py failed\nStdout: {stdout}\nStderr: {stderr}"
    assert FEATURES_CSV.exists(), f"Output file {FEATURES_CSV} was not created"

    # Run regression model
    print("Running regression model...")
    returncode, stdout, stderr = run_script(
        "regression_model.py",
        timeout=int(MODELING_PHASE_BUDGET * 0.5)  # Allocate 50% of budget
    )
    assert returncode == 0, f"regression_model.py failed\nStdout: {stdout}\nStderr: {stderr}"
    assert MODEL_RESULTS_JSON.exists(), f"Output file {MODEL_RESULTS_JSON} was not created"

    elapsed_time = time.time() - start_time

    # Log the actual time taken
    print(f"Modeling phase completed in {elapsed_time:.2f} seconds (budget: {MODELING_PHASE_BUDGET:.2f}s)")

    # Assert we are within budget
    assert elapsed_time < MODELING_PHASE_BUDGET, (
        f"Modeling phase took {elapsed_time:.2f}s, exceeding budget of {MODELING_PHASE_BUDGET:.2f}s"
    )


@pytest.mark.timeout(VISUALIZATION_PHASE_BUDGET)
def test_visualization_phase_time_budget():
    """
    T010d: Verify that the visualization phase (US3) completes within 1 hour.

    This test runs visualize_results.py and ensures it finishes within
    the allocated time budget of 1 hour (3600 seconds).
    The visualization phase depends on the output from US2 (model_results.json).
    """
    start_time = time.time()

    # Verify prerequisite data exists
    assert MODEL_RESULTS_JSON.exists(), (
        f"Prerequisite file {MODEL_RESULTS_JSON} not found. "
        "Run US2 tasks (feature_engineering.py and regression_model.py) first."
    )

    # Run the visualization script
    print("Running visualization phase...")
    returncode, stdout, stderr = run_script(
        "visualize_results.py",
        timeout=int(VISUALIZATION_PHASE_BUDGET * 0.9)  # 90% of budget
    )

    elapsed_time = time.time() - start_time

    # Assert the script completed successfully
    assert returncode == 0, (
        f"visualize_results.py failed with code {returncode}\n"
        f"Stdout: {stdout}\n"
        f"Stderr: {stderr}"
    )

    # Assert the output file was created
    assert RESIDUAL_PNG.exists(), f"Output file {RESIDUAL_PNG} was not created"

    # Log the actual time taken
    print(f"Visualization phase completed in {elapsed_time:.2f} seconds (budget: {VISUALIZATION_PHASE_BUDGET:.2f}s)")

    # Assert we are within budget (with a small margin for test overhead)
    assert elapsed_time < VISUALIZATION_PHASE_BUDGET, (
        f"Visualization phase took {elapsed_time:.2f}s, exceeding budget of {VISUALIZATION_PHASE_BUDGET:.2f}s"
    )


@pytest.mark.timeout(TOTAL_PIPELINE_BUDGET)
def test_full_pipeline_time_budget():
    """
    T023b: Verify total pipeline (DP + Model + Plot) completes within 6 hours.

    This test runs the entire pipeline sequentially and ensures the total
    execution time does not exceed the 6-hour budget defined in SC-004.
    """
    start_time = time.time()

    # Run DP phase
    print("=== Running DP Phase ===")
    returncode, _, stderr = run_script(
        "generate_partitions.py",
        timeout=int(DP_PHASE_BUDGET * 0.9)
    )
    assert returncode == 0, f"DP phase failed: {stderr}"

    # Run Modeling phase
    print("=== Running Modeling Phase ===")
    returncode, _, stderr = run_script(
        "feature_engineering.py",
        timeout=int(MODELING_PHASE_BUDGET * 0.4)
    )
    assert returncode == 0, f"Feature engineering failed: {stderr}"

    returncode, _, stderr = run_script(
        "regression_model.py",
        timeout=int(MODELING_PHASE_BUDGET * 0.5)
    )
    assert returncode == 0, f"Regression modeling failed: {stderr}"

    # Run Visualization phase
    print("=== Running Visualization Phase ===")
    returncode, _, stderr = run_script(
        "visualize_results.py",
        timeout=int(VISUALIZATION_PHASE_BUDGET * 0.9)
    )
    assert returncode == 0, f"Visualization failed: {stderr}"

    elapsed_time = time.time() - start_time

    # Log the actual time taken
    print(f"Full pipeline completed in {elapsed_time:.2f} seconds (budget: {TOTAL_PIPELINE_BUDGET:.2f}s)")

    # Assert we are within total budget
    assert elapsed_time < TOTAL_PIPELINE_BUDGET, (
        f"Full pipeline took {elapsed_time:.2f}s, exceeding total budget of {TOTAL_PIPELINE_BUDGET:.2f}s"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])