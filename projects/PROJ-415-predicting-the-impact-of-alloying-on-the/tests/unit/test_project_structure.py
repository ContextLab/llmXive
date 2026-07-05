"""
Unit tests to verify the project structure was created correctly.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "code/utils",
    "code/data",
    "code/models",
    "code/validation",
    "tests",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "data",
    "data/raw",
    "data/curated",
    "data/artifacts",
    "data/logs",
    "models",
    "reports",
    "figures"
]

REQUIRED_PACKAGES = [
    "code",
    "code/utils",
    "code/data",
    "code/models",
    "code/validation",
    "tests",
    "tests/unit",
    "tests/contract",
    "tests/integration"
]

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path.cwd()

def test_required_directories_exist(project_root):
    """Verify all required directories exist."""
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

def test_init_files_exist(project_root):
    """Verify __init__.py files exist for Python packages."""
    for dir_path in REQUIRED_PACKAGES:
        init_file = project_root / dir_path / "__init__.py"
        assert init_file.exists(), f"__init__.py missing: {init_file}"
        assert init_file.is_file(), f"Not a file: {init_file}"

def test_data_subdirectories_exist(project_root):
    """Verify data subdirectories exist."""
    data_subdirs = ["raw", "curated", "artifacts", "logs"]
    for subdir in data_subdirs:
        full_path = project_root / "data" / subdir
        assert full_path.exists(), f"Data subdirectory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

def test_tests_subdirectories_exist(project_root):
    """Verify test subdirectories exist."""
    test_subdirs = ["unit", "contract", "integration"]
    for subdir in test_subdirs:
        full_path = project_root / "tests" / subdir
        assert full_path.exists(), f"Test subdirectory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"