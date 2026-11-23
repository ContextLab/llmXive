import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.setup_directories import setup_data_directories
from src.utils.config import Config, reset_config

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    # Save original config
    original_config = None
    if hasattr(Config, '_instance'):
        original_config = Config._instance
    
    # Set up temp config
    reset_config()
    Config._instance = Config(data_root=temp_dir)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    # Restore original config
    if original_config:
        Config._instance = original_config
    else:
        reset_config()

class TestDirectorySetup:
    def test_setup_creates_required_directories(self, temp_config_dir):
        """Test that setup_data_directories creates all required directories."""
        result = setup_data_directories()
        assert result is True, "Directory setup should return True on success"
        
        data_root = Path(temp_config_dir)
        required_dirs = [
            data_root / "raw",
            data_root / "processed",
            data_root / "traits",
            data_root / "manifests",
            data_root / "synthetic"
        ]
        
        for dir_path in required_dirs:
            assert dir_path.exists(), f"Directory {dir_path} should exist"
            assert dir_path.is_dir(), f"{dir_path} should be a directory"
            assert os.access(dir_path, os.W_OK), f"{dir_path} should be writable"

    def test_setup_creates_flag_file(self, temp_config_dir):
        """Test that setup_data_directories creates the flag file."""
        result = setup_data_directories()
        assert result is True, "Directory setup should return True on success"
        
        flag_file = Path(temp_config_dir) / ".dir_setup_complete"
        assert flag_file.exists(), "Flag file should exist"
        assert flag_file.is_file(), "Flag file should be a file"
        
        with open(flag_file, 'r') as f:
            content = f.read()
            assert "Directory setup completed successfully" in content, \
                "Flag file should contain success message"

    def test_setup_idempotent(self, temp_config_dir):
        """Test that running setup multiple times doesn't cause errors."""
        # Run setup twice
        result1 = setup_data_directories()
        result2 = setup_data_directories()
        
        assert result1 is True, "First setup should succeed"
        assert result2 is True, "Second setup should succeed"
        
        # Verify directories still exist
        data_root = Path(temp_config_dir)
        required_dirs = [
            data_root / "raw",
            data_root / "processed",
            data_root / "traits",
            data_root / "manifests",
            data_root / "synthetic"
        ]
        
        for dir_path in required_dirs:
            assert dir_path.exists(), f"Directory {dir_path} should exist after multiple setups"
