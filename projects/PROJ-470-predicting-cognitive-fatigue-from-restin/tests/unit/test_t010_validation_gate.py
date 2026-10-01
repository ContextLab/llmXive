"""
Test for T010: Data Validation Gate.
Verifies that T009 completed successfully and generated the required validation artifacts.
"""
import json
import os
import pytest
from pathlib import Path

# Project root relative to tests/unit
PROJECT_ROOT = Path(__file__).parent.parent.parent
VALIDATION_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "validation_report.json"


def test_validation_report_exists():
    """Assert that the validation report file exists."""
    assert VALIDATION_REPORT_PATH.exists(), (
        "Validation report missing: T009 failed. "
        f"Expected file at {VALIDATION_REPORT_PATH}"
    )


def test_validation_report_structure():
    """Assert that the report contains the expected keys and valid data."""
    if not VALIDATION_REPORT_PATH.exists():
        pytest.skip("Validation report missing, skipping structure check.")

    with open(VALIDATION_REPORT_PATH, "r") as f:
        report = json.load(f)

    # Check required keys
    required_keys = ["n_participants", "variables_found", "status"]
    for key in required_keys:
        assert key in report, f"Missing required key '{key}' in validation report."

    # Check data types and validity
    assert isinstance(report["n_participants"], int), "n_participants must be an integer."
    assert report["n_participants"] >= 30, (
        f"Sample size N ({report['n_participants']}) is less than 30. "
        "Task T009 should have failed earlier."
    )

    assert isinstance(report["variables_found"], list), "variables_found must be a list."
    assert len(report["variables_found"]) > 0, "variables_found cannot be empty."

    assert report["status"] == "success", (
        f"Validation report status is '{report['status']}', expected 'success'. "
        "T009 may have failed."
    )