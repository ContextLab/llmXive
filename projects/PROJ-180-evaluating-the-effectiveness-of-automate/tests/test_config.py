import os
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the module under test
# Note: We assume the test runner sets up the path correctly
# or we add the code directory to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.config import (
    get_config,
    get_github_token,
    get_data_raw_dir,
    get_data_processed_dir,
    get_results_dir,
    get_max_repos,
    get_retry_count,
    get_log_level,
    validate_paths,
    load_env
)

@pytest.fixture
def mock_env_vars():
    """Fixture to provide mock environment variables"""
    return {
        'GITHUB_TOKEN': 'test_token_123',
        'DATA_RAW_DIR': 'test_data/raw',
        'DATA_PROCESSED_DIR': 'test_data/processed',
        'RESULTS_DIR': 'test_results',
        'MAX_REPOS': '10',
        'RETRY_COUNT': '3',
        'LOG_LEVEL': 'DEBUG'
    }

def test_get_config_uses_env_vars(mock_env_vars):
    """Test that config values are overridden by environment variables"""
    with patch.dict(os.environ, mock_env_vars):
        config = get_config()
        assert config['GITHUB_TOKEN'] == 'test_token_123'
        assert config['DATA_RAW_DIR'] == 'test_data/raw'
        assert config['MAX_REPOS'] == 10
        assert config['RETRY_COUNT'] == 3
        assert config['LOG_LEVEL'] == 'DEBUG'

def test_get_github_token_returns_token(mock_env_vars):
    """Test that GitHub token is retrieved correctly"""
    with patch.dict(os.environ, mock_env_vars):
        token = get_github_token()
        assert token == 'test_token_123'

def test_get_github_token_returns_none_when_missing():
    """Test that None is returned when token is missing"""
    with patch.dict(os.environ, {}, clear=True):
        token = get_github_token()
        assert token is None

def test_get_data_raw_dir_returns_path(mock_env_vars):
    """Test that raw data directory is returned as Path object"""
    with patch.dict(os.environ, mock_env_vars):
        raw_dir = get_data_raw_dir()
        assert isinstance(raw_dir, Path)
        assert str(raw_dir) == 'test_data/raw'

def test_get_max_repos_parses_integer(mock_env_vars):
    """Test that MAX_REPOS is parsed as integer"""
    with patch.dict(os.environ, mock_env_vars):
        max_repos = get_max_repos()
        assert isinstance(max_repos, int)
        assert max_repos == 10

def test_get_max_repos_uses_default_when_invalid(mock_env_vars):
    """Test that default is used when MAX_REPOS is invalid"""
    mock_env_vars['MAX_REPOS'] = 'invalid'
    with patch.dict(os.environ, mock_env_vars):
        max_repos = get_max_repos()
        assert isinstance(max_repos, int)
        assert max_repos == 40  # Default value

def test_get_log_level_returns_correct_constant(mock_env_vars):
    """Test that LOG_LEVEL is converted to logging constant"""
    import logging
    with patch.dict(os.environ, mock_env_vars):
        level = get_log_level()
        assert level == logging.DEBUG

def test_validate_paths_creates_directories(tmp_path, mock_env_vars):
    """Test that validate_paths creates missing directories"""
    # Use temporary directory for testing
    test_env = {
        'DATA_RAW_DIR': str(tmp_path / 'raw'),
        'DATA_PROCESSED_DIR': str(tmp_path / 'processed'),
        'RESULTS_DIR': str(tmp_path / 'results'),
        'SPECS_DIR': str(tmp_path / 'specs'),
        'CODE_DIR': str(tmp_path / 'code')
    }
    
    with patch.dict(os.environ, test_env):
        # Directories should not exist yet
        assert not (tmp_path / 'raw').exists()
        
        # Validate should create them
        result = validate_paths()
        
        assert result is True
        assert (tmp_path / 'raw').exists()
        assert (tmp_path / 'processed').exists()
        assert (tmp_path / 'results').exists()
        assert (tmp_path / 'specs').exists()
        assert (tmp_path / 'code').exists()