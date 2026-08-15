import os
import pytest
from pathlib import Path
import shutil
import tempfile

from create_project_structure import create_structure

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to simulate the project root."""
    return tmp_path / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"

def test_create_structure_creates_all_dirs(temp_project_root):
    """
    Test that create_structure creates all required subdirectories.
    """
    # Run the creation logic on the temp directory
    create_structure(str(temp_project_root))
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/checkpoints",
        "artifacts/results",
    ]
    
    for dir_path in required_dirs:
        full_path = temp_project_root / dir_path
        assert full_path.exists(), f"Directory {full_path} was not created."
        assert full_path.is_dir(), f"{full_path} exists but is not a directory."

def test_create_structure_idempotent(temp_project_root):
    """
    Test that running create_structure twice does not raise errors.
    """
    create_structure(str(temp_project_root))
    # Run again
    create_structure(str(temp_project_root))
    
    assert (temp_project_root / "code").exists()
    assert (temp_project_root / "data/raw").exists()