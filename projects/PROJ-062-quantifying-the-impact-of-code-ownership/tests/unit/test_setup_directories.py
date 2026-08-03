"""
Unit tests for the setup_directories script (Task T004).
Verifies that the required data directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to add the code directory to the path to import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.setup_directories import create_directories


class TestSetupDirectories:
    """Test cases for directory creation functionality."""

    def setup_method(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_creates_raw_directory(self):
        """Test that data/raw/ directory is created."""
        create_directories()
        raw_dir = Path("data/raw")
        assert raw_dir.exists(), "data/raw/ directory should be created"
        assert raw_dir.is_dir(), "data/raw/ should be a directory"

    def test_creates_intermediate_directory(self):
        """Test that data/intermediate/ directory is created."""
        create_directories()
        intermediate_dir = Path("data/intermediate")
        assert intermediate_dir.exists(), "data/intermediate/ directory should be created"
        assert intermediate_dir.is_dir(), "data/intermediate/ should be a directory"

    def test_creates_results_directory(self):
        """Test that data/results/ directory is created."""
        create_directories()
        results_dir = Path("data/results")
        assert results_dir.exists(), "data/results/ directory should be created"
        assert results_dir.is_dir(), "data/results/ should be a directory"

    def test_creates_gitkeep_in_raw(self):
        """Test that .gitkeep file is created in data/raw/."""
        create_directories()
        gitkeep_path = Path("data/raw/.gitkeep")
        assert gitkeep_path.exists(), ".gitkeep should exist in data/raw/"
        assert gitkeep_path.is_file(), ".gitkeep in data/raw/ should be a file"

    def test_creates_gitkeep_in_intermediate(self):
        """Test that .gitkeep file is created in data/intermediate/."""
        create_directories()
        gitkeep_path = Path("data/intermediate/.gitkeep")
        assert gitkeep_path.exists(), ".gitkeep should exist in data/intermediate/"
        assert gitkeep_path.is_file(), ".gitkeep in data/intermediate/ should be a file"

    def test_creates_gitkeep_in_results(self):
        """Test that .gitkeep file is created in data/results/."""
        create_directories()
        gitkeep_path = Path("data/results/.gitkeep")
        assert gitkeep_path.exists(), ".gitkeep should exist in data/results/"
        assert gitkeep_path.is_file(), ".gitkeep in data/results/ should be a file"

    def test_idempotent_creation(self):
        """Test that running the script twice doesn't cause errors."""
        create_directories()
        # Run again - should not raise any exceptions
        create_directories()
        
        # Verify all directories still exist
        assert Path("data/raw").exists()
        assert Path("data/intermediate").exists()
        assert Path("data/results").exists()

    def test_creates_parent_data_directory(self):
        """Test that the parent data/ directory is created if it doesn't exist."""
        # Ensure data/ doesn't exist
        if Path("data").exists():
            shutil.rmtree("data")
        
        create_directories()
        data_dir = Path("data")
        assert data_dir.exists(), "Parent data/ directory should be created"
        assert data_dir.is_dir(), "Parent data/ should be a directory"