"""
Tests for environment variable management module.

These tests verify that the environment configuration system works correctly,
including path validation, API key retrieval, and directory creation.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

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
    """Tests for the EnvConfig model."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            assert config.DATA_ROOT == Path("data")
            assert config.DATA_RAW == Path("data/raw")
            assert config.DATA_PROCESSED == Path("data/processed")
            assert config.DATA_INTERIM == Path("data/interim")
            assert config.LOGS_DIR == Path("logs")
            assert config.FIGURES_DIR == Path("figures")
            assert config.NCBI_API_KEY is None

    def test_custom_paths(self):
        """Test that custom paths can be set via environment variables."""
        test_env = {
            'DATA_ROOT': '/custom/data',
            'DATA_RAW': '/custom/data/raw',
            'LOGS_DIR': '/custom/logs'
        }
        with patch.dict(os.environ, test_env):
            config = EnvConfig()
            assert config.DATA_ROOT == Path("/custom/data")
            assert config.DATA_RAW == Path("/custom/data/raw")
            assert config.LOGS_DIR == Path("/custom/logs")

    def test_api_keys(self):
        """Test that API keys can be set via environment variables."""
        test_env = {
            'NCBI_API_KEY': 'test_ncbi_key',
            'PMDB_API_KEY': 'test_pmdb_key',
            'METABOLIGHTS_TOKEN': 'test_metabolights_token'
        }
        with patch.dict(os.environ, test_env):
            config = EnvConfig()
            assert config.NCBI_API_KEY == 'test_ncbi_key'
            assert config.PMDB_API_KEY == 'test_pmdb_key'
            assert config.METABOLIGHTS_TOKEN == 'test_metabolights_token'


class TestLoadEnvironment:
    """Tests for the load_environment function."""

    def test_load_environment_success(self):
        """Test successful loading of environment configuration."""
        config = load_environment()
        assert isinstance(config, EnvConfig)
        assert config.DATA_ROOT is not None

    def test_load_environment_with_custom_values(self):
        """Test loading with custom environment values."""
        test_env = {
            'DATA_ROOT': '/test/root',
            'DATA_PROCESSED': '/test/processed'
        }
        with patch.dict(os.environ, test_env):
            config = load_environment()
            assert config.DATA_ROOT == Path("/test/root")
            assert config.DATA_PROCESSED == Path("/test/processed")


class TestEnsureDirectories:
    """Tests for the ensure_directories function."""

    def test_create_missing_directories(self, tmp_path):
        """Test that missing directories are created."""
        test_config = EnvConfig()
        # Override with temp paths
        test_config.DATA_ROOT = tmp_path / "data"
        test_config.DATA_RAW = tmp_path / "data" / "raw"
        test_config.DATA_PROCESSED = tmp_path / "data" / "processed"
        test_config.DATA_INTERIM = tmp_path / "data" / "interim"
        test_config.LOGS_DIR = tmp_path / "logs"
        test_config.FIGURES_DIR = tmp_path / "figures"

        ensure_directories(test_config)

        assert test_config.DATA_ROOT.exists()
        assert test_config.DATA_RAW.exists()
        assert test_config.DATA_PROCESSED.exists()
        assert test_config.DATA_INTERIM.exists()
        assert test_config.LOGS_DIR.exists()
        assert test_config.FIGURES_DIR.exists()

    def test_existing_directories_unchanged(self, tmp_path):
        """Test that existing directories are not modified."""
        # Create directories first
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        
        test_config = EnvConfig()
        test_config.DATA_ROOT = test_dir

        ensure_directories(test_config)
        
        assert test_dir.exists()


class TestGetApiKey:
    """Tests for the get_api_key function."""

    def test_get_ncbi_key(self):
        """Test retrieving NCBI API key."""
        with patch.dict(os.environ, {'NCBI_API_KEY': 'test_key'}):
            key = get_api_key('ncbi')
            assert key == 'test_key'

    def test_get_pmdb_key(self):
        """Test retrieving PMDB API key."""
        with patch.dict(os.environ, {'PMDB_API_KEY': 'test_pmdb_key'}):
            key = get_api_key('pmdb')
            assert key == 'test_pmdb_key'

    def test_get_metabolights_token(self):
        """Test retrieving MetaboLights token."""
        with patch.dict(os.environ, {'METABOLIGHTS_TOKEN': 'test_token'}):
            key = get_api_key('metabolights')
            assert key == 'test_token'

    def test_missing_key_returns_none(self):
        """Test that missing keys return None."""
        with patch.dict(os.environ, {}, clear=True):
            key = get_api_key('ncbi')
            assert key is None

    def test_unknown_service_raises_error(self):
        """Test that unknown service names raise ValueError."""
        with pytest.raises(ValueError, match="Unknown service"):
            get_api_key('unknown_service')


class TestGetPaths:
    """Tests for path retrieval functions."""

    def test_get_data_path_root(self):
        """Test getting root data path."""
        with patch.dict(os.environ, {'DATA_ROOT': '/test/data'}):
            path = get_data_path()
            assert path == Path("/test/data")

    def test_get_data_path_subpath(self):
        """Test getting subpath within data root."""
        with patch.dict(os.environ, {'DATA_ROOT': '/test/data'}):
            path = get_data_path('raw/genomes')
            assert path == Path("/test/data/raw/genomes")

    def test_get_logs_path(self):
        """Test getting logs path."""
        with patch.dict(os.environ, {'LOGS_DIR': '/test/logs'}):
            path = get_logs_path()
            assert path == Path("/test/logs")

    def test_get_figures_path(self):
        """Test getting figures path."""
        with patch.dict(os.environ, {'FIGURES_DIR': '/test/figures'}):
            path = get_figures_path()
            assert path == Path("/test/figures")


class TestValidateRequiredEnvVars:
    """Tests for validate_required_env_vars function."""

    def test_all_present(self):
        """Test validation when all required vars are present."""
        with patch.dict(os.environ, {'VAR1': 'value1', 'VAR2': 'value2'}):
            # Should not raise
            validate_required_env_vars({'VAR1', 'VAR2'})

    def test_missing_vars(self):
        """Test validation when some required vars are missing."""
        with patch.dict(os.environ, {'VAR1': 'value1'}):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                validate_required_env_vars({'VAR1', 'VAR2', 'VAR3'})

    def test_empty_set(self):
        """Test validation with empty set of required vars."""
        # Should not raise
        validate_required_env_vars(set())


class TestCreateEnvFileTemplate:
    """Tests for create_env_file_template function."""

    def test_create_template(self, tmp_path):
        """Test creating a template .env file."""
        output_path = tmp_path / ".env"
        result_path = create_env_file_template(str(output_path))
        
        assert result_path.exists()
        content = result_path.read_text()
        assert "NCBI_API_KEY" in content
        assert "PMDB_API_KEY" in content
        assert "DATA_ROOT" in content

    def test_existing_file_not_overwritten(self, tmp_path):
        """Test that existing .env file is not overwritten."""
        output_path = tmp_path / ".env"
        output_path.write_text("EXISTING_CONTENT")
        
        result_path = create_env_file_template(str(output_path))
        
        assert result_path.exists()
        content = result_path.read_text()
        assert content == "EXISTING_CONTENT"


class TestGetEnvConfig:
    """Tests for get_env_config function."""

    def test_returns_config(self):
        """Test that get_env_config returns a valid config."""
        config = get_env_config()
        assert isinstance(config, EnvConfig)
        assert config.DATA_ROOT is not None

    def test_creates_directories(self, tmp_path):
        """Test that get_env_config creates required directories."""
        # This is harder to test in isolation due to side effects,
        # but we can verify it doesn't crash
        with patch('config_env.ensure_directories') as mock_ensure:
            with patch('config_env.load_environment') as mock_load:
                mock_load.return_value = EnvConfig()
                config = get_env_config()
                mock_ensure.assert_called_once()
                mock_load.assert_called_once()