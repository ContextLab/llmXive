import os
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import get_project_root
from setup_directories import setup_data_and_results_directories

class TestDirectorySetup:
    """Tests for T008 directory structure setup."""

    def test_directories_exist(self):
        """Verify that data/raw, data/processed, and results directories exist."""
        project_root = get_project_root()
        
        required_dirs = [
            project_root / "data" / "raw",
            project_root / "data" / "processed",
            project_root / "results",
        ]
        
        for dir_path in required_dirs:
            assert dir_path.exists(), f"Directory {dir_path} does not exist"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_gitkeep_files_exist(self):
        """Verify that .gitkeep files exist in data/raw, data/processed, and results."""
        project_root = get_project_root()
        
        required_gitkeeps = [
            project_root / "data" / "raw" / ".gitkeep",
            project_root / "data" / "processed" / ".gitkeep",
            project_root / "results" / ".gitkeep",
        ]
        
        for gitkeep_path in required_gitkeeps:
            assert gitkeep_path.exists(), f".gitkeep file {gitkeep_path} does not exist"
            assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

    def test_setup_function_returns_correct_results(self):
        """Verify that setup_data_and_results_directories returns correct status."""
        project_root = get_project_root()
        
        results = setup_data_and_results_directories(project_root)
        
        # Should return 3 results
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # Check that all paths are relative and correct
        expected_paths = {"data/raw", "data/processed", "results"}
        returned_paths = {path_str for path_str, _ in results}
        
        assert expected_paths == returned_paths, f"Expected {expected_paths}, got {returned_paths}"

    def test_idempotency(self):
        """Verify that running setup multiple times does not cause errors."""
        project_root = get_project_root()
        
        # Run setup twice
        results1 = setup_data_and_results_directories(project_root)
        results2 = setup_data_and_results_directories(project_root)
        
        # Both runs should succeed
        assert len(results1) == 3
        assert len(results2) == 3
        
        # All directories should still exist
        for path_str, _ in results2:
            full_path = project_root / path_str
            assert full_path.exists(), f"Directory {full_path} missing after second run"
