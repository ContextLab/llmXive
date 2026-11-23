import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the function to test
from code.setup_project import initialize_project_structure

class TestProjectInitialization:
    """Tests for the project directory structure initialization."""

    def setup_method(self):
        """Create a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir) / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av"

    def teardown_method(self):
        """Clean up the temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_creates_root_directory(self):
        """Test that the root project directory is created."""
        result = initialize_project_structure(str(self.project_root))
        
        assert result is True
        assert self.project_root.exists()
        assert self.project_root.is_dir()

    def test_creates_code_directory(self):
        """Test that the code/ subdirectory is created."""
        initialize_project_structure(str(self.project_root))
        
        code_dir = self.project_root / "code"
        assert code_dir.exists()
        assert code_dir.is_dir()

    def test_creates_data_directories(self):
        """Test that data/raw and data/processed subdirectories are created."""
        initialize_project_structure(str(self.project_root))
        
        raw_dir = self.project_root / "data" / "raw"
        processed_dir = self.project_root / "data" / "processed"
        
        assert raw_dir.exists()
        assert raw_dir.is_dir()
        assert processed_dir.exists()
        assert processed_dir.is_dir()

    def test_creates_tests_directory(self):
        """Test that the tests/ subdirectory is created."""
        initialize_project_structure(str(self.project_root))
        
        tests_dir = self.project_root / "tests"
        assert tests_dir.exists()
        assert tests_dir.is_dir()

    def test_creates_docs_directory(self):
        """Test that the docs/ subdirectory is created."""
        initialize_project_structure(str(self.project_root))
        
        docs_dir = self.project_root / "docs"
        assert docs_dir.exists()
        assert docs_dir.is_dir()

    def test_creates_state_directory(self):
        """Test that the state/ subdirectory is created."""
        initialize_project_structure(str(self.project_root))
        
        state_dir = self.project_root / "state"
        assert state_dir.exists()
        assert state_dir.is_dir()

    def test_creates_config_directory(self):
        """Test that the config/ subdirectory is created."""
        initialize_project_structure(str(self.project_root))
        
        config_dir = self.project_root / "config"
        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_idempotent_operation(self):
        """Test that running the initialization twice does not cause errors."""
        result1 = initialize_project_structure(str(self.project_root))
        result2 = initialize_project_structure(str(self.project_root))
        
        assert result1 is True
        assert result2 is True
        
        # Verify structure still exists
        assert (self.project_root / "code").exists()
        assert (self.project_root / "data" / "raw").exists()

    def test_full_structure_exists(self):
        """Test that all required directories exist after initialization."""
        initialize_project_structure(str(self.project_root))
        
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "tests",
            "docs",
            "state",
            "config"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} is not a directory."