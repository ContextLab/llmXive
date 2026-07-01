"""
Unit tests to verify the project structure was created correctly.
"""
import os
import pytest
from pathlib import Path

# Define the expected project root
PROJECT_ROOT = Path("projects/PROJ-056-the-impact-of-musical-training-on-functi")

# Define expected directories
EXPECTED_DIRS = [
    "code/data",
    "code/analysis",
    "code/utils",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "data/raw",
    "data/processed",
    "specs/001-the-impact-of-musical-training-on-functi",
    "contracts",
]

def test_project_root_exists():
    """Test that the project root directory exists."""
    assert PROJECT_ROOT.exists(), f"Project root {PROJECT_ROOT} does not exist"
    assert PROJECT_ROOT.is_dir(), f"{PROJECT_ROOT} is not a directory"

@pytest.mark.parametrize("dir_path", EXPECTED_DIRS)
def test_directory_exists(dir_path):
    """Test that each expected directory exists."""
    full_path = PROJECT_ROOT / dir_path
    assert full_path.exists(), f"Directory {dir_path} does not exist"
    assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_code_structure():
    """Test that the code subdirectories exist."""
    code_dir = PROJECT_ROOT / "code"
    assert code_dir.exists() and code_dir.is_dir()
    
    subdirs = ["data", "analysis", "utils"]
    for subdir in subdirs:
        assert (code_dir / subdir).exists() and (code_dir / subdir).is_dir()

def test_tests_structure():
    """Test that the tests subdirectories exist."""
    tests_dir = PROJECT_ROOT / "tests"
    assert tests_dir.exists() and tests_dir.is_dir()
    
    subdirs = ["unit", "integration", "contract"]
    for subdir in subdirs:
        assert (tests_dir / subdir).exists() and (tests_dir / subdir).is_dir()

def test_data_structure():
    """Test that the data subdirectories exist."""
    data_dir = PROJECT_ROOT / "data"
    assert data_dir.exists() and data_dir.is_dir()
    
    subdirs = ["raw", "processed"]
    for subdir in subdirs:
        assert (data_dir / subdir).exists() and (data_dir / subdir).is_dir()

def test_specs_and_contracts_exist():
    """Test that specs and contracts directories exist."""
    specs_dir = PROJECT_ROOT / "specs" / "001-the-impact-of-musical-training-on-functi"
    contracts_dir = PROJECT_ROOT / "contracts"
    
    assert specs_dir.exists() and specs_dir.is_dir()
    assert contracts_dir.exists() and contracts_dir.is_dir()

def test_readme_exists():
    """Test that README.md exists in the project root."""
    readme_path = PROJECT_ROOT / "README.md"
    assert readme_path.exists(), "README.md does not exist in project root"
    assert readme_path.is_file(), "README.md is not a file"
    
    # Check that it has content
    content = readme_path.read_text()
    assert len(content) > 0, "README.md is empty"
    assert "PROJ-056" in content, "README.md does not contain project identifier"
