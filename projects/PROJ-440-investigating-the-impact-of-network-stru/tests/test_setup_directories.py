import os
import pytest
from pathlib import Path
from code.setup_directories import setup_directories

def test_setup_directories_creates_structure():
    """
    Test that T001a requirements are met:
    Creates code/, data/, data/raw/, data/processed/, data/analysis/, 
    tests/, contracts/, state/
    """
    # Ensure the directories exist by running the setup
    setup_directories()
    
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state"
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        assert dir_path.exists(), f"Directory {dir_name} does not exist after setup."
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory."

def test_nested_directories_exist():
    """
    Specific check for nested directories created by T001a.
    """
    setup_directories()
    
    # Check data subdirectories specifically
    data_raw = Path("data/raw")
    data_processed = Path("data/processed")
    data_analysis = Path("data/analysis")
    
    assert data_raw.exists()
    assert data_processed.exists()
    assert data_analysis.exists()
