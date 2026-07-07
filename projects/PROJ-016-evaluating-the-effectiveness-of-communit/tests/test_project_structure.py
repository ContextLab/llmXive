import os
import sys
from pathlib import Path
import pytest

def test_project_structure_exists():
    """Verify that the required project directories exist."""
    project_root = Path(__file__).resolve().parent.parent

    required_dirs = [
        "code/data",
        "code/analysis",
        "code/tests",
        "data/raw",
        "data/processed",
        "docs/output",
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

def test_code_init_exists():
    """Verify code/__init__.py exists."""
    project_root = Path(__file__).resolve().parent.parent
    init_file = project_root / "code" / "__init__.py"
    assert init_file.exists(), "code/__init__.py does not exist"

def test_requirements_exists():
    """Verify requirements.txt exists."""
    project_root = Path(__file__).resolve().parent.parent
    req_file = project_root / "requirements.txt"
    assert req_file.exists(), "requirements.txt does not exist"

def test_linting_config_exists():
    """Verify linting configuration files exist."""
    project_root = Path(__file__).resolve().parent.parent
    ruff_config = project_root / ".ruff.toml"
    pyproject = project_root / "pyproject.toml"
    
    assert ruff_config.exists(), ".ruff.toml does not exist"
    assert pyproject.exists(), "pyproject.toml does not exist"
    assert "[tool.black]" in pyproject.read_text(), "Black config missing in pyproject.toml"