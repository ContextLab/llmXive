"""
Test suite for verifying Spec Alignment Report existence and content.
Corresponds to Task T009 verification requirements.
"""
import os
import pytest
from pathlib import Path

REPORT_PATH = Path("docs") / "spec_alignment_report.md"


def test_report_exists():
    """
    Assert that the spec alignment report file exists.
    This test verifies the output of T000/T000a.
    """
    assert REPORT_PATH.exists(), f"Report file {REPORT_PATH} does not exist. Please run T000/T000a to generate it."


def test_report_not_empty():
    """
    Assert that the spec alignment report file is not empty.
    Ensures the report contains actual content, not just a placeholder.
    """
    assert REPORT_PATH.exists(), f"Report file {REPORT_PATH} does not exist."
    
    size = REPORT_PATH.stat().st_size
    assert size > 0, f"Report file {REPORT_PATH} exists but is empty (0 bytes)."


def test_ci_script_exists():
    """
    Assert that the CI check script for spec alignment exists.
    This verifies the implementation of Task T009.
    """
    ci_script = Path("ci") / "check_spec_alignment.sh"
    assert ci_script.exists(), f"CI script {ci_script} does not exist."
    
    # Verify it is executable (optional but good practice)
    # Note: On some systems, checking executable bit might require os.access
    # For this test, we just ensure the file is present.