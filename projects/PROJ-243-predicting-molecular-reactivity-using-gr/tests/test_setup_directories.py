import os
import pytest
from config import get_config, ensure_directories

def test_directories_exist():
    """Verify that all required directories are created by ensure_directories."""
    ensure_directories()
    config = get_config()
    
    required_dirs = [
        config.data_raw,
        config.data_processed,
        config.data_assets,
        config.code_dir,
        config.tests_dir,
        config.artifacts_dir,
        config.artifacts_logs,
    ]
    
    for dir_path in required_dirs:
        assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"

def test_data_raw_exists():
    """Specific check for T001a: data/raw must exist."""
    ensure_directories()
    config = get_config()
    assert os.path.isdir(config.data_raw), "data/raw directory is missing"