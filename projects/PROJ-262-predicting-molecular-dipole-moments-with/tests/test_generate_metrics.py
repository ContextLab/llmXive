"""
tests/test_generate_metrics.py
------------------------------

Simple integration test for ``code/generate_metrics.py``.  The test invokes the
script via ``subprocess`` and checks that the expected CSV file is created
and contains the correct header row.

The test does **not** require actual model checkpoints – it works even when
the ``data/checkpoints`` directory is empty.  In that case the CSV will only
contain the header line.
"""

import csv
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.fixture(scope="function")
def clean_results_dir(tmp_path: Path):
    """
    Ensure a fresh ``results`` directory for each test run.
    """
    results_dir = Path("results")
    # Remove any stale results directory that might exist from previous runs.
    if results_dir.is_dir():
        for child in results_dir.iterdir():
            child.unlink()
        results_dir.rmdir()
    yield
    # Cleanup after test
    if results_dir.is_dir():
        for child in results_dir.iterdir():
            child.unlink()
        results_dir.rmdir()

def test_generate_metrics_creates_csv(clean_results_dir):
    """
    Run the script and verify that ``results/metrics.csv`` exists and has the
    correct header.
    """
    script_path = Path("code") / "generate_metrics.py"
    # Execute the script using the same interpreter that runs the tests.
    subprocess.check_call([sys.executable, str(script_path)])

    csv_path = Path("results") / "metrics.csv"
    assert csv_path.is_file(), "metrics.csv was not created"

    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["seed", "model_type", "MAE", "RMSE"], "CSV header is incorrect"

    # The file should contain at least the header line; additional rows are
    # optional depending on which checkpoints are present.
    # No further assertions are made to keep the test robust in environments
    # without trained models.