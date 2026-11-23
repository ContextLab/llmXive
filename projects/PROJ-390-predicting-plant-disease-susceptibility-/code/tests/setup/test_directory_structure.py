"""
Test suite for T002a: Directory Structure Creation.

Verifies that the required directories exist and the verification file is generated.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "models",
    "templates"
]

@pytest.fixture
def project_root():
    """Returns the project root path (current working directory)."""
    return Path.cwd()

def test_required_directories_exist(project_root):
    """Assert that all required directories created by T002a exist."""
    missing = []
    for dir_name in REQUIRED_DIRS:
        path = project_root / dir_name
        if not path.exists():
            missing.append(dir_name)
        elif not path.is_dir():
            missing.append(dir_name)
    
    assert len(missing) == 0, f"The following required directories are missing: {missing}"

def test_nested_data_directories_exist(project_root):
    """Assert that nested data directories (raw, processed) exist."""
    raw_path = project_root / "data" / "raw"
    processed_path = project_root / "data" / "processed"
    
    assert raw_path.exists(), "data/raw directory missing"
    assert processed_path.exists(), "data/processed directory missing"
    assert raw_path.is_dir(), "data/raw is not a directory"
    assert processed_path.is_dir(), "data/processed is not a directory"

def test_verification_file_generated(project_root):
    """Assert that the verification artifact was created."""
    verification_file = project_root / "data" / "processed" / "directory_structure.txt"
    assert verification_file.exists(), "Verification file data/processed/directory_structure.txt not found"
    
    content = verification_file.read_text()
    assert "Directories created/verified:" in content, "Verification file missing expected header"
    assert "Summary:" in content, "Verification file missing summary section"
    
    # Verify at least one directory is listed as existing
    assert "YES" in content, "Verification file does not indicate any existing directories"

def test_directory_structure_is_valid(project_root):
    """Additional check: ensure src and tests have __init__.py or are valid Python packages if they contain code."""
    # Basic check: they are directories. Content validation is handled by other tasks.
    src_path = project_root / "src"
    tests_path = project_root / "tests"
    
    assert src_path.is_dir(), "src is not a directory"
    assert tests_path.is_dir(), "tests is not a directory"