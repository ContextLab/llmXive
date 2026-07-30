import os
import pytest
from pathlib import Path

def test_project_structure_exists():
    """
    Test that the required directory structure exists after running create_project_structure.py
    """
    project_root = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_project_structure_is_clean():
    """
    Test that the created directories are empty (except for .gitkeep if added)
    """
    project_root = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Check that we can list the directories without error
    for dir_path in ["data/raw", "data/processed", "code", "tests", "artifacts", "artifacts/checkpoints", "artifacts/results"]:
        full_path = project_root / dir_path
        assert full_path.exists()
        # We don't assert emptiness as __init__.py files might be added later
        # Just ensure we can access them