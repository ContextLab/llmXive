"""
Unit tests for the precondition check in run_analysis.py (Task T108).

This test suite verifies that the `precondition_check` function
correctly enforces the pipeline order by raising a DataValidationError
when cleaned_sessions.csv is missing.
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import the function and exception from the module under test
# Note: We import from the local module structure relative to code/
import sys
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.run_analysis import precondition_check, DataValidationError


class TestPreconditionCheck:
    """Tests for the precondition_check function."""

    def test_missing_cleaned_data_raises_error(self):
        """
        Test that precondition_check raises DataValidationError
        when cleaned_sessions.csv is missing.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Ensure the directory is empty (no cleaned_sessions.csv)
            input_path = Path(temp_dir)
            
            with pytest.raises(DataValidationError) as exc_info:
                precondition_check(str(input_path))
            
            # Verify the error message contains expected text
            assert "cleaned_sessions.csv" in str(exc_info.value)
            assert "missing" in str(exc_info.value).lower()
            assert "Precondition failed" in str(exc_info.value)

    def test_cleaned_data_exists_returns_true(self):
        """
        Test that precondition_check returns True when
        cleaned_sessions.csv exists.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the cleaned_sessions.csv file
            cleaned_file = Path(temp_dir) / "cleaned_sessions.csv"
            cleaned_file.touch()  # Create an empty file
            
            # Should not raise an exception
            result = precondition_check(temp_dir)
            
            assert result is True

    def test_missing_file_in_subdirectory(self):
        """
        Test that the check specifically looks in the provided directory,
        not in parent or child directories.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a subdirectory with the file
            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()
            (sub_dir / "cleaned_sessions.csv").touch()
            
            # The check should fail because the file is not in temp_dir
            with pytest.raises(DataValidationError):
                precondition_check(temp_dir)

    def test_wrong_filename_does_not_pass(self):
        """
        Test that a file with a similar but incorrect name does not pass.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with a wrong name
            wrong_file = Path(temp_dir) / "cleaned_data.csv"
            wrong_file.touch()
            
            with pytest.raises(DataValidationError):
                precondition_check(temp_dir)

    def test_empty_directory_raises_error(self):
        """
        Test that an empty directory raises the error.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(DataValidationError):
                precondition_check(temp_dir)

    def test_directory_with_other_files_raises_error(self):
        """
        Test that a directory with other files but no cleaned_sessions.csv raises error.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some other files
            Path(temp_dir, "raw_data.json").touch()
            Path(temp_dir, "notes.txt").write_text("Some notes")
            
            with pytest.raises(DataValidationError):
                precondition_check(temp_dir)

    def test_case_sensitivity(self):
        """
        Test that the filename check is case-sensitive (Linux default).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with wrong case
            wrong_case_file = Path(temp_dir) / "Cleaned_Sessions.csv"
            wrong_case_file.touch()
            
            # Should raise error because exact match is required
            with pytest.raises(DataValidationError):
                precondition_check(temp_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])