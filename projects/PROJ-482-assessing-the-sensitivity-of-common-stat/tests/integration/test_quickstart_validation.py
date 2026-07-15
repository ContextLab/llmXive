"""
Integration tests for Quickstart validation.
Ensures that the validation script runs correctly and reports expected results.
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestQuickstartValidation:
    """Tests for the quickstart validation script."""

    def test_validation_script_exists(self):
        """Check that the validation script exists."""
        script_path = PROJECT_ROOT / "code" / "validate_quickstart.py"
        assert script_path.exists(), f"Validation script not found: {script_path}"

    def test_validation_script_runs(self):
        """Check that the validation script runs without crashing."""
        script_path = PROJECT_ROOT / "code" / "validate_quickstart.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        # The script might fail if outputs are missing, but it should run
        assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"
        assert "Quickstart Validation" in result.stdout or "Quickstart Validation" in result.stderr

    def test_validation_checks_paths(self):
        """Check that the validation script checks for required paths."""
        script_path = PROJECT_ROOT / "code" / "validate_quickstart.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        # Check that path validation messages are present
        assert "Code directory" in result.stdout or "Code directory" in result.stderr
        assert "Raw data directory" in result.stdout or "Raw data directory" in result.stderr

    def test_validation_checks_imports(self):
        """Check that the validation script checks for required imports."""
        script_path = PROJECT_ROOT / "code" / "validate_quickstart.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        # Check that import validation messages are present
        assert "Validating module imports" in result.stdout or "Validating module imports" in result.stderr

    def test_validation_script_handles_missing_files(self):
        """Check that the validation script correctly reports missing files."""
        # Temporarily rename a required file to test error handling
        data_raw_dir = PROJECT_ROOT / "data" / "raw"
        sample_file = data_raw_dir / "sample_validation.csv"
        backup_file = data_raw_dir / "sample_validation.csv.bak"

        if sample_file.exists():
            sample_file.rename(backup_file)
            try:
                script_path = PROJECT_ROOT / "code" / "validate_quickstart.py"
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                # Should report missing file
                assert "Sample validation dataset" in result.stderr or "Sample validation dataset" in result.stdout
                assert "missing" in result.stderr.lower() or "missing" in result.stdout.lower()
            finally:
                # Restore the file
                if backup_file.exists():
                    backup_file.rename(sample_file)
        else:
            pytest.skip("Sample validation file does not exist, cannot test missing file handling")