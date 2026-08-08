"""
Unit tests for environment configuration management.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust path to import from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config_env import (
    EnvConfig,
    load_environment,
    ensure_directories,
    get_api_key,
    get_data_path,
    get_logs_path,
    get_figures_path,
    validate_required_env_vars,
    create_env_file_template,
    get_env_config
)


class TestEnvConfig:
    """Tests for EnvConfig model."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            assert config.DATA_ROOT_DIR == "data"
            assert config.LOG_LEVEL == "INFO"
            assert config.NCBI_API_KEY is None

    def test_invalid_log_level(self):
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError):
            EnvConfig(
                LOG_LEVEL="INVALID_LEVEL"
            )

    def test_custom_values(self):
        """Test that custom values are accepted."""
        config = EnvConfig(
            DATA_ROOT_DIR="/custom/data",
            LOG_LEVEL="DEBUG",
            NCBI_API_KEY="test-key-123"
        )
        assert config.DATA_ROOT_DIR == "/custom/data"
        assert config.LOG_LEVEL == "DEBUG"
        assert config.NCBI_API_KEY == "test-key-123"


class TestLoadEnvironment:
    """Tests for load_environment function."""

    def test_load_success(self):
        """Test successful loading of environment."""
        with patch.dict(os.environ, {
            'DATA_ROOT_DIR': 'test_data',
            'LOG_LEVEL': 'WARNING'
        }):
            config = load_environment()
            assert config.DATA_ROOT_DIR == 'test_data'
            assert config.LOG_LEVEL == 'WARNING'


class TestEnsureDirectories:
    """Tests for ensure_directories function."""

    def test_creates_directories(self, tmp_path):
        """Test that directories are created."""
        test_root = tmp_path / "test_data"
        config = EnvConfig(
            DATA_ROOT_DIR=str(test_root),
            DATA_RAW_DIR=str(test_root / "raw"),
            DATA_PROCESSED_DIR=str(test_root / "processed"),
            DATA_INTERIM_DIR=str(test_root / "interim"),
            LOG_FILE_PATH=str(test_root / "logs" / "test.log"),
            FIGURES_DIR=str(test_root / "figures")
        )

        ensure_directories(config)

        assert test_root.exists()
        assert (test_root / "raw").exists()
        assert (test_root / "processed").exists()
        assert (test_root / "interim").exists()
        assert (test_root / "logs").exists()
        assert (test_root / "figures").exists()

    def test_skips_existing_directories(self, tmp_path):
        """Test that existing directories are not recreated."""
        test_root = tmp_path / "test_data"
        test_root.mkdir()

        config = EnvConfig(
            DATA_ROOT_DIR=str(test_root),
            DATA_RAW_DIR=str(test_root),
            DATA_PROCESSED_DIR=str(test_root),
            DATA_INTERIM_DIR=str(test_root),
            LOG_FILE_PATH=str(test_root / "logs" / "test.log"),
            FIGURES_DIR=str(test_root)
        )

        # Should not raise
        ensure_directories(config)


class TestGetApiKeys:
    """Tests for get_api_key function."""

    def test_returns_key_when_set(self):
        """Test that API key is returned when set."""
        with patch.dict(os.environ, {'NCBI_API_KEY': 'test-key-123'}):
            key = get_api_key('ncbi')
            assert key == 'test-key-123'

    def test_returns_none_when_not_set(self):
        """Test that None is returned when key is not set."""
        with patch.dict(os.environ, {}, clear=True):
            key = get_api_key('ncbi')
            assert key is None

    def test_case_insensitive_service(self):
        """Test that service name is case insensitive."""
        with patch.dict(os.environ, {'NCBI_API_KEY': 'test-key'}):
            assert get_api_key('NCBI') == 'test-key'
            assert get_api_key('ncbi') == 'test-key'
            assert get_api_key('NcBi') == 'test-key'


class TestGetPaths:
    """Tests for path getter functions."""

    def test_get_data_path(self):
        """Test get_data_path with and without subdir."""
        with patch.dict(os.environ, {'DATA_ROOT_DIR': '/test/data'}):
            assert str(get_data_path()) == '/test/data'
            assert str(get_data_path('raw')) == '/test/data/raw'
            assert str(get_data_path('processed/subdir')) == '/test/data/processed/subdir'

    def test_get_logs_path(self):
        """Test get_logs_path."""
        with patch.dict(os.environ, {'LOG_FILE_PATH': '/test/logs/app.log'}):
            assert str(get_logs_path()) == '/test/logs/app.log'

    def test_get_figures_path(self):
        """Test get_figures_path."""
        with patch.dict(os.environ, {'FIGURES_DIR': '/test/figures'}):
            assert str(get_figures_path()) == '/test/figures'


class TestValidateRequiredEnvVars:
    """Tests for validate_required_env_vars function."""

    def test_all_present(self):
        """Test validation passes when all required vars are present."""
        with patch.dict(os.environ, {
            'NCBI_API_KEY': 'key1',
            'METABOLIGHTS_API_KEY': 'key2'
        }):
            # Should not raise
            validate_required_env_vars({'NCBI_API_KEY', 'METABOLIGHTS_API_KEY'})

    def test_missing_one(self):
        """Test validation fails when one required var is missing."""
        with patch.dict(os.environ, {
            'NCBI_API_KEY': 'key1'
        }):
            with pytest.raises(ValueError) as exc_info:
                validate_required_env_vars({'NCBI_API_KEY', 'METABOLIGHTS_API_KEY'})
            assert 'METABOLIGHTS_API_KEY' in str(exc_info.value)

    def test_empty_value(self):
        """Test validation fails when value is empty."""
        with patch.dict(os.environ, {
            'NCBI_API_KEY': '',
            'METABOLIGHTS_API_KEY': 'key2'
        }):
            with pytest.raises(ValueError) as exc_info:
                validate_required_env_vars({'NCBI_API_KEY', 'METABOLIGHTS_API_KEY'})
            assert 'NCBI_API_KEY' in str(exc_info.value)


class TestCreateEnvFileTemplate:
    """Tests for create_env_file_template function."""

    def test_contains_expected_keys(self):
        """Test that template contains expected configuration keys."""
        template = create_env_file_template()
        expected_keys = [
            'NCBI_API_KEY',
            'METABOLIGHTS_API_KEY',
            'PMDB_ACCESS_TOKEN',
            'DATA_ROOT_DIR',
            'LOG_LEVEL'
        ]
        for key in expected_keys:
            assert key in template

    def test_contains_comments(self):
        """Test that template contains helpful comments."""
        template = create_env_file_template()
        assert '# API Keys' in template
        assert '# Local Path' in template


class TestGetEnvConfig:
    """Tests for get_env_config function."""

    def test_masks_sensitive_data(self):
        """Test that sensitive data is masked in output."""
        with patch.dict(os.environ, {
            'NCBI_API_KEY': 'secret-key-123',
            'DATA_ROOT_DIR': '/test/data'
        }):
            config_dict = get_env_config()
            assert config_dict['NCBI_API_KEY'] == '***'
            assert config_dict['DATA_ROOT_DIR'] == '/test/data'

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        with patch.dict(os.environ, {}, clear=True):
            config_dict = get_env_config()
            assert isinstance(config_dict, dict)
            assert 'DATA_ROOT_DIR' in config_dict
            assert 'LOG_LEVEL' in config_dict