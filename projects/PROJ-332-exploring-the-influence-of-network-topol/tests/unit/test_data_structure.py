"""
Test suite for T007: Verify data directory structure and .gitkeep files.
"""
import os
import pytest

@pytest.fixture
def project_root():
    """Get the project root directory (parent of 'code' and 'data')."""
    # Assuming this test runs from the project root or code/
    current = os.path.dirname(os.path.abspath(__file__))
    # Navigate up to find 'code' and 'data' siblings
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, 'code')) and os.path.exists(os.path.join(current, 'data')):
            return current
        current = os.path.dirname(current)
    # Fallback if not found (should not happen in valid repo)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_data_root_exists(project_root):
    """Verify data/ directory exists."""
    data_dir = os.path.join(project_root, 'data')
    assert os.path.isdir(data_dir), f"Directory 'data/' does not exist at {data_dir}"

def test_raw_dir_exists(project_root):
    """Verify data/raw/ directory exists."""
    raw_dir = os.path.join(project_root, 'data', 'raw')
    assert os.path.isdir(raw_dir), f"Directory 'data/raw/' does not exist at {raw_dir}"

def test_processed_dir_exists(project_root):
    """Verify data/processed/ directory exists."""
    processed_dir = os.path.join(project_root, 'data', 'processed')
    assert os.path.isdir(processed_dir), f"Directory 'data/processed/' does not exist at {processed_dir}"

def test_gitkeep_in_data(project_root):
    """Verify .gitkeep exists in data/."""
    gitkeep_path = os.path.join(project_root, 'data', '.gitkeep')
    assert os.path.isfile(gitkeep_path), f".gitkeep missing in 'data/' at {gitkeep_path}"

def test_gitkeep_in_raw(project_root):
    """Verify .gitkeep exists in data/raw/."""
    gitkeep_path = os.path.join(project_root, 'data', 'raw', '.gitkeep')
    assert os.path.isfile(gitkeep_path), f".gitkeep missing in 'data/raw/' at {gitkeep_path}"

def test_gitkeep_in_processed(project_root):
    """Verify .gitkeep exists in data/processed/."""
    gitkeep_path = os.path.join(project_root, 'data', 'processed', '.gitkeep')
    assert os.path.isfile(gitkeep_path), f".gitkeep missing in 'data/processed/' at {gitkeep_path}"