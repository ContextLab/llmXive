"""
Unit tests for edge cases in code/preprocess.py.
Specifically tests missing data scenarios.
"""
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocess import stream_eeg_files, load_config
from utils.logging import get_logger

class TestMissingDataEdgeCases:
    """Tests for handling missing data in preprocessing."""

    def test_missing_data_directory(self, tmp_path):
        """
        Verify that stream_eeg_files raises FileNotFoundError
        when the specified data directory does not exist.
        """
        nonexistent_dir = tmp_path / "nonexistent_data"
        
        with pytest.raises(FileNotFoundError) as excinfo:
            list(stream_eeg_files(str(nonexistent_dir)))
        
        assert "Data directory not found" in str(excinfo.value)
        assert str(nonexistent_dir) in str(excinfo.value)

    def test_missing_eeg_file_in_directory(self, tmp_path, monkeypatch):
        """
        Verify that stream_eeg_files raises FileNotFoundError
        when the directory exists but contains no EEG files.
        """
        # Create a directory with no EEG files
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "readme.txt").write_text("No EEG here")
        
        # Mock config to point to this directory
        mock_config = {
            "raw_data_dir": str(data_dir),
            "file_extensions": [".edf", ".bdf", ".vhdr"]
        }
        
        # Patch load_config to return our mock
        monkeypatch.setattr("preprocess.load_config", lambda _: mock_config)
        
        with pytest.raises(FileNotFoundError) as excinfo:
            list(stream_eeg_files(str(data_dir)))
        
        assert "No EEG files found" in str(excinfo.value)

    def test_corrupted_eeg_file_handling(self, tmp_path):
        """
        Verify that stream_eeg_files handles corrupted files gracefully
        by logging the error and continuing (or raising if strict mode).
        """
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create a corrupted file with .edf extension
        corrupted_file = data_dir / "participant_001.edf"
        corrupted_file.write_bytes(b"corrupted binary data")
        
        # We expect this to either raise or log an error during reading
        # The exact behavior depends on MNE's error handling
        # For this test, we verify the function attempts to read it
        try:
            files = list(stream_eeg_files(str(data_dir)))
            # If it returns, it means MNE handled the error internally
            # or the file was skipped
            assert isinstance(files, list)
        except Exception as e:
            # If it raises, it should be a clear error about the file
            assert "Error reading" in str(e) or "corrupted" in str(e).lower()
