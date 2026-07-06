import os
import pytest
from pathlib import Path
from code.setup_directories import create_project_directories

class TestCreateProjectDirectories:
    """Tests for the directory creation utility."""

    def test_directories_exist_after_creation(self, tmp_path, monkeypatch):
        """Verify that required directories are created."""
        # We need to mock the project root to use a temporary directory
        # to avoid creating files in the actual repository during tests
        original_cwd = os.getcwd()
        project_root = tmp_path / "projects" / "PROJ-530-neural-correlates-of-error-monitoring-du"
        
        # Create the parent structure manually to allow the function to run
        # The function expects to create 'projects/...' relative to cwd
        # We change cwd to tmp_path to simulate the environment
        monkeypatch.chdir(tmp_path)
        
        try:
            paths = create_project_directories()
            
            # Check specific T002 requirements
            assert "data/raw" in paths
            assert "data/processed" in paths
            
            # Verify they actually exist on disk
            assert (project_root / "data/raw").exists()
            assert (project_root / "data/processed").exists()
            assert (project_root / "data/raw").is_dir()
            assert (project_root / "data/processed").is_dir()
            
            # Check T003 requirements as well since the function creates them
            assert "results/models" in paths
            assert "results/figures" in paths
            assert "results/diagnostics" in paths
            assert "code" in paths
            assert "tests" in paths
            
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path, monkeypatch):
        """Verify that running the function twice does not raise errors."""
        monkeypatch.chdir(tmp_path)
        
        try:
            # Run twice
            create_project_directories()
            create_project_directories()
            # If no exception, it is idempotent
            assert True
        finally:
            os.chdir(os.getcwd())
