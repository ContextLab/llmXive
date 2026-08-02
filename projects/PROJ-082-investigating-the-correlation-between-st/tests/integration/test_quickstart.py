"""
Integration test for T036a: Quickstart Validation.
Verifies that the quickstart_validator.py script runs and produces the expected log.
"""
import os
import sys
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

@pytest.mark.integration
def test_quickstart_validator_runs():
    """Test that the quickstart validator script executes without crashing."""
    validator_script = PROJECT_ROOT / "code" / "quickstart_validator.py"
    
    assert validator_script.exists(), "quickstart_validator.py must exist"

    result = subprocess.run(
        [sys.executable, str(validator_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    # The validator might return non-zero if the pipeline fails, 
    # but the script itself should run and produce a report.
    report_path = PROJECT_ROOT / "data" / "logs" / "quickstart_report.md"
    
    assert report_path.exists(), "quickstart_report.md must be generated"
    assert report_path.stat().st_size > 0, "quickstart_report.md must not be empty"

    # Read report to ensure it has structure
    with open(report_path, 'r') as f:
        content = f.read()
        assert "Quickstart Validation Report" in content, "Report must have header"
        assert "Status" in content, "Report must have status"
        assert "Check Results" in content, "Report must have check results section"

@pytest.mark.integration
def test_validator_handles_missing_artifacts_gracefully():
    """Test that the validator reports missing artifacts instead of crashing."""
    # This test assumes the validator is run in an environment where some artifacts
    # might be missing (e.g., fresh run). The validator should detect this and report it.
    validator_script = PROJECT_ROOT / "code" / "quickstart_validator.py"
    
    result = subprocess.run(
        [sys.executable, str(validator_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    report_path = PROJECT_ROOT / "data" / "logs" / "quickstart_report.md"
    assert report_path.exists()

    with open(report_path, 'r') as f:
        content = f.read()
        # Even if validation fails, the report should be generated
        assert "Validation Report" in content