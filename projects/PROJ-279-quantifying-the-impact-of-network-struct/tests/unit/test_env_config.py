import os
import pytest
from pathlib import Path
from unittest.mock import patch

from code.config.env_config import (
    ConfigError,
    EnvironmentConfig,
    get_config,
    reload_config,
    get_cutoff_radius,
    get_zenodo_url,
    get_data_dir,
    get_processed_dir,
    get_log_level,
    get_log_file_path,
    _load_config_from_env,
)
import logging

@pytest.fixture
def clean_env():
    """Remove relevant env vars before test, restore after."""
    keys = ['CUTOFF_RADIUS', 'ZENODO_URL', 'DATA_DIR', 'PROCESSED_DIR', 'LOG_LEVEL', 'LOG_FILE_PATH']
    original = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    yield
    for k, v in original.items():
        if v is not None:
            os.environ[k] = v
        else:
            os.environ.pop(k, None)

class TestEnvironmentConfigValidation:
    def test_missing_cutoff_radius_raises(self, clean_env):
        """Test that missing CUTOFF_RADIUS raises ConfigError."""
        os.environ['ZENODO_URL'] = 'https://zenodo.org/api/files/123'
        with pytest.raises(ConfigError, match="Missing required env var: CUTOFF_RADIUS"):
            _load_config_from_env()

    def test_missing_zenodo_url_raises(self, clean_env):
        """Test that missing ZENODO_URL raises ConfigError."""
        os.environ['CUTOFF_RADIUS'] = '3.0'
        with pytest.raises(ConfigError, match="Missing required env var: ZENODO_URL"):
            _load_config_from_env()

    def test_invalid_cutoff_radius_type_raises(self, clean_env):
        """Test that non-numeric CUTOFF_RADIUS raises ConfigError."""
        os.environ['CUTOFF_RADIUS'] = 'not_a_number'
        os.environ['ZENODO_URL'] = 'https://zenodo.org'
        with pytest.raises(ConfigError, match="CUTOFF_RADIUS must be a valid number"):
            _load_config_from_env()

    def test_negative_cutoff_radius_raises(self, clean_env):
        """Test that negative CUTOFF_RADIUS raises ConfigError."""
        os.environ['CUTOFF_RADIUS'] = '-1.0'
        os.environ['ZENODO_URL'] = 'https://zenodo.org'
        with pytest.raises(ConfigError, match="CUTOFF_RADIUS must be a positive number"):
            _load_config_from_env()

class TestEnvironmentConfigProperties:
    def test_default_values(self, clean_env):
        """Test default values when env vars are not set (except required)."""
        os.environ['CUTOFF_RADIUS'] = '3.0'
        os.environ['ZENODO_URL'] = 'https://zenodo.org'
        cfg = _load_config_from_env()
        
        assert cfg.cutoff_radius == 3.0
        assert cfg.zenodo_url == 'https://zenodo.org'
        assert cfg.data_dir == Path('data')
        assert cfg.processed_dir == Path('data/processed')
        assert cfg.log_level == logging.INFO
        assert cfg.log_file_path == Path('logs/analysis.log')

    def test_custom_paths(self, clean_env):
        """Test custom data and log paths."""
        os.environ['CUTOFF_RADIUS'] = '2.8'
        os.environ['ZENODO_URL'] = 'https://custom.url'
        os.environ['DATA_DIR'] = '/custom/data'
        os.environ['PROCESSED_DIR'] = '/custom/processed'
        os.environ['LOG_FILE_PATH'] = '/custom/logs/app.log'
        os.environ['LOG_LEVEL'] = 'DEBUG'
        
        cfg = _load_config_from_env()
        
        assert cfg.cutoff_radius == 2.8
        assert cfg.zenodo_url == 'https://custom.url'
        assert cfg.data_dir == Path('/custom/data')
        assert cfg.processed_dir == Path('/custom/processed')
        assert cfg.log_level == logging.DEBUG
        assert cfg.log_file_path == Path('/custom/logs/app.log')

class TestGlobalAccessors:
    def test_get_config_singleton(self, clean_env):
        """Test that get_config returns a singleton instance."""
        os.environ['CUTOFF_RADIUS'] = '3.0'
        os.environ['ZENODO_URL'] = 'https://zenodo.org'
        
        cfg1 = get_config()
        cfg2 = get_config()
        
        assert cfg1 is cfg2

    def test_reload_config(self, clean_env):
        """Test that reload_config creates a new instance."""
        os.environ['CUTOFF_RADIUS'] = '3.0'
        os.environ['ZENODO_URL'] = 'https://zenodo.org'
        
        cfg1 = get_config()
        os.environ['CUTOFF_RADIUS'] = '3.5'
        cfg2 = reload_config()
        
        assert cfg1 is not cfg2
        assert cfg1.cutoff_radius == 3.0
        assert cfg2.cutoff_radius == 3.5

    def test_convenience_functions(self, clean_env):
        """Test convenience functions return correct values."""
        os.environ['CUTOFF_RADIUS'] = '3.2'
        os.environ['ZENODO_URL'] = 'https://zenodo.org/api'
        os.environ['LOG_LEVEL'] = 'WARNING'
        
        assert get_cutoff_radius() == 3.2
        assert get_zenodo_url() == 'https://zenodo.org/api'
        assert get_log_level() == logging.WARNING
        assert get_data_dir() == Path('data')
        assert get_processed_dir() == Path('data/processed')
        assert get_log_file_path() == Path('logs/analysis.log')

class TestDerivedPaths:
    def test_raw_dir(self, clean_env):
        """Test raw directory is derived from data_dir."""
        os.environ['CUTOFF_RADIUS'] = '3.0'
        os.environ['ZENODO_URL'] = 'https://zenodo.org'
        os.environ['DATA_DIR'] = '/my/data'
        
        cfg = _load_config_from_env()
        assert cfg.raw_dir == Path('/my/data/raw')

    def test_graphs_dir(self, clean_env):
        """Test graphs directory is derived from processed_dir."""
        os.environ['CUTOFF_RADIUS'] = '3.0'
        os.environ['ZENODO_URL'] = 'https://zenodo.org'
        os.environ['PROCESSED_DIR'] = '/processed'
        
        cfg = _load_config_from_env()
        assert cfg.graphs_dir == Path('/processed/graphs')

    def test_results_dir(self, clean_env):
        """Test results directory is derived from processed_dir."""
        os.environ['CUTOFF_RADIUS'] = '3.0'
        os.environ['ZENODO_URL'] = 'https://zenodo.org'
        os.environ['PROCESSED_DIR'] = '/processed'
        
        cfg = _load_config_from_env()
        assert cfg.results_dir == Path('/processed/results')
