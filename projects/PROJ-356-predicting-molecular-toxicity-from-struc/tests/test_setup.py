import os
import sys
from pathlib import Path
import pytest
from setup_directories import main

def test_data_directory_exists(tmp_path):
    """
    Test that the setup script creates the required data directory structure.
    This verifies the creation of 'code/data/' under the project root.
    """
    # Change to tmp_path to simulate a fresh environment
    original_cwd = os.getcwd()
    project_root = tmp_path / "PROJ-356-predicting-molecular-toxicity-from-struc"
    
    try:
        os.chdir(tmp_path)
        
        # Run the main function which creates directories
        result = main()
        
        assert result == 0, "Setup script should return 0 on success"
        
        # Verify the specific directory for T001 exists
        code_dir = project_root / "code"
        assert code_dir.exists(), f"Root project code directory {code_dir} should exist"
        assert code_dir.is_dir(), f"{code_dir} should be a directory"
        
        # Verify T004 specific subdirectory
        data_dir = code_dir / "data"
        assert data_dir.exists(), f"Data directory {data_dir} should exist"
        assert data_dir.is_dir(), f"{data_dir} should be a directory"

    finally:
        os.chdir(original_cwd)

def test_setup_script_creates_results_dir(tmp_path):
    """
    Test that the setup script creates the results directory.
    """
    original_cwd = os.getcwd()
    project_root = tmp_path / "PROJ-356-predicting-molecular-toxicity-from-struc"
    
    try:
        os.chdir(tmp_path)
        
        # Run the main function
        main()
        
        # Verify results directory
        results_dir = project_root / "code" / "results"
        assert results_dir.exists(), f"Results directory {results_dir} should exist"
        assert results_dir.is_dir(), f"{results_dir} should be a directory"

    finally:
        os.chdir(original_cwd)
