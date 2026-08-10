"""
Contract test for T003b: Verify Setup artifacts exist and are valid.

This test ensures that the directory structure (T001a) and linting
configuration (T003) are correctly in place before proceeding to Phase 2.
"""
import os
import yaml
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_DIR = PROJECT_ROOT / "projects" / "PROJ-799-statistical-properties-of-integer-partit"

REQUIRED_DIRS = [
    "code",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/schemas",
    "tests",
    "tests/data",
    "docs",
]

REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    "requirements.txt",
    ".flake8",
    "pyproject.toml",
]

def test_project_directory_exists():
    """Verify the main project directory exists."""
    assert PROJECT_DIR.exists(), f"Project directory {PROJECT_DIR} does not exist."

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_required_directories_exist(dir_name):
    """Verify all required subdirectories exist."""
    dir_path = PROJECT_DIR / dir_name
    assert dir_path.exists(), f"Required directory {dir_path} is missing."
    assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

@pytest.mark.parametrize("file_name", REQUIRED_FILES)
def test_required_files_exist(file_name):
    """Verify all required configuration and placeholder files exist."""
    file_path = PROJECT_DIR / file_name
    assert file_path.exists(), f"Required file {file_path} is missing."
    assert file_path.is_file(), f"{file_path} exists but is not a file."

def test_flake8_config_valid():
    """Verify .flake8 is a valid config file."""
    flake8_path = PROJECT_DIR / ".flake8"
    assert flake8_path.exists()
    content = flake8_path.read_text()
    assert "[flake8]" in content, ".flake8 must contain a [flake8] section."

def test_pyproject_black_config_valid():
    """Verify pyproject.toml contains Black configuration."""
    pyproject_path = PROJECT_DIR / "pyproject.toml"
    assert pyproject_path.exists()
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section."
    assert "line-length" in content, "Black config should specify line-length."

def test_state_directory_exists():
    """Verify the repository-level state directory exists (T001a requirement)."""
    state_dir = PROJECT_ROOT / "state"
    assert state_dir.exists(), f"State directory {state_dir} must exist at repo root."
    assert state_dir.is_dir(), f"{state_dir} must be a directory."

def test_project_state_file_exists():
    """Verify the project state YAML file exists."""
    state_file = PROJECT_ROOT / "state" / "projects" / "PROJ-799.yaml"
    assert state_file.exists(), f"State file {state_file} must exist."
    
    # Verify it can be parsed as YAML (even if empty or minimal)
    try:
        content = state_file.read_text()
        # Allow empty files, but if content exists, it should be valid YAML
        if content.strip():
            yaml.safe_load(content)
    except yaml.YAMLError as e:
        pytest.fail(f"State file {state_file} contains invalid YAML: {e}")
