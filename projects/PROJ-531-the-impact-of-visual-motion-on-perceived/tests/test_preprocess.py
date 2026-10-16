"""
Integration test for the T004 preprocessing script.

The test runs the `code/preprocess.py` script and checks that the expected
output files exist and contain a plausible number of rows (≥ 100) as required
by SC‑001.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.fixture(scope="module")
def run_preprocess():
    """Execute the preprocessing script once for the test module."""
    script_path = Path("code", "preprocess.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Preprocess script failed:\n{result.stderr}"
    return result

def test_output_files_exist(run_preprocess):
    """Check that the required output files were created."""
    csv_path = Path("data", "processed", "analysis_ready.csv")
    json_path = Path("data", "processed", "preprocess_report.json")
    assert csv_path.is_file(), "analysis_ready.csv was not created"
    assert json_path.is_file(), "preprocess_report.json was not created"

def test_row_count_meets_requirement(run_preprocess):
    """The cleaned dataset must contain at least 100 complete rows."""
    csv_path = Path("data", "processed", "analysis_ready.csv")
    df = __import__("pandas").read_csv(csv_path)
    assert len(df) >= 100, f"Expected ≥100 rows after cleaning, got {len(df)}"

def test_report_contains_expected_keys(run_preprocess):
    """The JSON report should contain the defined keys."""
    json_path = Path("data", "processed", "preprocess_report.json")
    with json_path.open("r", encoding="utf-8") as f:
        report = json.load(f)
    for key in [
        "total_rows_raw",
        "rows_after_missing_drop",
        "lead_time_derived",
        "lead_time_rows",
        "timestamp",
    ]:
        assert key in report, f"Missing key '{key}' in preprocess_report.json"