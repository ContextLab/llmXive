import os
import tempfile
import yaml
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import get_path, ensure_directories, get_config_dict, _PROJECT_ROOT

def test_get_path_default():
    """Test that get_path returns the correct default path."""
    # Assuming default config exists or fallback is used
    raw_dir = get_path('data', 'raw_dir')
    assert isinstance(raw_dir, Path)
    # Should be under project root
    assert raw_dir.is_absolute()

def test_get_path_nonexistent_key():
    """Test that get_path raises KeyError for missing keys."""
    with pytest.raises(KeyError):
        get_path('nonexistent_key', 'subkey')

def test_ensure_directories_creates_folders():
    """Test that ensure_directories creates the necessary folders."""
    # Create a temporary config to test directory creation
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_config = {
            'data': {
                'raw_dir': 'temp_test_raw',
                'processed_dir': 'temp_test_processed',
            },
            'paths': {}
        }
        yaml.dump(temp_config, f)
        temp_path = f.name

    try:
        # Set environment variable to use temp config
        os.environ['LLMXIVE_CONFIG_PATH'] = temp_path

        # Reload config by forcing a fresh import (or re-reading)
        # Since _load_config reads from env var, we can just call ensure_directories
        # But we need to clear any cached state if the module caches the config.
        # Our implementation reads fresh every time, so it should work.
        ensure_directories()

        # Check if directories were created relative to project root
        raw_dir = _PROJECT_ROOT / 'temp_test_raw'
        processed_dir = _PROJECT_ROOT / 'temp_test_processed'

        assert raw_dir.exists()
        assert processed_dir.exists()

        # Cleanup
        import shutil
        if raw_dir.exists():
            shutil.rmtree(raw_dir)
        if processed_dir.exists():
            shutil.rmtree(processed_dir)

    finally:
        # Clean up env var and temp file
        if 'LLMXIVE_CONFIG_PATH' in os.environ:
            del os.environ['LLMXIVE_CONFIG_PATH']
        os.unlink(temp_path)

def test_get_config_dict_returns_dict():
    """Test that get_config_dict returns a dictionary."""
    config = get_config_dict()
    assert isinstance(config, dict)
    assert 'data' in config
