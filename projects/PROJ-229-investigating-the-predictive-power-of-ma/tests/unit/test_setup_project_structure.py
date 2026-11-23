import os
import pytest
from pathlib import Path
from config import get_config
from code.setup_project_structure import create_project_structure

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root for testing."""
    # Mock config to use temp_path
    import code.config as config_module
    original_get_config = config_module.get_config
    
    def mock_get_config():
        cfg = original_get_config()
        cfg['project_root'] = str(tmp_path)
        return cfg
    
    config_module.get_config = mock_get_config
    yield tmp_path
    config_module.get_config = original_get_config

def test_creates_code_directories(temp_project_root):
    """Test that T001b code directories are created."""
    required_dirs = ['code/data', 'code/models', 'code/utils']
    
    assert create_project_structure() is True
    
    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_creates_test_directories(temp_project_root):
    """Test that T001c test directories are created."""
    required_dirs = ['tests/unit', 'tests/integration', 'tests/contract']
    
    # Re-run to ensure it doesn't fail if dirs exist
    create_project_structure()
    
    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_idempotent_creation(temp_project_root):
    """Test that running twice doesn't cause errors."""
    assert create_project_structure() is True
    # Run again
    assert create_project_structure() is True