"""
Test for Task T001c: Verify data/results/ directory creation
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config

@pytest.fixture
def data_dir():
    """Get the data directory from config"""
    config = get_config()
    return Path(config.get('paths', {}).get('data', 'data'))

def test_results_directory_exists(data_dir):
    """
    Test that data/results/ directory exists after T001c execution.
    """
    results_dir = data_dir / 'results'
    
    # Assert directory exists
    assert results_dir.exists(), f"Directory {results_dir} does not exist"
    assert results_dir.is_dir(), f"{results_dir} is not a directory"
    
    # Check for .gitkeep placeholder (optional but good practice)
    gitkeep = results_dir / '.gitkeep'
    # Note: .gitkeep existence is not strictly required by the task,
    # but it's a common convention for empty directories in git
    # We don't assert on this to avoid false negatives if the script
    # was run without the placeholder creation logic

def test_results_directory_is_writable(data_dir):
    """
    Test that data/results/ directory is writable.
    """
    results_dir = data_dir / 'results'
    
    # Try to create a temporary test file
    test_file = results_dir / '.test_write_permissions'
    try:
        test_file.touch()
        assert test_file.exists()
        test_file.unlink()  # Clean up
    except Exception as e:
        pytest.fail(f"Directory {results_dir} is not writable: {e}")
