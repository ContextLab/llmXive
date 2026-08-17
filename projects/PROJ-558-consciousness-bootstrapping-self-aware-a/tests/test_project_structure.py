import os
import pytest
from pathlib import Path

def test_project_structure_exists():
    """Verify that the main project directory exists."""
    project_root = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    assert project_root.exists(), f"Project root directory {project_root} does not exist"
    assert project_root.is_dir(), f"{project_root} is not a directory"

def test_required_subdirectories_exist():
    """Verify that all required subdirectories exist."""
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
        assert full_path.exists(), f"Required directory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"
