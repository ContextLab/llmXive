"""
Unit tests for the configuration loader (T006).

Tests verify that the config module correctly initializes seeds, paths,
and configuration parameters, and that paths are properly resolved.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.config import Config, get_config, get_config_with_overrides, _BASE_DIR


class TestConfigInitialization:
    """Tests for basic Config initialization."""
    
    def test_default_seed(self):
        """Test that default seed is 42."""
        config = Config()
        assert config.seed == 42
    
    def test_default_openml_ids(self):
        """Test that default OpenML IDs are set."""
        config = Config()
        expected_ids = [150, 159, 160, 161, 162, 163, 164, 165, 166, 167]
        assert config.openml_ids == expected_ids
        assert len(config.openml_ids) == 10
    
    def test_default_snr_levels(self):
        """Test that default SNR levels are set."""
        config = Config()
        expected_snr = [0.5, 1.0, 2.0, 5.0]
        assert config.snr_levels == expected_snr
    
    def test_default_sparsity_levels(self):
        """Test that default sparsity levels are set."""
        config = Config()
        expected_sparsity = [0.1, 0.2, 0.5, 1.0]
        assert config.sparsity_levels == expected_sparsity
    
    def test_default_output_path_is_relative(self):
        """Test that default output_path is relative in initialization."""
        config = Config()
        # Before _resolve_paths, it should be relative
        assert config.output_path == "data/processed"
    
    def test_paths_are_resolved_after_init(self):
        """Test that paths are resolved to absolute paths after initialization."""
        config = Config()
        # After __post_init__, paths should be absolute
        expected_output = os.path.join(_BASE_DIR, "data/processed")
        assert config.output_path == expected_output
        assert os.path.isabs(config.output_path)
    
    def test_raw_data_path_resolved(self):
        """Test that raw_data_path is resolved correctly."""
        config = Config()
        expected_raw = os.path.join(_BASE_DIR, "data/raw")
        assert config.raw_data_path == expected_raw
    
    def test_results_path_resolved(self):
        """Test that results_path is resolved correctly."""
        config = Config()
        expected_results = os.path.join(_BASE_DIR, "results")
        assert config.results_path == expected_results


class TestConfigValidation:
    """Tests for Config validation logic."""
    
    def test_invalid_seed_negative(self):
        """Test that negative seed raises ValueError."""
        with pytest.raises(ValueError, match="Seed must be a non-negative integer"):
            Config(seed=-1)
    
    def test_invalid_seed_string(self):
        """Test that string seed raises ValueError."""
        with pytest.raises(ValueError, match="Seed must be a non-negative integer"):
            Config(seed="42")
    
    def test_empty_openml_ids(self):
        """Test that empty openml_ids raises ValueError."""
        with pytest.raises(ValueError, match="openml_ids cannot be empty"):
            Config(openml_ids=[])
    
    def test_invalid_snr_level_zero(self):
        """Test that zero SNR level raises ValueError."""
        with pytest.raises(ValueError, match="All SNR levels must be positive numbers"):
            Config(snr_levels=[0.0, 1.0])
    
    def test_invalid_snr_level_negative(self):
        """Test that negative SNR level raises ValueError."""
        with pytest.raises(ValueError, match="All SNR levels must be positive numbers"):
            Config(snr_levels=[-1.0, 1.0])
    
    def test_invalid_sparsity_level_zero(self):
        """Test that zero sparsity level raises ValueError."""
        with pytest.raises(ValueError, match="All sparsity levels must be between 0 and 1"):
            Config(sparsity_levels=[0.0, 0.5])
    
    def test_invalid_sparsity_level_negative(self):
        """Test that negative sparsity level raises ValueError."""
        with pytest.raises(ValueError, match="All sparsity levels must be between 0 and 1"):
            Config(sparsity_levels=[-0.1, 0.5])
    
    def test_invalid_sparsity_level_greater_than_one(self):
        """Test that sparsity level > 1 raises ValueError."""
        with pytest.raises(ValueError, match="All sparsity levels must be between 0 and 1"):
            Config(sparsity_levels=[0.5, 1.5])
    
    def test_valid_sparsity_level_one(self):
        """Test that sparsity level of 1.0 is valid."""
        config = Config(sparsity_levels=[1.0])
        assert 1.0 in config.sparsity_levels
    
    def test_valid_sparsity_level_close_to_zero(self):
        """Test that sparsity level close to 0 is valid."""
        config = Config(sparsity_levels=[0.001, 0.5])
        assert 0.001 in config.sparsity_levels


class TestGetConfig:
    """Tests for the get_config factory function."""
    
    def test_get_config_returns_config_instance(self):
        """Test that get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)
    
    def test_get_config_has_all_required_keys(self):
        """Test that get_config returns config with all required keys."""
        config = get_config()
        required_keys = ['seed', 'openml_ids', 'snr_levels', 'sparsity_levels', 'output_path']
        for key in required_keys:
            assert hasattr(config, key)
    
    def test_get_config_creates_directories(self):
        """Test that get_config creates necessary directories."""
        # Clean up first if they exist
        temp_dir = os.path.join(_BASE_DIR, "test_temp_dirs")
        config = Config(
            output_path="test_temp_dirs/processed",
            raw_data_path="test_temp_dirs/raw",
            results_path="test_temp_dirs/results"
        )
        
        assert os.path.exists(config.output_path)
        assert os.path.exists(config.raw_data_path)
        assert os.path.exists(config.results_path)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

class TestGetConfigWithOverrides:
    """Tests for the get_config_with_overrides function."""
    
    def test_override_seed(self):
        """Test overriding seed value."""
        config = get_config_with_overrides({'seed': 123})
        assert config.seed == 123
    
    def test_override_openml_ids(self):
        """Test overriding openml_ids."""
        new_ids = [1, 2, 3]
        config = get_config_with_overrides({'openml_ids': new_ids})
        assert config.openml_ids == new_ids
    
    def test_override_multiple_values(self):
        """Test overriding multiple configuration values."""
        config = get_config_with_overrides({
            'seed': 999,
            'snr_levels': [10.0, 20.0],
            'sparsity_levels': [0.3]
        })
        assert config.seed == 999
        assert config.snr_levels == [10.0, 20.0]
        assert config.sparsity_levels == [0.3]
    
    def test_invalid_override_key(self):
        """Test that overriding non-existent key raises ValueError."""
        with pytest.raises(ValueError, match="Unknown configuration key"):
            get_config_with_overrides({'non_existent_key': 'value'})
    
    def test_override_creates_directories(self):
        """Test that overrides still result in directory creation."""
        config = get_config_with_overrides({
            'output_path': 'test_override_processed',
            'raw_data_path': 'test_override_raw',
            'results_path': 'test_override_results'
        })
        
        assert os.path.exists(config.output_path)
        assert os.path.exists(config.raw_data_path)
        assert os.path.exists(config.results_path)
        
        # Cleanup
        import shutil
        base_test_dir = os.path.join(_BASE_DIR, 'test_override_processed')
        if os.path.exists(base_test_dir):
            shutil.rmtree(os.path.dirname(base_test_dir), ignore_errors=True)