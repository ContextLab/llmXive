import os
import pytest
from pathlib import Path
from config import get_project_root
from code.setup_directories import create_directories

def test_directory_structure_exists():
    """
    Verify that the required directory structure exists after setup.
    
    Expected directories:
    - code/{data,stimuli,analysis,viz,tests}
    - data/{raw/stimuli,raw/responses,processed,results}
    - docs
    """
    # Ensure directories are created
    create_directories()
    
    project_root = get_project_root()
    
    # Define expected directories
    expected_dirs = [
        # Code subdirectories
        project_root / "code" / "data",
        project_root / "code" / "stimuli",
        project_root / "code" / "analysis",
        project_root / "code" / "viz",
        project_root / "code" / "tests",
        
        # Data subdirectories
        project_root / "data" / "raw" / "stimuli",
        project_root / "data" / "raw" / "responses",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        
        # Documentation
        project_root / "docs",
    ]
    
    # Verify each directory exists
    for directory in expected_dirs:
        assert directory.exists(), f"Directory does not exist: {directory}"
        assert directory.is_dir(), f"Path is not a directory: {directory}"

def test_directory_tree_integrity():
    """
    Verify that the directory tree matches the expected structure exactly.
    """
    # Ensure directories are created
    create_directories()
    
    project_root = get_project_root()
    
    # Check that code directory has the expected subdirectories
    code_dir = project_root / "code"
    expected_code_subdirs = {"data", "stimuli", "analysis", "viz", "tests"}
    actual_code_subdirs = {d.name for d in code_dir.iterdir() if d.is_dir()}
    assert expected_code_subdirs.issubset(actual_code_subdirs), \
        f"Missing code subdirectories. Expected: {expected_code_subdirs}, Found: {actual_code_subdirs}"
    
    # Check that data directory has the expected subdirectories
    data_dir = project_root / "data"
    expected_data_subdirs = {"raw", "processed", "results"}
    actual_data_subdirs = {d.name for d in data_dir.iterdir() if d.is_dir()}
    assert expected_data_subdirs.issubset(actual_data_subdirs), \
        f"Missing data subdirectories. Expected: {expected_data_subdirs}, Found: {actual_data_subdirs}"
    
    # Check raw data subdirectories
    raw_dir = data_dir / "raw"
    expected_raw_subdirs = {"stimuli", "responses"}
    actual_raw_subdirs = {d.name for d in raw_dir.iterdir() if d.is_dir()}
    assert expected_raw_subdirs.issubset(actual_raw_subdirs), \
        f"Missing raw data subdirectories. Expected: {expected_raw_subdirs}, Found: {actual_raw_subdirs}"
