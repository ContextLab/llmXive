"""
Tests for the project setup script.
Verifies that the required directory structure is created correctly.
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

@pytest.fixture
def required_dirs():
    """List of required directories relative to project root."""
    return [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/logs",
        "artifacts/plots",
        "artifacts/reports",
        "contracts"
    ]

def test_setup_script_runs_successfully(project_root):
    """Test that the setup script runs without errors."""
    setup_script = project_root / "code" / "setup_project.py"
    
    result = subprocess.run(
        [sys.executable, str(setup_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Setup script failed with:\n{result.stderr}"

def test_required_directories_exist(project_root, required_dirs):
    """Test that all required directories exist after setup."""
    # Run setup first to ensure directories are created
    setup_script = project_root / "code" / "setup_project.py"
    subprocess.run(
        [sys.executable, str(setup_script)],
        cwd=project_root,
        check=True
    )
    
    # Verify each directory exists
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Required directory missing: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"

def test_directory_structure_is_correct(project_root, required_dirs):
    """Test that the directory structure matches the specification."""
    # Run setup first
    setup_script = project_root / "code" / "setup_project.py"
    subprocess.run(
        [sys.executable, str(setup_script)],
        cwd=project_root,
        check=True
    )
    
    # Verify the exact structure
    expected_structure = {
        "data": ["raw", "processed"],
        "artifacts": ["logs", "plots", "reports"]
    }
    
    for parent, children in expected_structure.items():
        parent_path = project_root / parent
        assert parent_path.exists(), f"Parent directory missing: {parent_path}"
        
        for child in children:
            child_path = parent_path / child
            assert child_path.exists(), f"Child directory missing: {child_path}"
            assert child_path.is_dir(), f"Path is not a directory: {child_path}"