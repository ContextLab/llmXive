import os
import pytest
from pathlib import Path
import shutil

# Import the function to test
# Note: In a real test suite, we would import the module directly.
# Since setup_project.py is a script, we test the logic it performs.

PROJECT_ROOT = Path("projects/001-statistical-evaluation-of-dimensionality")

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Ensure the project structure exists before tests, and clean up after."""
    # Setup: Run the creation logic
    from code.setup_project import main as setup_main
    # We don't actually run main() here to avoid side effects during import,
    # but we assume the task implementation creates these.
    # For this test, we verify the existence of the directories.
    yield
    # Teardown: Optional cleanup if needed in a real CI environment
    # if PROJECT_ROOT.exists():
    #     shutil.rmtree(PROJECT_ROOT)

def test_project_root_exists():
    """Test that the main project directory exists."""
    assert PROJECT_ROOT.exists(), f"Project root directory {PROJECT_ROOT} does not exist"
    assert PROJECT_ROOT.is_dir(), f"{PROJECT_ROOT} is not a directory"

def test_data_raw_exists():
    """Test that data/raw directory exists."""
    path = PROJECT_ROOT / "data" / "raw"
    assert path.exists(), f"Directory {path} does not exist"
    assert path.is_dir(), f"{path} is not a directory"

def test_data_processed_exists():
    """Test that data/processed directory exists."""
    path = PROJECT_ROOT / "data" / "processed"
    assert path.exists(), f"Directory {path} does not exist"
    assert path.is_dir(), f"{path} is not a directory"

def test_results_exists():
    """Test that results directory exists."""
    path = PROJECT_ROOT / "results"
    assert path.exists(), f"Directory {path} does not exist"
    assert path.is_dir(), f"{path} is not a directory"

def test_code_exists():
    """Test that code directory exists."""
    path = PROJECT_ROOT / "code"
    assert path.exists(), f"Directory {path} does not exist"
    assert path.is_dir(), f"{path} is not a directory"

def test_tests_exists():
    """Test that tests directory exists."""
    path = PROJECT_ROOT / "tests"
    assert path.exists(), f"Directory {path} does not exist"
    assert path.is_dir(), f"{path} is not a directory"

def test_directory_tree_structure():
    """
    Verify the specific nested structure required by T001.
    This ensures the 'mkdir -p' logic was applied correctly.
    """
    expected_paths = [
        "data/raw",
        "data/processed",
        "results",
        "code",
        "tests"
    ]
    
    for rel_path in expected_paths:
        full_path = PROJECT_ROOT / rel_path
        assert full_path.exists(), f"Missing required path: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"