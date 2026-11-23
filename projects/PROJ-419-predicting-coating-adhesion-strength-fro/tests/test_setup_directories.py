import os
import pytest
import shutil
from code.setup_directories import create_directory_structure

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_create_directory_structure(temp_test_dir):
    """Test that create_directory_structure creates the required directories."""
    # Expected directories relative to the temp_test_dir
    expected_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "state",
        "figures"
    ]

    # Verify directories don't exist before running
    for d in expected_dirs:
        assert not os.path.exists(d), f"Directory {d} should not exist before test"

    # Run the function
    result = create_directory_structure()

    # Verify return value
    assert result is True

    # Verify directories exist after running
    for d in expected_dirs:
        assert os.path.exists(d), f"Directory {d} should exist after creation"
        assert os.path.isdir(d), f"{d} should be a directory"

def test_create_directory_structure_idempotent(temp_test_dir):
    """Test that running create_directory_structure multiple times doesn't fail."""
    run1 = create_directory_structure()
    run2 = create_directory_structure()
    run3 = create_directory_structure()

    assert run1 is True
    assert run2 is True
    assert run3 is True