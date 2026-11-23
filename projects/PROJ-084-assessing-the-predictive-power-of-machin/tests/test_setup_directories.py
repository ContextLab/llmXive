import os
import pytest
from pathlib import Path
import sys

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_directories import main

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to simulate project root."""
    # Change to temp dir to test directory creation
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_directories_created(temp_project_root):
    """Test that all required directories are created."""
    # Run the main function
    main()

    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]

    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_existing_directories_not_overwritten(temp_project_root):
    """Test that existing directories are handled gracefully."""
    # Pre-create one directory
    pre_created = temp_project_root / "code"
    pre_created.mkdir(parents=True, exist_ok=True)

    # Run main
    main()

    # Should still exist and be a directory
    assert pre_created.exists()
    assert pre_created.is_dir()
    # Should contain __init__.py or other files if they existed before
    # (though we didn't add any, it should still be there)