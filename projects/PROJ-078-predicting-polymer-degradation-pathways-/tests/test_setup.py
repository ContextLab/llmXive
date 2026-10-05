import os
import pytest
from pathlib import Path
import subprocess
import sys

def test_directories_exist():
    """Test that all required directories exist after setup."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state",
        "state/projects"
    ]
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_setup_log_exists():
    """Test that the setup log file was created."""
    log_path = Path("state/setup_log.txt")
    assert log_path.exists(), "Setup log file does not exist"
    
    # Check that it contains non-empty content
    with open(log_path, 'r') as f:
        content = f.read()
        assert len(content) > 0, "Setup log file is empty"
        assert "Project Setup Log" in content, "Setup log does not contain expected header"

def test_setup_script_runs():
    """Test that the setup script runs without errors."""
    result = subprocess.run(
        [sys.executable, "code/setup_project.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"