"""
Unit tests for the dataset verification script (T000).

The tests create temporary raw dataset files with various column
configurations and assert that the script produces the expected
JSON report and exit code.
"""

import os
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Helper to locate the script under the repository root
SCRIPT = Path("code/src/data/verify_dataset.py")

@pytest.fixture
def tmp_raw_dir(tmp_path):
    """Create a temporary data/raw directory and return its Path."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    return raw_dir

def run_script(tmp_path, extra_args=None):
    """
    Execute the verification script with the current Python interpreter.
    Returns (exit_code, stdout, stderr, report_path).
    """
    args = [sys.executable, str(SCRIPT)]
    if extra_args:
        args.extend(extra_args)

    # Ensure the project's path helpers resolve inside the temporary dir
    env = dict(**dict(os.environ), PYTHONPATH=str(Path.cwd()))
    proc = subprocess.run(
        args,
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    report_path = Path(tmp_path) / "data" / "results" / "dataset_verification.json"
    return proc.returncode, proc.stdout, proc.stderr, report_path

def test_all_columns_present(tmp_path, tmp_raw_dir):
    # Create a minimal CSV with all required columns
    csv_path = tmp_raw_dir / "games.csv"
    csv_path.write_text(
        "white_rating,black_rating,eco_code,move_times,outcome\\n"
        "1500,1600,A,0.5,1\\n"
    )
    # Run the script
    exit_code, out, err, report_path = run_script(tmp_path)
    assert exit_code == 0, f"Script failed: {err}"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["all_columns_present"] is True
    assert report["missing_columns"] == []

def test_missing_columns(tmp_path, tmp_raw_dir):
    # CSV missing 'move_times' and 'outcome'
    csv_path = tmp_raw_dir / "games.csv"
    csv_path.write_text(
        "white_rating,black_rating,eco_code\\n"
        "1500,1600,A\\n"
    )
    exit_code, out, err, report_path = run_script(tmp_path)
    assert exit_code == 1
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["all_columns_present"] is False
    # Order of missing columns is alphabetical due to `sorted` in script
    assert sorted(report["missing_columns"]) == ["move_times", "outcome"]

def test_no_dataset_file(tmp_path):
    # No raw dataset present in the temporary workspace
    exit_code, out, err, report_path = run_script(tmp_path)
    assert exit_code == 1
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["all_columns_present"] is False
    assert report["missing_columns"] == ["file_not_found"]