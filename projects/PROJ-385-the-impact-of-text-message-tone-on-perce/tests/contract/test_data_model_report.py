"""
Contract test for T004: Data Model Validation.

Verifies that code/verify_data_model.py runs successfully and generates
the expected report file with correct content.
"""

import os
import sys
import subprocess
import pytest
from pathlib import Path

# Add code directory to path for imports if running directly,
# but primarily we test the script execution.
CODE_DIR = Path(__file__).parent.parent.parent / "code"


def test_data_model_report_generation():
    """
    Runs verify_data_model.py and checks that:
    1. The script exits with code 0 (success).
    2. The report file exists at data/validation/data_model_report.txt.
    3. The report contains "Status: PASSED".
    """
    script_path = CODE_DIR / "verify_data_model.py"
    assert script_path.exists(), f"Script not found: {script_path}"

    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )

    # Assert exit code
    assert result.returncode == 0, (
        f"Script failed with code {result.returncode}\n"
        f"Stdout: {result.stdout}\n"
        f"Stderr: {result.stderr}"
    )

    # Check report existence
    report_path = Path("data/validation/data_model_report.txt")
    assert report_path.exists(), f"Report file not generated: {report_path}"

    # Check content
    content = report_path.read_text()
    assert "Status: PASSED" in content, (
        f"Validation did not pass. Report content:\n{content}"
    )
    assert "Stimulus" in content, "Report missing Stimulus entity check."
    assert "Participant" in content, "Report missing Participant entity check."
    assert "Rating" in content, "Report missing Rating entity check."
    assert "AnalysisResult" in content, "Report missing AnalysisResult entity check."


def test_report_path_matches_spec():
    """
    Verifies the report is generated at the exact path specified in tasks.md.
    """
    expected_path = Path("data/validation/data_model_report.txt")
    assert expected_path.exists(), f"Expected report at {expected_path} but not found."
