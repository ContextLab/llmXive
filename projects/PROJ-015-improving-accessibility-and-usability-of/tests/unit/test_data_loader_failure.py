"""
Unit test for T121: Data Loader Failure Test.

This test asserts that load_real_data raises FileNotFoundError 
when the input directory is empty or contains no valid session files.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Ensure the project root is in the path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.analysis.data_loader import load_real_data


class TestDataLoaderFailure:
    """Tests for data loader failure conditions."""

    def test_raises_error_on_empty_directory(self):
        """
        Test that load_real_data raises FileNotFoundError when the 
        input directory exists but is empty.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir)
            
            # Verify directory is empty
            assert len(list(input_path.glob("*"))) == 0
            
            # Expect FileNotFoundError with specific message
            with pytest.raises(FileNotFoundError) as exc_info:
                load_real_data(str(input_path))
            
            assert "Real data not found" in str(exc_info.value)
            assert str(input_path) in str(exc_info.value)

    def test_raises_error_on_nonexistent_directory(self):
        """
        Test that load_real_data raises FileNotFoundError when the 
        input directory does not exist.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            non_existent_path = Path(tmp_dir) / "does_not_exist"
            
            # Verify path does not exist
            assert not non_existent_path.exists()
            
            # Expect FileNotFoundError
            with pytest.raises(FileNotFoundError) as exc_info:
                load_real_data(str(non_existent_path))
            
            assert "Real data not found" in str(exc_info.value)
            assert str(non_existent_path) in str(exc_info.value)

    def test_raises_error_on_directory_with_only_invalid_files(self):
        """
        Test that load_real_data raises FileNotFoundError when the 
        directory contains files that are not valid session JSON files.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir)
            
            # Create a non-JSON file
            invalid_file = input_path / "not_a_session.txt"
            invalid_file.write_text("This is not a session file")
            
            # Expect FileNotFoundError because no valid JSON sessions exist
            with pytest.raises(FileNotFoundError) as exc_info:
                load_real_data(str(input_path))
            
            assert "Real data not found" in str(exc_info.value)

    def test_success_with_valid_session_file(self):
        """
        Test that load_real_data succeeds when a valid session file exists.
        This ensures the error handling doesn't break the happy path.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir)
            
            # Create a minimal valid session JSON file
            valid_session = {
                "participant_id": "test-001",
                "interface_type": "traditional",
                "status": "complete",
                "metrics": {
                    "completion_time": 10.5,
                    "error_count": 0
                }
            }
            
            session_file = input_path / "session_test_001.json"
            session_file.write_text(
                json.dumps(valid_session, indent=2)
            )
            
            # This should NOT raise an error
            try:
                import json
                df = load_real_data(str(input_path))
                assert df is not None
                assert len(df) > 0
                assert "participant_id" in df.columns
            except FileNotFoundError:
                pytest.fail("load_real_data raised FileNotFoundError unexpectedly with valid data")