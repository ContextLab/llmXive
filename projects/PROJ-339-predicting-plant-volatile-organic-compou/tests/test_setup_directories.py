import os
import pytest
from pathlib import Path
from code.setup_directories import create_directories

def test_create_directories_structure():
    """
    Verify that the create_directories function creates all required directories.
    This is a contract test for T001a.
    """
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "data/models",
        "specs"
    ]
    
    # Run the directory creation
    result = create_directories()
    assert result is True, "create_directories should return True on success"
    
    # Verify each directory exists
    base_path = Path(".")
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Directory {dir_path} should exist after creation"
        assert dir_path.is_dir(), f"{dir_path} should be a directory"
    
    # Specifically check nested structures
    assert (base_path / "data" / "raw").exists(), "data/raw should exist"
    assert (base_path / "data" / "processed").exists(), "data/processed should exist"
    assert (base_path / "data" / "results").exists(), "data/results should exist"
    assert (base_path / "data" / "models").exists(), "data/models should exist"

def test_idempotency():
    """
    Verify that running create_directories multiple times does not cause errors.
    """
    # Run twice
    result1 = create_directories()
    result2 = create_directories()
    
    assert result1 is True
    assert result2 is True
    
    # Verify structure is intact
    assert (Path(".") / "code").exists()
    assert (Path(".") / "data" / "raw").exists()