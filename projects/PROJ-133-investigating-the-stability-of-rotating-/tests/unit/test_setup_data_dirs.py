import os
import pytest
from pathlib import Path
import tempfile
import shutil

from utils.setup_data_dirs import create_project_structure

class TestDataDirSetup:
    """Tests for the data directory creation utility."""

    def test_creates_required_structure(self, tmp_path):
        """Verify that create_project_structure creates raw, processed, and aggregated."""
        # Run the function on a temporary directory
        create_project_structure(str(tmp_path))
        
        # Verify the directories exist
        assert (tmp_path / "raw").exists(), "raw directory should be created"
        assert (tmp_path / "processed").exists(), "processed directory should be created"
        assert (tmp_path / "aggregated").exists(), "aggregated directory should be created"
        
        # Verify they are directories
        assert (tmp_path / "raw").is_dir()
        assert (tmp_path / "processed").is_dir()
        assert (tmp_path / "aggregated").is_dir()

    def test_idempotent(self, tmp_path):
        """Verify that running the function twice does not cause errors."""
        # Run twice
        create_project_structure(str(tmp_path))
        create_project_structure(str(tmp_path))
        
        # Verify structure still exists
        assert (tmp_path / "raw").exists()
        assert (tmp_path / "processed").exists()
        assert (tmp_path / "aggregated").exists()

    def test_creates_parent_if_needed(self, tmp_path):
        """Verify that parent directories are created if they don't exist."""
        nested = tmp_path / "level1" / "level2"
        
        create_project_structure(str(nested))
        
        assert (nested / "raw").exists()
        assert (nested / "processed").exists()
        assert (nested / "aggregated").exists()
        
        # Verify parent was created
        assert nested.exists()
        assert (tmp_path / "level1").exists()