import os
import pytest
from config import get_config

def test_data_directories_exist():
    """Test that required data directories exist after setup."""
    config = get_config()
    data_dirs = [
        config['data']['raw'],
        config['data']['processed'],
        config['data']['assets']
    ]
    
    for dir_path in data_dirs:
        assert os.path.exists(dir_path), f"Directory {dir_path} does not exist"
        assert os.path.isdir(dir_path), f"{dir_path} is not a directory"

def test_code_directories_exist():
    """Test that required code and test directories exist."""
    config = get_config()
    required_dirs = [
        config['paths']['code'],
        config['paths']['tests'],
        config['paths']['artifacts']
    ]
    
    for dir_path in required_dirs:
        assert os.path.exists(dir_path), f"Directory {dir_path} does not exist"
        assert os.path.isdir(dir_path), f"{dir_path} is not a directory"

def test_artifacts_directories_exist():
    """Test that required artifacts directories exist."""
    config = get_config()
    artifacts_dirs = [
        config['paths']['artifacts'],
        os.path.join(config['paths']['artifacts'], 'logs'),
        os.path.join(config['paths']['artifacts'], 'metrics')
    ]
    
    for dir_path in artifacts_dirs:
        assert os.path.exists(dir_path), f"Directory {dir_path} does not exist"
        assert os.path.isdir(dir_path), f"{dir_path} is not a directory"