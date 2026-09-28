import os
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch

# Mock config to use a temporary directory for testing
@pytest.fixture
def temp_project_root():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config(temp_project_root):
    # Patch get_config to return our temp directory as base_path
    with patch('setup_dirs.get_config') as mock_get_config:
        mock_get_config.return_value = {'base_path': temp_project_root}
        yield mock_get_config

def test_create_required_directories(temp_project_root, mock_config):
    """Test that all required directories are created."""
    from setup_dirs import create_required_directories

    required_dirs = [
        'data/raw',
        'data/processed',
        'data/results',
        'data/stimuli',
        'contracts',
        'code',
        'tests',
        'paper'
    ]

    # Verify directories don't exist initially
    for dir_name in required_dirs:
        assert not (temp_project_root / dir_name).exists()

    # Run the function
    created = create_required_directories()

    # Verify all directories now exist
    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

    # Verify the return value contains the created paths
    assert len(created) == len(required_dirs)
    for dir_name in required_dirs:
        assert str(temp_project_root / dir_name) in created

def test_create_required_directories_already_exist(temp_project_root, mock_config):
    """Test that the function handles existing directories gracefully."""
    from setup_dirs import create_required_directories

    # Pre-create some directories
    (temp_project_root / 'code').mkdir(parents=True, exist_ok=True)
    (temp_project_root / 'data').mkdir(parents=True, exist_ok=True)
    (temp_project_root / 'data/raw').mkdir(parents=True, exist_ok=True)

    # Run the function
    created = create_required_directories()

    # Only the new directories should be in the return list
    # (code and data/raw already existed)
    assert len(created) == 6  # 8 total - 2 existing
    assert str(temp_project_root / 'code') not in created
    assert str(temp_project_root / 'data/raw') not in created

def test_create_required_directories_nested(temp_project_root, mock_config):
    """Test that nested directories are created correctly."""
    from setup_dirs import create_required_directories

    # Ensure parent 'data' doesn't exist
    assert not (temp_project_root / 'data').exists()

    created = create_required_directories()

    # Verify nested structure
    assert (temp_project_root / 'data').exists()
    assert (temp_project_root / 'data/raw').exists()
    assert (temp_project_root / 'data/processed').exists()
    assert (temp_project_root / 'data/results').exists()
    assert (temp_project_root / 'data/stimuli').exists()
    assert (temp_project_root / 'contracts').exists()
    assert (temp_project_root / 'code').exists()
    assert (temp_project_root / 'tests').exists()
    assert (temp_project_root / 'paper').exists()
