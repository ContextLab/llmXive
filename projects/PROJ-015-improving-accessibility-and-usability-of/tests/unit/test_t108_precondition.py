"""
Unit tests for T108: Pipeline Order Enforcement.
Tests that precondition_check() raises an error if cleaned_sessions.csv is missing.
"""
import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.run_analysis import precondition_check, DataValidationError


class TestPreconditionCheck:
    def test_raises_error_when_file_missing(self):
        """
        Test that precondition_check raises DataValidationError
        if the cleaned_sessions.csv file does not exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cleaned_sessions.csv"
            
            # File does not exist
            with pytest.raises(DataValidationError) as exc_info:
                precondition_check(output_path)
            
            assert "missing" in str(exc_info.value).lower()
            assert "cleaning step" in str(exc_info.value).lower()

    def test_raises_error_when_file_empty(self):
        """
        Test that precondition_check raises DataValidationError
        if the cleaned_sessions.csv file exists but is empty.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cleaned_sessions.csv"
            output_path.touch()  # Create empty file
            
            with pytest.raises(DataValidationError) as exc_info:
                precondition_check(output_path)
            
            assert "empty" in str(exc_info.value).lower()

    def test_returns_true_when_file_exists_and_non_empty(self):
        """
        Test that precondition_check returns True when the file
        exists and has content.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cleaned_sessions.csv"
            # Write some dummy CSV content
            output_path.write_text("participant_id,metric\n1,10.5\n2,12.3\n")
            
            result = precondition_check(output_path)
            
            assert result is True

    def test_integration_missing_file_in_pipeline(self):
        """
        Integration-style test: Ensure the error message is descriptive
        enough to guide the user to run the cleaning step first.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cleaned_sessions.csv"
            
            with pytest.raises(DataValidationError) as exc_info:
                precondition_check(output_path)
            
            error_msg = str(exc_info.value)
            assert "T021c-cli" in error_msg or "clean_data.py" in error_msg
            assert "precondition" in error_msg.lower()