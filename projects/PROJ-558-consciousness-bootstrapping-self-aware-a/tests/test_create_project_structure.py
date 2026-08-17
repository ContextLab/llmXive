import os
import shutil
from pathlib import Path
import pytest
from code.create_project_structure import create_structure

@pytest.fixture
def project_name():
    return "TEST-PROJ-558-TEMP"

@pytest.fixture
def cleanup_project(project_name):
    """Yields a clean project path and cleans it up after the test."""
    base_dir = Path("projects")
    project_dir = base_dir / project_name
    
    # Ensure it doesn't exist before the test
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    yield project_dir
    
    # Cleanup after test
    if project_dir.exists():
        shutil.rmtree(project_dir)

def test_create_structure_creates_all_directories(cleanup_project, project_name):
    """Test that create_structure creates the full directory tree."""
    create_structure(project_name)
    
    expected_subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results",
    ]
    
    for subdir in expected_subdirs:
        dir_path = cleanup_project / subdir
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

def test_create_structure_idempotent(cleanup_project, project_name):
    """Test that running create_structure twice doesn't raise errors."""
    create_structure(project_name)
    # Run again
    create_structure(project_name)
    
    # Verify structure still exists
    assert (cleanup_project / "code").exists()
    assert (cleanup_project / "data/raw").exists()

def test_create_structure_relative_to_root():
    """Test that the structure is created under 'projects/' relative to cwd."""
    test_name = "TEST-REL-ROOT"
    try:
        create_structure(test_name)
        assert Path("projects").exists()
        assert Path(f"projects/{test_name}").exists()
    finally:
        # Cleanup
        if Path(f"projects/{test_name}").exists():
            shutil.rmtree(f"projects/{test_name}")
