import pytest
from pathlib import Path
import yaml
import tempfile
import shutil
import os

# Adjust import based on actual structure - assuming tests are at code/tests/unit/
# and setup_state is at code/setup_state.py
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.setup_state import create_state_structure


class TestSetupState:
    """Unit tests for state directory creation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_creates_state_directory(self):
        """Test that create_state_structure creates the state directory."""
        create_state_structure(self.test_dir)
        
        state_dir = self.test_dir / "state"
        assert state_dir.exists(), "State directory should be created"
        assert state_dir.is_dir(), "State should be a directory"

    def test_creates_projects_subdirectory(self):
        """Test that the projects subdirectory is created."""
        create_state_structure(self.test_dir)
        
        projects_dir = self.test_dir / "state" / "projects"
        assert projects_dir.exists(), "Projects directory should be created"
        assert projects_dir.is_dir(), "Projects should be a directory"

    def test_no_error_if_directories_exist(self):
        """Test that no error is raised if directories already exist."""
        # Create directories first
        state_dir = self.test_dir / "state"
        projects_dir = state_dir / "projects"
        state_dir.mkdir(parents=True)
        projects_dir.mkdir()
        
        # Should not raise an exception
        create_state_structure(self.test_dir)
        
        assert state_dir.exists()
        assert projects_dir.exists()

    def test_creates_nested_structure(self):
        """Test that nested directory structure is created correctly."""
        create_state_structure(self.test_dir)
        
        state_dir = self.test_dir / "state"
        projects_dir = state_dir / "projects"
        
        assert state_dir.exists()
        assert projects_dir.exists()
        assert state_dir in projects_dir.parents

    def test_state_file_creation(self):
        """Test that the placeholder state file is created with correct content."""
        from code.setup_state import main
        
        # Change to test directory to simulate script execution
        original_cwd = Path.cwd()
        try:
            os.chdir(self.test_dir)
            main()
            
            project_id = "PROJ-122-identifying-structure-property-relations"
            state_file = self.test_dir / "state" / "projects" / f"{project_id}.yaml"
            
            assert state_file.exists(), "State file should be created"
            
            with open(state_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            assert "project_id" in data
            assert data["project_id"] == project_id
            assert "created_at" in data
            assert "updated_at" in data
            assert "status" in data
            assert data["status"] == "initialized"
            assert "artifacts" in data
            assert "checksums" in data
            assert "metadata" in data
        finally:
            os.chdir(original_cwd)

    def test_state_file_content_structure(self):
        """Test that the state file has the expected structure and fields."""
        from code.setup_state import main
        
        original_cwd = Path.cwd()
        try:
            os.chdir(self.test_dir)
            main()
            
            project_id = "PROJ-122-identifying-structure-property-relations"
            state_file = self.test_dir / "state" / "projects" / f"{project_id}.yaml"
            
            with open(state_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            # Check required top-level keys
            required_keys = ["project_id", "created_at", "updated_at", "status", "artifacts", "checksums", "metadata"]
            for key in required_keys:
                assert key in data, f"Missing required key: {key}"
            
            # Check metadata structure
            assert "description" in data["metadata"]
            assert "version" in data["metadata"]
            
            # Check types
            assert isinstance(data["artifacts"], dict)
            assert isinstance(data["checksums"], dict)
        finally:
            os.chdir(original_cwd)
