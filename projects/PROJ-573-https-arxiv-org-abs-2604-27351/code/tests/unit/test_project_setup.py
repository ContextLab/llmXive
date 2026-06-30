"""
Unit tests for project setup and configuration.
"""
import os
import sys
import pytest
from pathlib import Path

def test_project_structure_exists():
    """Verify that the standard project directory structure exists."""
    project_root = Path(__file__).parent.parent.parent
    required_dirs = [
        "code/src",
        "code/tests",
        "code/data",
        "code/state",
        "code/contracts",
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists at project root."""
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / "pyproject.toml"
    assert config_file.exists(), "pyproject.toml not found"
    assert config_file.is_file(), "pyproject.toml is not a file"

def test_requirements_exists():
    """Verify that requirements.txt exists at project root."""
    project_root = Path(__file__).parent.parent.parent
    req_file = project_root / "requirements.txt"
    assert req_file.exists(), "requirements.txt not found"
    assert req_file.is_file(), "requirements.txt is not a file"

    # Verify Python 3.11 is specified
    content = req_file.read_text()
    # Check for key dependencies
    assert "numpy" in content, "numpy dependency missing"
    assert "pandas" in content, "pandas dependency missing"
    assert "pyyaml" in content, "pyyaml dependency missing"

def test_setup_script_exists():
    """Verify that setup_project.py exists and is importable."""
    project_root = Path(__file__).parent.parent.parent
    setup_script = project_root / "setup_project.py"
    assert setup_script.exists(), "setup_project.py not found"

    # Verify it can be imported
    sys.path.insert(0, str(project_root))
    try:
        import setup_project
        assert hasattr(setup_project, "main"), "setup_project missing main function"
    finally:
        sys.path.pop(0)
