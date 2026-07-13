"""
Test suite to verify the project directory structure has been created correctly.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def expected_dirs():
    return [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "code/models",
        "code/analysis"
    ]

@pytest.fixture
def expected_init_dirs():
    return [
        "code",
        "code/data",
        "code/models",
        "code/analysis",
        "tests"
    ]

@pytest.fixture
def expected_gitkeep_dirs():
    return [
        "data/raw",
        "data/processed"
    ]

def test_directories_exist(expected_dirs):
    """Test that all required directories exist."""
    for dir_path in expected_dirs:
        assert Path(dir_path).exists(), f"Directory {dir_path} does not exist"
        assert Path(dir_path).is_dir(), f"{dir_path} is not a directory"

def test_init_files_exist(expected_init_dirs):
    """Test that __init__.py files exist in all required directories."""
    for dir_path in expected_init_dirs:
        init_file = Path(dir_path) / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {dir_path}"
        assert init_file.is_file(), f"{dir_path}/__init__.py is not a file"

def test_gitkeep_files_exist(expected_gitkeep_dirs):
    """Test that .gitkeep files exist in data directories."""
    for dir_path in expected_gitkeep_dirs:
        gitkeep_file = Path(dir_path) / ".gitkeep"
        assert gitkeep_file.exists(), f".gitkeep missing in {dir_path}"
        assert gitkeep_file.is_file(), f"{dir_path}/.gitkeep is not a file"

def test_code_data_directory_exists():
    """Test that code/data directory exists (needed for imports)."""
    assert Path("code/data").exists(), "code/data directory does not exist"
    assert Path("code/data").is_dir(), "code/data is not a directory"

def test_code_models_directory_exists():
    """Test that code/models directory exists (needed for imports)."""
    assert Path("code/models").exists(), "code/models directory does not exist"
    assert Path("code/models").is_dir(), "code/models is not a directory"

def test_code_analysis_directory_exists():
    """Test that code/analysis directory exists (needed for imports)."""
    assert Path("code/analysis").exists(), "code/analysis directory does not exist"
    assert Path("code/analysis").is_dir(), "code/analysis is not a directory"