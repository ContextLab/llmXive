"""Basic sanity test that the report generation script runs without error.

The test does not validate the scientific content – it only checks that the
PDF file is created and is non‑empty. This ensures that the script can be
executed in the CI environment after the upstream data‑processing steps
have succeeded.
"""
import os
from pathlib import Path

import pytest

# Import the main function directly – this works because the module is
# located under ``code/`` which is on the Python path in the test runner.
from code._05_generate_report import generate_report  # type: ignore


@pytest.mark.integration
def test_report_is_created(tmp_path: Path, monkeypatch):
    # Ensure the output directory exists and is writable.
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Run the report generation – any exception will cause the test to fail.
    report_path = generate_report()

    assert report_path.is_file(), "Report PDF was not created."
    assert report_path.stat().st_size > 0, "Report PDF is empty."

    # Cleanup – not strictly required but keeps the workspace tidy.
    try:
        os.remove(report_path)
    except OSError:
        pass