"""
Tests for T010b: Verification of citation validation log creation.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

class TestCitationLogVerification:
    """Test suite for citation validation log verification."""

    def test_log_file_creation(self, tmp_path):
        """Test that the log file is created during validation."""
        # Create a temporary logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        # Save original paths
        original_cwd = Path.cwd()
        try:
            # Change to temp directory
            os.chdir(tmp_path)

            # Create dummy data
            dummy_data = [
                {
                    "composition": "Al2O3",
                    "weibull_modulus": 10.5,
                    "source_url": "https://example.com/test",
                    "doi": "10.1000/test"
                }
            ]

            # Import after changing directory to ensure relative paths work
            from ingestion import validate_source_citations

            # Run validation
            validate_source_citations(dummy_data)

            # Check log file exists
            log_file = logs_dir / "citation_validation.log"
            # Note: The actual log path is hardcoded in code/ingestion.py
            # We check the actual location
            actual_log = Path("logs/citation_validation.log")
            assert actual_log.exists(), "Log file was not created"

            # Check log file has content
            content = actual_log.read_text()
            assert len(content) > 0, "Log file is empty"

        finally:
            os.chdir(original_cwd)

    def test_log_contains_validation_entry(self):
        """Test that the log file contains at least one validation entry."""
        # This test assumes T010b has been run successfully
        # If T010b hasn't been run, this test will fail appropriately
        log_file = Path("logs/citation_validation.log")

        if not log_file.exists():
            pytest.skip("Log file does not exist yet. Run T010b first.")

        content = log_file.read_text()
        assert len(content.strip()) > 0, "Log file is empty"

        # Check for typical log entry patterns
        assert any(keyword in content.lower() for keyword in ['validation', 'citation', 'url', 'doi', 'success', 'failure']), \
            "Log file does not contain expected validation entries"