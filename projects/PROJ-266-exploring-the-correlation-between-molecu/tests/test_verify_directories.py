"""
Tests for directory verification logic.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.verify_directories import verify_directories, get_project_root

class TestVerifyDirectories:
    def test_verify_directories_success(self, tmp_path):
        """Test that verification passes when directories exist."""
        # Create temporary directories to simulate project structure
        data_raw = tmp_path / "data" / "raw"
        data_processed = tmp_path / "data" / "processed"
        
        data_raw.mkdir(parents=True)
        data_processed.mkdir(parents=True)
        
        # Change to tmp_path to simulate running from project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # This should not raise an AssertionError
            result = verify_directories()
            assert result is True
        finally:
            os.chdir(original_cwd)

    def test_verify_directories_missing_raw(self, tmp_path):
        """Test that verification fails when data/raw is missing."""
        data_processed = tmp_path / "data" / "processed"
        data_processed.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(AssertionError) as exc_info:
                verify_directories()
            assert "data/raw" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)

    def test_verify_directories_missing_processed(self, tmp_path):
        """Test that verification fails when data/processed is missing."""
        data_raw = tmp_path / "data" / "raw"
        data_raw.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(AssertionError) as exc_info:
                verify_directories()
            assert "data/processed" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)

    def test_verify_directories_missing_both(self, tmp_path):
        """Test that verification fails when both directories are missing."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(AssertionError) as exc_info:
                verify_directories()
            assert "data/raw" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)