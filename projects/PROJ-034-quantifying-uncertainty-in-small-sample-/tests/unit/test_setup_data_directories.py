"""
Unit tests for the data directory setup script (task T007).
These tests verify that the required directory structure is created correctly.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from scripts.setup_data_directories import create_directories


class TestDataDirectorySetup:
    """Tests for data directory creation functionality."""

    def test_creates_data_root_directory(self, tmp_path):
        """Test that the data root directory is created."""
        create_directories(tmp_path)
        data_root = tmp_path / "data"
        assert data_root.exists()
        assert data_root.is_dir()

    def test_creates_raw_subdirectory(self, tmp_path):
        """Test that the data/raw subdirectory is created."""
        create_directories(tmp_path)
        raw_dir = tmp_path / "data" / "raw"
        assert raw_dir.exists()
        assert raw_dir.is_dir()

    def test_creates_simulated_subdirectory(self, tmp_path):
        """Test that the data/simulated subdirectory is created."""
        create_directories(tmp_path)
        simulated_dir = tmp_path / "data" / "simulated"
        assert simulated_dir.exists()
        assert simulated_dir.is_dir()

    def test_creates_results_subdirectory(self, tmp_path):
        """Test that the data/results subdirectory is created."""
        create_directories(tmp_path)
        results_dir = tmp_path / "data" / "results"
        assert results_dir.exists()
        assert results_dir.is_dir()

    def test_creates_gitkeep_in_raw(self, tmp_path):
        """Test that .gitkeep file exists in data/raw."""
        create_directories(tmp_path)
        gitkeep_path = tmp_path / "data" / "raw" / ".gitkeep"
        assert gitkeep_path.exists()
        assert gitkeep_path.is_file()

    def test_creates_gitkeep_in_simulated(self, tmp_path):
        """Test that .gitkeep file exists in data/simulated."""
        create_directories(tmp_path)
        gitkeep_path = tmp_path / "data" / "simulated" / ".gitkeep"
        assert gitkeep_path.exists()
        assert gitkeep_path.is_file()

    def test_creates_gitkeep_in_results(self, tmp_path):
        """Test that .gitkeep file exists in data/results."""
        create_directories(tmp_path)
        gitkeep_path = tmp_path / "data" / "results" / ".gitkeep"
        assert gitkeep_path.exists()
        assert gitkeep_path.is_file()

    def test_all_gitkeep_files_are_empty(self, tmp_path):
        """Test that all .gitkeep files are empty (as expected for placeholder files)."""
        create_directories(tmp_path)
        
        gitkeep_files = [
            tmp_path / "data" / "raw" / ".gitkeep",
            tmp_path / "data" / "simulated" / ".gitkeep",
            tmp_path / "data" / "results" / ".gitkeep"
        ]
        
        for gitkeep in gitkeep_files:
            assert gitkeep.stat().st_size == 0, f"{gitkeep} should be empty"

    def test_idempotent_creation(self, tmp_path):
        """Test that running create_directories multiple times doesn't cause errors."""
        # First run
        create_directories(tmp_path)
        
        # Second run - should not raise exceptions
        create_directories(tmp_path)
        
        # Verify structure still exists
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "simulated").exists()
        assert (tmp_path / "data" / "results").exists()

    def test_creates_intermediate_directories(self, tmp_path):
        """Test that intermediate directories are created if they don't exist."""
        # Start with an empty tmp_path
        assert not (tmp_path / "data").exists()
        
        create_directories(tmp_path)
        
        # All directories should now exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "simulated").exists()
        assert (tmp_path / "data" / "results").exists()