"""
Unit tests for the setup_data_dirs module.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import sys
import os

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import get_config, ensure_directories
from setup_data_dirs import main


class TestSetupDataDirs:
    """Tests for data directory setup functionality."""

    def test_ensure_directories_creates_new(self, tmp_path):
        """Test that ensure_directories creates new directories."""
        test_dir = tmp_path / "test" / "sub" / "dir"
        result = ensure_directories([test_dir])
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directories_existing(self, tmp_path):
        """Test that ensure_directories returns True for existing directories."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        result = ensure_directories([test_dir])
        assert result is True

    def test_setup_data_dirs_creates_expected_dirs(self, tmp_path, monkeypatch):
        """Test that main() creates the expected data directories."""
        # Patch get_config to use our temp directory
        def mock_get_config():
            return {
                "project_root": str(tmp_path),
                "data_dir": "data",
                "raw_dir": "data/raw",
                "results_dir": "data/results",
                "figures_dir": "data/figures",
            }
        
        monkeypatch.setattr("setup_data_dirs.get_config", mock_get_config)
        monkeypatch.setattr("setup_data_dirs.setup_logging", lambda: None)

        # Run main
        result = main()
        
        # Verify exit code
        assert result == 0

        # Verify directories were created
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "results").exists()
        assert (tmp_path / "data" / "figures").exists()

    def test_setup_data_dirs_handles_errors(self, tmp_path, monkeypatch):
        """Test that main() handles directory creation errors."""
        def mock_get_config():
            return {
                "project_root": str(tmp_path),
                "data_dir": "data",
                "raw_dir": "data/raw",
                "results_dir": "data/results",
                "figures_dir": "data/figures",
            }
        
        monkeypatch.setattr("setup_data_dirs.get_config", mock_get_config)
        
        # Mock ensure_directories to fail
        def mock_ensure_directories(dirs):
            return False
        
        monkeypatch.setattr("setup_data_dirs.ensure_directories", mock_ensure_directories)
        monkeypatch.setattr("setup_data_dirs.setup_logging", lambda: None)

        # Run main
        result = main()
        
        # Should return 1 on failure
        assert result == 1
