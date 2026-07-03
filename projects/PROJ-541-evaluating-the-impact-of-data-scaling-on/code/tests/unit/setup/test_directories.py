import pytest
import os
from pathlib import Path
import sys

# Add parent to path to allow imports if needed, though this test is simple
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_directories import create_directories

class TestDirectoryCreation:
    """
    Tests for T001b: Verify that the required subdirectories are created.
    """

    def test_required_code_subdirectories_exist(self):
        """
        Verify that code/simulation, code/preprocessing, code/analysis, 
        and code/visualization directories are created.
        """
        base_path = Path(__file__).resolve().parent.parent.parent.parent
        
        required_dirs = [
            "code/simulation",
            "code/preprocessing",
            "code/analysis",
            "code/visualization"
        ]
        
        for dir_name in required_dirs:
            full_path = base_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} does not exist"
            assert full_path.is_dir(), f"{dir_name} is not a directory"

    def test_data_subdirectories_exist(self):
        """
        Verify that data/raw, data/scaled, data/config exist.
        """
        base_path = Path(__file__).resolve().parent.parent.parent.parent
        
        required_dirs = [
            "data/raw",
            "data/scaled",
            "data/config"
        ]
        
        for dir_name in required_dirs:
            full_path = base_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} does not exist"
            assert full_path.is_dir(), f"{dir_name} is not a directory"

    def test_results_and_scaled_subdirectories_exist(self):
        """
        Verify that results/figures and data/scaled/{standardized, minmax, robust} exist.
        """
        base_path = Path(__file__).resolve().parent.parent.parent.parent
        
        required_dirs = [
            "results/figures",
            "data/scaled/standardized",
            "data/scaled/minmax",
            "data/scaled/robust"
        ]
        
        for dir_name in required_dirs:
            full_path = base_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} does not exist"
            assert full_path.is_dir(), f"{dir_name} is not a directory"

    def test_create_directories_function_runs(self):
        """
        Ensure the create_directories function executes without error.
        """
        # This should run without raising exceptions
        result = create_directories()
        assert result is True