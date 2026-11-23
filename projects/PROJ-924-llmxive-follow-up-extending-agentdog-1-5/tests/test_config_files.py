import os
import pytest
from pathlib import Path

# Project root is the parent of the 'tests' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_ruff_config_exists():
    """
    Verify that .ruff.toml exists and is non-empty.
    """
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    assert ruff_path.exists(), ".ruff.toml file does not exist in project root."
    assert ruff_path.stat().st_size > 0, ".ruff.toml file is empty."

def test_pyproject_config_exists():
    """
    Verify that pyproject.toml exists and is non-empty.
    """
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml file does not exist in project root."
    assert pyproject_path.stat().st_size > 0, "pyproject.toml file is empty."

def test_requirements_txt_exists():
    """
    Verify that requirements.txt exists and is non-empty (from T009).
    """
    req_path = PROJECT_ROOT / "requirements.txt"
    assert req_path.exists(), "requirements.txt file does not exist in project root."
    assert req_path.stat().st_size > 0, "requirements.txt file is empty."