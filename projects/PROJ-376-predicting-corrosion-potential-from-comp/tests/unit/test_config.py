"""
Unit tests for configuration management functionality.
Tests for T008: Environment configuration management for random seeds and file paths.
"""

import pytest
import random
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.config import (
    ProjectConfig,
    ConfigManager,
    get_config,
    set_random_seed,
    get_path,
    get_data_path,
    get_processed_data_path,
    get_log_path,
    save_config,
    update_config,
    get_processed_dataset_path,
    get_model_results_path,
    get_pipeline_log_path,
    get_split_indices_path,
    get_split_validation_path,
    get_diagnostics_path,
    get_count_report_path,
    get_figures_path,
    get_interpretability_path,
    get_astm_tolerance_config_path,
    get_verified_datasets_config_path
)
from utils.exceptions import CorrosionPipelineError


class TestProjectConfig:
    """Tests for ProjectConfig dataclass."""

    def test_default_initialization(self):
        """Test that ProjectConfig initializes with defaults."""
        config = ProjectConfig()
        assert config.random_seeds is not None
        assert config.file_paths is not None
        assert config.data_sources is not None
        assert config.processing is not None
        assert config.model_training is not None
        assert config.validation is not None

    def test_custom_initialization(self):
        """Test ProjectConfig with custom values."""
        custom_seeds = {'global_seed': 123, 'custom_seed': 456}
        config = ProjectConfig(random_seeds=custom_seeds)
        assert config.random_seeds == custom_seeds

    def test_post_init_defaults(self):
        """Test that __post_init__ sets defaults when empty dicts provided."""
        config = ProjectConfig(random_seeds={}, file_paths={})
        assert 'global_seed' in config.random_seeds
        assert 'raw_data_dir' in config.file_paths


class TestConfigManager:
    """Tests for ConfigManager singleton."""

    def test_singleton_pattern(self):
        """Test that ConfigManager is a singleton."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        assert manager1 is manager2

    @patch('utils.config.Path')
    def test_load_config_missing_file(self, mock_path):
        """Test error when config file is missing."""
        mock_path.return_value.exists.return_value = False

        with pytest.raises(CorrosionPipelineError) as exc_info:
            ConfigManager._load_config("nonexistent.yaml")

        assert "not found" in str(exc_info.value)

    @patch('builtins.open')
    @patch('utils.config.yaml')
    def test_load_config_invalid_yaml(self, mock_yaml, mock_open):
        """Test error when config file has invalid YAML."""
        mock_yaml.safe_load.side_effect = Exception("YAML error")

        with pytest.raises(CorrosionPipelineError) as exc_info:
            ConfigManager._load_config("invalid.yaml")

        assert "Failed to parse" in str(exc_info.value)

    def test_get_config_returns_instance(self):
        """Test that get_config returns a ProjectConfig instance."""
        config = get_config()
        assert isinstance(config, ProjectConfig)

    def test_update_config(self):
        """Test updating configuration values."""
        manager = ConfigManager()
        initial_seeds = manager.get_config().random_seeds.copy()

        update_config({'random_seeds': {'custom_seed': 999}})

        new_config = manager.get_config()
        assert 'custom_seed' in new_config.random_seeds
        assert new_config.random_seeds['custom_seed'] == 999

    @patch('builtins.open')
    @patch('utils.config.Path')
    def test_save_config(self, mock_path, mock_open):
        """Test saving configuration to file."""
        mock_path.return_value.parent = MagicMock()
        manager = ConfigManager()
        manager.save_config("test_config.yaml")

        mock_path.return_value.parent.mkdir.assert_called_once()
        mock_open.assert_called_once()


class TestRandomSeedFunctions:
    """Tests for random seed management."""

    @patch('utils.config.random')
    @patch('utils.config.os')
    def test_set_random_seed_with_value(self, mock_os, mock_random):
        """Test setting random seed with explicit value."""
        result = set_random_seed(seed=123, seed_name='test_seed')

        assert result == 123
        mock_random.seed.assert_called_once_with(123)
        assert mock_os.environ['PYTHONHASHSEED'] == '123'

    @patch('utils.config.get_config')
    @patch('utils.config.random')
    @patch('utils.config.os')
    def test_set_random_seed_from_config(self, mock_os, mock_random, mock_get_config):
        """Test setting random seed from config when not provided."""
        mock_config = MagicMock()
        mock_config.random_seeds = {'global_seed': 456}
        mock_get_config.return_value = mock_config

        result = set_random_seed(seed=None, seed_name='global_seed')

        assert result == 456
        mock_random.seed.assert_called_once_with(456)


class TestPathFunctions:
    """Tests for path retrieval functions."""

    @patch('utils.config.get_config')
    def test_get_path_valid_key(self, mock_get_config):
        """Test getting a valid path from config."""
        mock_config = MagicMock()
        mock_config.file_paths = {'test_key': '/path/to/file'}
        mock_get_config.return_value = mock_config

        path = get_path('test_key')
        assert path == Path('/path/to/file')

    @patch('utils.config.get_config')
    def test_get_path_invalid_key(self, mock_get_config):
        """Test error when getting invalid path key."""
        mock_config = MagicMock()
        mock_config.file_paths = {'other_key': '/path'}
        mock_get_config.return_value = mock_config

        with pytest.raises(CorrosionPipelineError) as exc_info:
            get_path('invalid_key')

        assert "not found" in str(exc_info.value)

    def test_get_data_path(self):
        """Test get_data_path returns correct path."""
        # This will use the actual config, just verify it returns a Path
        path = get_data_path()
        assert isinstance(path, Path)

    def test_get_processed_data_path(self):
        """Test get_processed_data_path returns correct path."""
        path = get_processed_data_path()
        assert isinstance(path, Path)

    def test_get_log_path(self):
        """Test get_log_path returns correct path."""
        path = get_log_path()
        assert isinstance(path, Path)

    def test_get_processed_dataset_path(self):
        """Test get_processed_dataset_path returns correct path."""
        path = get_processed_dataset_path()
        assert isinstance(path, Path)

    def test_get_model_results_path(self):
        """Test get_model_results_path returns correct path."""
        path = get_model_results_path()
        assert isinstance(path, Path)

    def test_get_pipeline_log_path(self):
        """Test get_pipeline_log_path returns correct path."""
        path = get_pipeline_log_path()
        assert isinstance(path, Path)

    def test_get_split_indices_path(self):
        """Test get_split_indices_path returns correct path."""
        path = get_split_indices_path()
        assert isinstance(path, Path)

    def test_get_split_validation_path(self):
        """Test get_split_validation_path returns correct path."""
        path = get_split_validation_path()
        assert isinstance(path, Path)

    def test_get_diagnostics_path(self):
        """Test get_diagnostics_path returns correct path."""
        path = get_diagnostics_path()
        assert isinstance(path, Path)

    def test_get_count_report_path(self):
        """Test get_count_report_path returns correct path."""
        path = get_count_report_path()
        assert isinstance(path, Path)

    def test_get_figures_path(self):
        """Test get_figures_path returns correct path."""
        path = get_figures_path()
        assert isinstance(path, Path)

    def test_get_interpretability_path(self):
        """Test get_interpretability_path returns correct path."""
        path = get_interpretability_path()
        assert isinstance(path, Path)

    def test_get_astm_tolerance_config_path(self):
        """Test get_astm_tolerance_config_path returns correct path."""
        path = get_astm_tolerance_config_path()
        assert isinstance(path, Path)

    def test_get_verified_datasets_config_path(self):
        """Test get_verified_datasets_config_path returns correct path."""
        path = get_verified_datasets_config_path()
        assert isinstance(path, Path)