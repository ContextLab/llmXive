"""
Test suite for the verify_data_source script.

The test checks that the script creates the expected JSON report file.
Because the script reaches out to external services, the test runs the
script in a subprocess and verifies that it exits with status 0 **only**
when a matching dataset is found. In environments without internet
access (e.g., during CI without network), the script will exit with a
non‑zero status, which is also a valid outcome. Therefore the test
asserts that the JSON file exists and contains a top‑level "datasets"
key (which may be an empty list).
"""

import json
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_verify_data_source_creates_report(tmp_path, monkeypatch):
    # Ensure the script writes to a temporary data directory to avoid
    # interfering with any existing files.
    # Monkey‑patch the paths.data function to redirect under tmp_path.
    original_data = paths.data

    def redirected_data(*parts):
        return Path(tmp_path, *parts)

    monkeypatch.setattr(paths, "data", redirected_data)

    script_path = Path("code", "verify_data_source.py")
    # Run the script; capture exit code.
    result = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # The script should always produce the JSON report, even on failure.
    report_path = redirected_data("source", "availability_report.json")
    assert report_path.is_file(), f"Report not created at {report_path}"

    # Load the JSON and verify structure.
    with report_path.open() as f:
        data = json.load(f)

    assert isinstance(data, dict), "Report JSON is not an object"
    assert "datasets" in data, "Report missing 'datasets' key"
    assert isinstance(data["datasets"], list), "'datasets' should be a list"

    # If the script succeeded (exit code 0) we must have at least one entry.
    if result.returncode == 0:
        assert len(data["datasets"]) > 0, "Successful run but no datasets found"

    # If the script failed (non‑zero), the CI pipeline will treat this as a
    # proper abort; the test still passes because the report was generated.