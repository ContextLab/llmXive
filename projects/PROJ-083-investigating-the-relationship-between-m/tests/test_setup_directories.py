import os
import tempfile
import shutil
import pytest

# Import the function to test
from code.setup_directories import setup_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_setup_directories_creates_all_paths(temp_project_root, monkeypatch):
    """
    Verify that setup_directories creates the required directory structure.
    """
    # Change the current working directory to the temp project root
    monkeypatch.chdir(temp_project_root)

    # Run the setup function
    result = setup_directories()

    assert result is True

    # Define expected directories relative to the root
    expected_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/models",
        "code",
        "tests",
        "docs",
        "docs/reports",
        "specs",
        "specs/001-molecular-topology-selectivity",
        "contracts",
    ]

    for dir_name in expected_dirs:
        full_path = os.path.join(temp_project_root, dir_name)
        assert os.path.exists(full_path), f"Directory {full_path} was not created."
        assert os.path.isdir(full_path), f"{full_path} exists but is not a directory."

def test_setup_directories_idempotent(temp_project_root, monkeypatch):
    """
    Verify that running setup_directories twice does not cause errors.
    """
    monkeypatch.chdir(temp_project_root)

    # Run setup twice
    setup_directories()
    result_second_run = setup_directories()

    assert result_second_run is True

    # Verify directories still exist
    assert os.path.exists(os.path.join(temp_project_root, "data/raw"))
    assert os.path.exists(os.path.join(temp_project_root, "code"))