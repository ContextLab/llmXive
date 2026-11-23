"""
Basic test to verify the project directory structure exists.
"""
import os
import pytest

REQUIRED_DIRS = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "results",
    "state",
    "contracts",
    "logs",
    "docs"
]

REQUIRED_FILES = [
    "requirements.txt",
    "config.yaml",
    "pyproject.toml"
]

def test_directories_exist():
    """Assert that all required directories exist."""
    missing = []
    for d in REQUIRED_DIRS:
        if not os.path.isdir(d):
            missing.append(d)
    assert not missing, f"Missing directories: {missing}"

def test_config_files_exist():
    """Assert that required configuration files exist."""
    missing = []
    for f in REQUIRED_FILES:
        if not os.path.isfile(f):
            missing.append(f)
    assert not missing, f"Missing config files: {missing}"
