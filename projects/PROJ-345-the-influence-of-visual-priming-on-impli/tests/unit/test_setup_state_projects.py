"""
Unit tests for the state project directory setup functionality.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the function to test
from setup_state_projects import create_state_project_directories

class TestCreateStateProjectDirectories:
    """Tests for the create_state_project_directories function."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.test_base = Path(tempfile.mkdtemp())
        # Change to the test directory to simulate project root
        self.original_cwd = Path.cwd()
        os.chdir(self.test_base)
        
        # Create state directory structure in test location
        self.state_dir = self.test_base / "state"
        self.state_dir.mkdir()
        
    def teardown_method(self):
        """Clean up after each test method."""
        # Restore original working directory
        os.chdir(self.original_cwd)
        # Remove the temporary test directory
        if self.test_base.exists():
            shutil.rmtree(self.test_base)
    
    def test_creates_project_directory(self):
        """Test that the main project directory is created."""
        project_id = "TEST-PROJECT"
        created_dirs = create_state_project_directories(project_id)
        
        # Check that the main project directory exists
        project_dir = Path("state") / "projects" / project_id
        assert project_dir.exists(), f"Project directory {project_dir} was not created"
        assert project_dir.is_dir(), f"{project_dir} is not a directory"
    
    def test_creates_all_subdirectories(self):
        """Test that all required subdirectories are created."""
        project_id = "TEST-PROJECT"
        created_dirs = create_state_project_directories(project_id)
        
        expected_subdirs = ["artifacts", "logs", "snapshots", "config", "results"]
        project_dir = Path("state") / "projects" / project_id
        
        for subdir in expected_subdirs:
            subdir_path = project_dir / subdir
            assert subdir_path.exists(), f"Subdirectory {subdir_path} was not created"
            assert subdir_path.is_dir(), f"{subdir_path} is not a directory"
    
    def test_creates_gitkeep_files(self):
        """Test that .gitkeep files are created in all directories."""
        project_id = "TEST-PROJECT"
        create_state_project_directories(project_id)
        
        project_dir = Path("state") / "projects" / project_id
        
        # Check main project directory
        assert (project_dir / ".gitkeep").exists(), ".gitkeep not created in project root"
        
        # Check all subdirectories
        for subdir in ["artifacts", "logs", "snapshots", "config", "results"]:
            subdir_path = project_dir / subdir
            assert (subdir_path / ".gitkeep").exists(), f".gitkeep not created in {subdir}"
    
    def test_returns_list_of_created_directories(self):
        """Test that the function returns a list of created directory paths."""
        project_id = "TEST-PROJECT"
        created_dirs = create_state_project_directories(project_id)
        
        assert isinstance(created_dirs, list), "Function should return a list"
        assert len(created_dirs) > 0, "Function should return at least one directory"
        
        # All returned paths should be Path objects
        for dir_path in created_dirs:
            assert isinstance(dir_path, Path), "Each item should be a Path object"
            assert dir_path.exists(), f"Returned path {dir_path} does not exist"
    
    def test_handles_existing_directories(self):
        """Test that the function handles existing directories gracefully."""
        project_id = "EXISTING-PROJECT"
        
        # Create the directory structure first
        create_state_project_directories(project_id)
        
        # Run the function again - should not raise an error
        created_dirs = create_state_project_directories(project_id)
        
        # Should still return a list of directories
        assert isinstance(created_dirs, list)
        assert len(created_dirs) > 0
    
    def test_default_project_id(self):
        """Test that the function uses the default project ID when none is provided."""
        created_dirs = create_state_project_directories()
        
        project_dir = Path("state") / "projects" / "PROJ-345"
        assert project_dir.exists(), "Default project directory was not created"