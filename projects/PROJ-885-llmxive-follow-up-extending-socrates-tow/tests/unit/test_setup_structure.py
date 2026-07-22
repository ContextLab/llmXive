import os
import pytest
from pathlib import Path
from setup_structure import create_directory_structure

def test_directory_structure_creation(tmp_path, monkeypatch):
    """
    Test that create_directory_structure creates the required folders.
    We use tmp_path to simulate the project root.
    """
    # Change the working directory to the temp path for the test
    monkeypatch.chdir(tmp_path)
    
    # Call the function
    created_paths = create_directory_structure()
    
    # Verify the expected directories were created
    expected_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "contracts",
    ]
    
    for dir_name in expected_dirs:
        dir_path = tmp_path / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created."
        assert dir_path.is_dir(), f"{dir_name} is not a directory."
    
    # Verify __init__.py files were created for packages
    package_dirs = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "contracts",
    ]
    
    for pkg_dir in package_dirs:
        init_file = tmp_path / pkg_dir / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {pkg_dir}"

def test_idempotency(tmp_path, monkeypatch):
    """
    Test that running create_directory_structure twice does not fail
    and does not duplicate directories.
    """
    monkeypatch.chdir(tmp_path)
    
    # First run
    created_first = create_directory_structure()
    
    # Second run
    created_second = create_directory_structure()
    
    # Second run should return empty list or just info that they exist
    # (depending on implementation, but shouldn't crash)
    assert len(created_second) == 0, "Second run should not create new directories."
    
    # Verify structure still exists
    assert (tmp_path / "code").exists()
    assert (tmp_path / "data" / "processed").exists()
