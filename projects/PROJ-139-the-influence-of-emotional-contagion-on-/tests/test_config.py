"""
Tests for configuration management.
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from code.config.settings import (
    Config,
    APIKeys,
    DatasetPaths,
    config,
    load_config_from_file
)


class TestAPIKeys:
    """Tests for API keys configuration."""

    def test_default_api_keys(self):
        """Test that API keys are initialized from environment or None."""
        keys = APIKeys()
        # Keys should be None or loaded from environment
        assert keys.reddit_user_agent is not None  # Has default

    def test_is_reddit_configured(self):
        """Test Reddit configuration check."""
        # Not configured
        keys = APIKeys()
        assert not keys.is_reddit_configured()

        # Configured
        keys = APIKeys(
            reddit_client_id="test_id",
            reddit_client_secret="test_secret"
        )
        assert keys.is_reddit_configured()

    def test_validate_service(self):
        """Test service validation."""
        keys = APIKeys(
            reddit_client_id="test_id",
            reddit_client_secret="test_secret",
            pushshift_api_url="https://test.com",
            huggingface_token="test_token"
        )

        # Valid services
        valid, msg = keys.validate_service('reddit')
        assert valid
        assert msg == "All required keys present"

        valid, msg = keys.validate_service('pushshift')
        assert valid

        valid, msg = keys.validate_service('huggingface')
        assert valid

        # Missing keys
        keys2 = APIKeys()
        valid, msg = keys2.validate_service('reddit')
        assert not valid
        assert 'Missing keys' in msg


class TestDatasetPaths:
    """Tests for dataset paths configuration."""

    def test_default_paths(self):
        """Test that default paths are set relative to project root."""
        paths = DatasetPaths()
        assert paths.project_root is not None
        assert paths.raw_data_dir is not None
        assert paths.processed_data_dir is not None

    def test_ensure_directories(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = DatasetPaths(
                project_root=Path(tmpdir),
                raw_data_dir=Path(tmpdir) / 'test_raw',
                processed_data_dir=Path(tmpdir) / 'test_processed'
            )

            assert paths.ensure_directories()
            assert paths.raw_data_dir.exists()
            assert paths.processed_data_dir.exists()

    def test_get_path(self):
        """Test path retrieval by name."""
        paths = DatasetPaths()
        raw_path = paths.get_path('raw')
        assert raw_path is not None
        assert paths.raw_data_dir == raw_path


class TestConfig:
    """Tests for main configuration class."""

    def test_config_initialization(self):
        """Test configuration initialization."""
        cfg = Config()
        assert cfg.api_keys is not None
        assert cfg.paths is not None
        assert cfg.debug_mode is False
        assert cfg.log_level == 'INFO'

    def test_load_from_yaml(self):
        """Test loading configuration from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'test_config.yaml'

            test_data = {
                'api_keys': {
                    'reddit_client_id': 'test_id',
                    'reddit_client_secret': 'test_secret'
                },
                'paths': {
                    'raw_data_dir': str(Path(tmpdir) / 'custom_raw')
                },
                'debug_mode': True,
                'log_level': 'DEBUG'
            }

            with open(config_path, 'w') as f:
                yaml.dump(test_data, f)

            cfg = Config()
            assert cfg.load_from_yaml(config_path)
            assert cfg.api_keys.reddit_client_id == 'test_id'
            assert cfg.debug_mode is True
            assert cfg.log_level == 'DEBUG'

    def test_save_to_yaml(self):
        """Test saving configuration to YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'saved_config.yaml'

            cfg = Config(
                api_keys=APIKeys(reddit_client_id='test_id'),
                debug_mode=True,
                log_level='DEBUG'
            )

            assert cfg.save_to_yaml(config_path)
            assert config_path.exists()

            # Load and verify
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)

            assert data['api_keys']['reddit_client_id'] == 'test_id'
            assert data['debug_mode'] is True

    def test_save_to_yaml_excludes_secrets(self):
        """Test that saving without include_secrets excludes sensitive data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'saved_config.yaml'

            cfg = Config(
                api_keys=APIKeys(
                    reddit_client_id='public_id',
                    reddit_client_secret='secret_value',
                    huggingface_token='token_value'
                )
            )

            # Save without secrets
            cfg.save_to_yaml(config_path, include_secrets=False)

            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)

            # Should have public key
            assert data['api_keys']['reddit_client_id'] == 'public_id'
            # Should NOT have secrets
            assert 'reddit_client_secret' not in data['api_keys']
            assert 'huggingface_token' not in data['api_keys']

    def test_validate(self):
        """Test configuration validation."""
        cfg = Config()
        valid, msg = cfg.validate()
        assert valid
        assert msg == "Configuration valid"

    def test_get_api_key(self):
        """Test API key retrieval."""
        cfg = Config(
            api_keys=APIKeys(
                reddit_client_id='test_id',
                pushshift_api_url='https://test.com'
            )
        )

        assert cfg.get_api_key('reddit') == 'test_id'
        assert cfg.get_api_key('pushshift') == 'https://test.com'
        assert cfg.get_api_key('huggingface') is None

    def test_get_data_path(self):
        """Test data path retrieval."""
        cfg = Config()
        path = cfg.get_data_path('raw')
        assert path is not None
        assert path == cfg.paths.raw_data_dir
