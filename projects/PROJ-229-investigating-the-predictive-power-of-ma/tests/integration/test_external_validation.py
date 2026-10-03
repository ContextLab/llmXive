"""
Integration test for the external validation script (T023).

The test runs the script and checks that the expected JSON report is
produced with the required fields.
"""

import json
from pathlib import Path

import pytest

# Import the script's main function directly
from code.validate.validate_external import main as validate_external_main

@pytest.mark.integration
def test_external_validation_produces_report(tmp_path, monkeypatch):
    """
    Run the external validation script and verify that
    ``validation_report.json`` exists and contains the expected keys.
    """
    # Ensure the data files exist – use the real repository files.
    # The test relies on the repository's existing ``literature_pcms_raw.csv``
    # and ``chemical_similarity_report.json`` (if present). If they are missing,
    # the script will raise an error, causing the test to fail – this is
    # intentional because the task requires real data.
    report_path = Path("data/results/validation_report.json")
    if report_path.is_file():
        report_path.unlink()  # Remove any stale report

    # Run the script
    validate_external_main()

    # Verify the report was created
    assert report_path.is_file(), "validation_report.json was not created"

    # Load and check JSON structure
    with report_path.open("r", encoding="utf-8") as f:
        report = json.load(f)

    expected_keys = {
        "total_records",
        "records_with_melting_point",
        "ranking_accuracy",
        "similarity_warning",
    }
    assert expected_keys.issubset(report.keys()), "Missing expected keys in report"

    # Basic sanity checks on values
    assert isinstance(report["total_records"], int) and report["total_records"] >= 0
    assert isinstance(report["records_with_melting_point"], int)
    assert isinstance(report["ranking_accuracy"], float)
    assert 0.0 <= report["ranking_accuracy"] <= 1.0
    assert isinstance(report["similarity_warning"], bool)