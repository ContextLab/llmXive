"""
Unit tests to verify the project structure creation.
"""
import os
import pytest
import subprocess
import sys

REQUIRED_DIRS = [
    "src/models",
    "src/services",
    "src/analysis",
    "src/cli",
    "src/utils",
    "data/raw",
    "data/processed",
    "tests/unit",
    "tests/integration",
    "docs"
]

def test_setup_script_creates_directories(tmp_path):
    """
    Runs the setup script in a temporary directory and verifies
    that all required directories are created.
    """
    # Change to temp directory
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run the setup script
        result = subprocess.run(
            [sys.executable, "code/setup_project_structure.py"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        # Verify directories exist
        missing_dirs = []
        for d in REQUIRED_DIRS:
            if not os.path.isdir(d):
                missing_dirs.append(d)
        
        assert not missing_dirs, f"Missing directories: {missing_dirs}"
        
    finally:
        os.chdir(original_dir)

def test_required_directories_exist_in_root():
    """
    Check if directories exist in the current working directory (where tests are run).
    This ensures the project structure is present.
    """
    missing = []
    for d in REQUIRED_DIRS:
        if not os.path.isdir(d):
            missing.append(d)
    
    if missing:
        pytest.fail(f"Project structure incomplete. Missing: {missing}")
    else:
        # If they exist, verify they are directories
        for d in REQUIRED_DIRS:
            assert os.path.isdir(d), f"{d} exists but is not a directory"