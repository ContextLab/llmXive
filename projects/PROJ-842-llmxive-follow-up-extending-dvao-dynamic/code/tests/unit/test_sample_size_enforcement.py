"""
Unit test to verify the sample size enforcement logic (T062) via T064.

This test executes a controlled run with --num-runs=10 (below the FR-006 
threshold of 30) to verify that the check in T062 triggers correctly and 
the run aborts immediately.

It validates the "Fail Loudly" principle for statistical constraints.
"""
import pytest
import subprocess
import sys
import os
import re

def test_sample_size_enforcement_aborts_with_error():
    """
    Verify that running the suite with --num-runs=10 causes an immediate abort
    with exit code 1 and the specific error message "FR-006 Violation".
    """
    # Construct the command to run the runner with insufficient sample size
    cmd = [
        sys.executable,
        "src/environment/runner.py",
        "--num-runs=10",
        "--n-objectives=5",  # Provide a minimal valid N to reach the check
        "--seed=42"
    ]

    # Execute the command
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.getcwd()
    )

    # Assert exit code is 1 (failure)
    assert result.returncode == 1, (
        f"Expected exit code 1, but got {result.returncode}. "
        f"Stdout: {result.stdout}, Stderr: {result.stderr}"
    )

    # Assert the specific error message is present in stdout or stderr
    combined_output = result.stdout + result.stderr
    assert "FR-006 Violation" in combined_output, (
        f"Expected 'FR-006 Violation' in output, but got:\n"
        f"Stdout: {result.stdout}\n"
        f"Stderr: {result.stderr}"
    )

    # Optional: Verify the specific message format matches T062 spec
    expected_msg_pattern = r"FR-006 Violation: One-sample t-test requires n >= 30 runs"
    assert re.search(expected_msg_pattern, combined_output), (
        f"Expected specific FR-006 error message pattern, but got:\n"
        f"{combined_output}"
    )
