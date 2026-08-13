import pytest
import os
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_directories import setup_directories

def test_setup_directories_creates_expected_paths():
    """
    Verify that setup_directories creates the required directory structure.
    """
    # Run the setup function
    success = setup_directories()
    
    assert success is True, "setup_directories should return True on success"
    
    # Determine project root based on test location
    test_dir = Path(__file__).resolve().parent
    project_root = test_dir.parent
    
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/artifacts",
        "data/models",
        "data/results",
        "data/reports",
        "logs"
    ]
    
    for rel_path in expected_dirs:
        full_path = project_root / rel_path
        assert full_path.exists(), f"Directory {full_path} should exist after setup"
        assert full_path.is_dir(), f"{full_path} should be a directory"

def test_setup_directories_idempotent():
    """
    Verify that running setup_directories multiple times does not cause errors.
    """
    # Run twice
    result1 = setup_directories()
    result2 = setup_directories()
    
    assert result1 is True
    assert result2 is True
