import pytest
from pathlib import Path
import os
from src.utils.config import get_path

def test_required_directories_exist():
    """
    Verify that all required project directories exist as per T001.
    
    Required directories:
    - src/, src/data/, src/synthesis/, src/analysis/, src/viz/, src/utils/
    - tests/unit/, tests/integration/, tests/contract/
    - data/raw/, data/processed/, data/results/
    - specs/, state/
    """
    required_dirs = [
        "src",
        "src/data",
        "src/synthesis",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "state",
    ]
    
    project_root = get_path(".")
    missing = []
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            missing.append(dir_name)
        elif not dir_path.is_dir():
            missing.append(f"{dir_name} (exists but is not a directory)")
    
    assert len(missing) == 0, f"Missing required directories: {', '.join(missing)}"

def test_directory_setup_script_exists():
    """Verify that the directory setup script exists."""
    project_root = get_path(".")
    setup_script = project_root / "setup_directories.py"
    assert setup_script.exists(), f"Setup script not found at {setup_script}"
    assert setup_script.is_file(), f"Setup script path is not a file: {setup_script}"