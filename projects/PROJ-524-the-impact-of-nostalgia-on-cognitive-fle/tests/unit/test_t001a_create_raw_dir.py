"""
Unit tests for Task T001a: Create data/raw directory.
"""
import os
import tempfile
import shutil
from pathlib import Path

import pytest

# Mock config to avoid dependency on full config loading during unit test
class MockConfig:
    def __init__(self, tmp_dir):
        self.tmp_dir = tmp_dir
        self.data = {"data_root": str(tmp_dir)}

    def get(self, key, default=None):
        return self.data.get(key, default)

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for testing."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)

def test_create_raw_directory_creates_dir(temp_config_dir):
    """Test that create_raw_directory creates the directory if it doesn't exist."""
    # Patch config to use temp dir
    import code.task_t001a_create_raw_dir as task_module
    from code import config

    original_get_config = config.get_config
    
    def mock_get_config():
        return MockConfig(temp_config_dir)

    config.get_config = mock_get_config
    
    try:
        raw_dir = temp_config_dir / "raw"
        assert not raw_dir.exists(), "Raw dir should not exist before test"
        
        result = task_module.create_raw_directory()
        
        assert result == raw_dir
        assert raw_dir.exists()
        assert raw_dir.is_dir()
    finally:
        config.get_config = original_get_config

def test_create_raw_directory_existing_dir(temp_config_dir):
    """Test that create_raw_directory returns existing path if dir already exists."""
    import code.task_t001a_create_raw_dir as task_module
    from code import config

    original_get_config = config.get_config
    
    def mock_get_config():
        return MockConfig(temp_config_dir)

    config.get_config = mock_get_config
    
    try:
        raw_dir = temp_config_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        result = task_module.create_raw_directory()
        
        assert result == raw_dir
        assert raw_dir.exists()
    finally:
        config.get_config = original_get_config

def test_main_execution(temp_config_dir, caplog):
    """Test the main entry point execution."""
    import code.task_t001a_create_raw_dir as task_module
    from code import config

    original_get_config = config.get_config
    
    def mock_get_config():
        return MockConfig(temp_config_dir)

    config.get_config = mock_get_config
    
    try:
        # Mock setup_logging to avoid cluttering test output
        import code.utils as utils
        original_setup = utils.setup_logging
        utils.setup_logging = lambda **kwargs: None
        
        try:
            exit_code = task_module.main()
            assert exit_code == 0
        finally:
            utils.setup_logging = original_setup
    finally:
        config.get_config = original_get_config