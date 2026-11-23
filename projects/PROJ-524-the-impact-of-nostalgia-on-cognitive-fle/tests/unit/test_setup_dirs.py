import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock config to use temp directory
@pytest.fixture
def temp_project_root():
    root = tempfile.mkdtemp()
    yield root
    shutil.rmtree(root)

def test_create_required_directories(temp_project_root):
    """
    Test that create_required_directories creates all required folders.
    """
    # Patch get_config to return our temp root
    with patch('setup_dirs.get_config') as mock_config:
        mock_config.return_value = {'base_path': temp_project_root}
        
        # Import after patching to ensure it picks up the mock
        from code.setup_dirs import create_required_directories
        
        result = create_required_directories()
        
        # Expected directories relative to temp_project_root
        expected_dirs = [
            'data/raw',
            'data/processed',
            'data/results',
            'data/stimuli',
            'contracts',
            'code',
            'tests',
            'paper'
        ]
        
        for rel_dir in expected_dirs:
            full_path = Path(temp_project_root) / rel_dir
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"
        
        assert result == len(expected_dirs), "Incorrect number of directories reported"

def test_idempotency(temp_project_root):
    """
    Test that running the function twice doesn't raise errors.
    """
    with patch('setup_dirs.get_config') as mock_config:
        mock_config.return_value = {'base_path': temp_project_root}
        
        from code.setup_dirs import create_required_directories
        
        # Run twice
        create_required_directories()
        result_second = create_required_directories()
        
        # Should still succeed
        assert result_second > 0
