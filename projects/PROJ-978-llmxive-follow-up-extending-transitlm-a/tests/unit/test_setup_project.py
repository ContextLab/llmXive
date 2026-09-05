import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.setup_project import create_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_create_directories_structure(temp_project_root):
    """
    Test that create_directories creates the expected directory structure.
    """
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/analysis",
        "models",
        "analysis",
        "tests",
        "docs"
    ]

    # Run the function
    create_directories()

    # Verify each directory exists
    for dir_name in expected_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

    # Verify nested structure for data
    data_raw = temp_project_root / "data" / "raw"
    data_processed = temp_project_root / "data" / "processed"
    data_analysis = temp_project_root / "data" / "analysis"
    
    assert data_raw.exists(), "data/raw was not created"
    assert data_processed.exists(), "data/processed was not created"
    assert data_analysis.exists(), "data/analysis was not created"

def test_create_directories_idempotent(temp_project_root):
    """
    Test that running create_directories multiple times does not cause errors.
    """
    # Run twice
    create_directories()
    create_directories()
    
    # Verify structure still exists
    expected_dirs = [
        "code", "data/raw", "data/processed", "data/analysis",
        "models", "analysis", "tests", "docs"
    ]
    for dir_name in expected_dirs:
        assert (temp_project_root / dir_name).exists()
