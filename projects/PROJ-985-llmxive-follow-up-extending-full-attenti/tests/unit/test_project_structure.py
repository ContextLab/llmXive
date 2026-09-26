import os
import pytest
from pathlib import Path

def test_directories_exist():
    """
    Verify that all base project directories exist as per T001a.
    Uses os.path.isdir() as required.
    """
    # Define all required directories relative to project root
    required_dirs = [
        "code",
        "tests",
        "data",
        "code/lib",
        "code/data",
        "code/models",
        "code/evaluation",
        "data/results",
        "data/logs",
        "data/intermediate",
        "data/config"
    ]

    # Get project root (current working directory)
    project_root = Path.cwd()
    
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        assert os.path.isdir(full_path), f"Directory missing: {full_path}"

def test_structure_verification_file_exists():
    """
    Verify that data/logs/structure_verification.txt exists and is non-empty.
    """
    log_file = Path.cwd() / "data" / "logs" / "structure_verification.txt"
    assert log_file.exists(), f"File missing: {log_file}"
    assert log_file.stat().st_size > 0, f"File is empty: {log_file}"