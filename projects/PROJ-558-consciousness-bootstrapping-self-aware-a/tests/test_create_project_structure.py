import os
import shutil
from pathlib import Path
import pytest

from code.create_project_structure import create_structure

@pytest.fixture
def temp_project_root(tmp_path):
    """
    Setup a temporary directory to simulate the project root.
    We change the current working directory to this temp dir to ensure
    relative paths in create_structure behave correctly during tests.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)
    # Cleanup: remove the created project structure if it exists
    project_dir = tmp_path / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
    if project_dir.exists():
        shutil.rmtree(project_dir)

def test_create_structure_creates_all_directories(temp_project_root):
    """
    Verify that create_structure() creates all required directories.
    """
    # Execute the function
    created_count = create_structure()
    
    # Define expected paths relative to the temp root
    base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    expected_paths = [
        base_dir,
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "code",
        base_dir / "tests",
        base_dir / "artifacts" / "checkpoints",
        base_dir / "artifacts" / "results",
    ]
    
    # Verify all directories exist
    for path in expected_paths:
        assert path.exists(), f"Directory {path} was not created."
        assert path.is_dir(), f"{path} exists but is not a directory."
    
    # Verify the count of created directories (should be 7 in a clean run)
    # Note: The function returns the count of directories it actually created (mkdir called).
    # Since we just created them, count should match the number of unique paths.
    assert created_count == len(expected_paths), f"Expected {len(expected_paths)} directories created, got {created_count}."

def test_create_structure_idempotent(temp_project_root):
    """
    Verify that running create_structure() twice does not fail and creates 0 new dirs on second run.
    """
    # First run
    first_count = create_structure()
    assert first_count > 0, "First run should create directories."
    
    # Second run
    second_count = create_structure()
    assert second_count == 0, "Second run should not create any new directories."
    
    # Verify paths still exist
    base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    assert (base_dir / "data" / "raw").exists()
    assert (base_dir / "artifacts" / "results").exists()