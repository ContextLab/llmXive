"""
Integration test for T047: Associational Framing Validation.

This test verifies that the verify_framing.py script correctly identifies
missing or incorrect framing in the results report.
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
import subprocess
import sys

import pytest

# We need to run the script in the context of the project
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "code" / "analysis" / "verify_framing.py"
METADATA_PATH = PROJECT_ROOT / "data" / "metrics" / "metadata.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "results.md"

@pytest.fixture
def backup_files():
    """Backup original metadata and report files if they exist."""
    backups = {}
    for path in [METADATA_PATH, REPORT_PATH]:
        if path.exists():
            backups[path] = path.read_text()
    yield backups
    # Restore
    for path, content in backups.items():
        path.write_text(content)

def test_framing_associational_correct(backup_files):
    """Test that the script passes when ASSOCIATIONAL framing is present and required."""
    # Setup metadata indicating non-randomized
    metadata = {
        "study_design": "observational",
        "randomized": False,
        "dataset_id": "test_ds"
    }
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f)

    # Setup report with correct framing
    report_content = """
    # Results

    ## Methodological Constraints
    Findings are framed as ASSOCIATIONAL.
    
    ## Analysis
    ...
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        f.write(report_content)

    # Run script
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "SUCCESS" in result.stdout or "PASSED" in result.stdout

def test_framing_associational_missing(backup_files):
    """Test that the script fails when ASSOCIATIONAL framing is required but missing."""
    # Setup metadata indicating non-randomized
    metadata = {
        "study_design": "observational",
        "randomized": False
    }
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f)

    # Setup report WITHOUT framing statement
    report_content = """
    # Results

    ## Analysis
    ...
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        f.write(report_content)

    # Run script
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 1, "Script should fail when framing is missing"
    assert "FAILURE" in result.stdout or "FAILED" in result.stderr

def test_framing_randomized_no_warning(backup_files):
    """Test that the script passes when study is randomized (no assoc tag required)."""
    # Setup metadata indicating randomized
    metadata = {
        "study_design": "randomized",
        "randomized": True
    }
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f)

    # Setup report
    report_content = """
    # Results
    
    ## Analysis
    ...
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        f.write(report_content)

    # Run script
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Script should pass for randomized studies: {result.stderr}"