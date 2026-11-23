import os
import pytest
from pathlib import Path

def test_t002_code_directory_exists():
    """Verify that the code/ directory exists."""
    code_dir = Path("code")
    assert code_dir.exists(), "The code/ directory does not exist."
    assert code_dir.is_dir(), "The code/ path is not a directory."

def test_t002_code_utils_directory_exists():
    """Verify that the code/utils/ directory exists."""
    utils_dir = Path("code/utils")
    assert utils_dir.exists(), "The code/utils/ directory does not exist."
    assert utils_dir.is_dir(), "The code/utils/ path is not a directory."

def test_t002_code_models_directory_exists():
    """Verify that the code/models/ directory exists."""
    models_dir = Path("code/models")
    assert models_dir.exists(), "The code/models/ directory does not exist."
    assert models_dir.is_dir(), "The code/models/ path is not a directory."

def test_t002_gitkeep_files_exist():
    """Verify that .gitkeep files exist in the required directories."""
    gitkeep_files = [
        "code/.gitkeep",
        "code/utils/.gitkeep",
        "code/models/.gitkeep"
    ]
    for file_path in gitkeep_files:
        p = Path(file_path)
        assert p.exists(), f"The file {file_path} does not exist."
        assert p.is_file(), f"The path {file_path} is not a file."