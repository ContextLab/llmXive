"""
Unit tests for the scaling simulation portion of ``run_experiment.py``.
The test verifies that the script creates the expected CSV files and
that a scaling plot PDF is generated without raising exceptions.

The test runs the script in a temporary directory to avoid polluting the
repository's real results folder.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# The script under test
SCRIPT = Path(__file__).resolve().parents[2] / "run_experiment.py"


@pytest.fixture(scope="function")
def temp_results_dir(tmp_path_factory):
    """Create a temporary results directory for the duration of the test."""
    dir_path = tmp_path_factory.mktemp("results")
    yield dir_path
    # Cleanup is automatic via the pytest tmp_path fixture


def test_scaling_simulation_creates_outputs(temp_results_dir):
    """
    Execute the scaling mode (agent counts 3,5,7) and assert that the three
    CSV files and the PDF plot are written.
    """
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--agent_counts",
        "3,5,7",
        "--games",
        "10",  # tiny number for a fast test run
        "--output_dir",
        str(temp_results_dir),
    ]

    # Run the script; any non‑zero exit status fails the test.
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected output files
    expected_csvs = [
        temp_results_dir / "results_scaling_3.csv",
        temp_results_dir / "results_scaling_5.csv",
        temp_results_dir / "results_scaling_7.csv",
    ]
    for csv_path in expected_csvs:
        assert csv_path.is_file(), f"Missing CSV: {csv_path}"

    pdf_path = temp_results_dir / "scaling_plot.pdf"
    assert pdf_path.is_file(), "Missing scaling_plot.pdf"