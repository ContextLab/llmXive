"""
Unit tests for T007: Configuration management module.

Tests verify:
- Singleton pattern works correctly
- Default values are set as specified in task requirements
- Environment variable overrides work
- Path resolution and directory creation
- JSON serialization/deserialization
- Validation of configuration values
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from src.utils.config import (
    Config,
    get_config,
    reset_config,
    save_config,
    load_config,
    get_project_root,
    get_data_dir,
    get_logs_dir,
    get_analysis_dir,
    get_figures_dir,
    get_cache_dir,
)


class TestConfigSingleton:
    """Test singleton pattern behavior."""
    
    def test_get_config_returns_same_instance(self):
        """Multiple calls to get_config should return the same instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_reset_config_creates_new_instance(self):
        """reset_config should create a new instance on next get_config call."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2
    
    def test_singleton_ignores_subsequent_initializations(self):
        """Singleton should ignore attempts to reinitialize."""
        reset_config()
        config1 = get_config()
        # Directly creating another Config instance shouldn't affect singleton
        config2 = Config()
        assert get_config() is config1
        assert config2 is not config1


class TestConfigDefaults:
    """Test default configuration values."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
    
    def test_default_seed_is_42(self):
        """Default random seed should be 42."""
        config = get_config()
        assert config.seed == 42
    
    def test_default_filter_low_freq_is_1_0(self):
        """Default low-frequency filter should be 1.0 Hz (Task T007 requirement)."""
        config = get_config()
        assert config.filter_low_freq == 1.0
    
    def test_default_filter_high_freq_is_40_0(self):
        """Default high-frequency filter should be 40.0 Hz."""
        config = get_config()
        assert config.filter_high_freq == 40.0
    
    def test_default_mmn_window_start_is_250(self):
        """Default MMN window start should be -250ms (Task T007 requirement)."""
        config = get_config()
        assert config.mmn_window_start == -250
    
    def test_default_epoch_tmin_is_0_2(self):
        """Default epoch tmin should be -0.2 seconds (-200ms)."""
        config = get_config()
        assert config.epoch_tmin == -0.2
    
    def test_default_epoch_tmax_is_0_5(self):
        """Default epoch tmax should be 0.5 seconds (500ms)."""
        config = get_config()
        assert config.epoch_tmax == 0.5
    
    def test_default_lagged_source_window_trials_is_50(self):
        """Default lagged source window should be 50 trials."""
        config = get_config()
        assert config.lagged_source_window_trials == 50
    
    def test_default_mmn_channels(self):
        """Default MMN channels should include CP3, CP4, C3, C4."""
        config = get_config()
        expected = ["CP3", "CP4", "C3", "C4"]
        assert config.mmn_channels == expected
    
    def test_default_permutation_n_is_1000(self):
        """Default permutation count should be 1000."""
        config = get_config()
        assert config.permutation_n == 1000
    
    def test_default_min_subjects_threshold_is_20(self):
        """Default minimum subjects threshold should be 20."""
        config = get_config()
        assert config.min_subjects_threshold == 20


class TestConfigOverrides:
    """Test configuration value overrides."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
    
    def test_set_valid_value(self):
        """Setting a valid configuration value should work."""
        config = get_config()
        config.set("seed", 123)
        assert config.seed == 123
    
    def test_set_invalid_key_raises_error(self):
        """Setting an invalid key should raise KeyError."""
        config = get_config()
        with pytest.raises(KeyError):
            config.set("invalid_key", "value")
    
    def test_set_invalid_seed_raises_error(self):
        """Setting negative seed should raise ValueError."""
        config = get_config()
        with pytest.raises(ValueError):
            config.set("seed", -1)
    
    def test_set_invalid_filter_raises_error(self):
        """Setting invalid filter values should raise ValueError."""
        config = get_config()
        with pytest.raises(ValueError):
            config.set("filter_low_freq", 50.0)  # Higher than high_freq
    
    def test_get_with_default(self):
        """get() with default should return default for missing keys."""
        config = get_config()
        assert config.get("nonexistent_key", "default") == "default"
    
    def test_get_returns_actual_value(self):
        """get() should return actual value for existing keys."""
        config = get_config()
        assert config.get("seed", 0) == 42


class TestConfigPersistence:
    """Test configuration save/load functionality."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
    
    def test_save_creates_file(self):
        """save() should create a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            save_config(path)
            assert path.exists()
    
    def test_save_and_load_preserves_values(self):
        """Save and load should preserve all configuration values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            config = get_config()
            config.seed = 999
            config.filter_low_freq = 2.5
            save_config(path)
            
            loaded_config = load_config(path)
            assert loaded_config.seed == 999
            assert loaded_config.filter_low_freq == 2.5
    
    def test_load_missing_file_raises_error(self):
        """Loading from non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.json")
    
    def test_to_json_produces_valid_json(self):
        """to_json() should produce valid JSON string."""
        import json
        config = get_config()
        json_str = config.to_json()
        # Should not raise
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
    
    def test_to_dict_excludes_internal_fields(self):
        """to_dict() should exclude fields starting with underscore."""
        config = get_config()
        d = config.to_dict()
        for key in d:
            assert not key.startswith("_")
    
    def test_path_resolution_creates_directories(self):
        """Path resolution should create necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a config with custom paths
            config = Config(
                project_root=Path(tmpdir),
                data_dir=Path("custom_data"),
                logs_dir=Path("custom_logs")
            )
            # Directories should be created
            assert (Path(tmpdir) / "custom_data").exists()
            assert (Path(tmpdir) / "custom_logs").exists()


class TestEnvironmentOverrides:
    """Test environment variable overrides."""
    
    def setup_method(self):
        """Reset config and clear env vars before each test."""
        reset_config()
        # Clear any relevant env vars
        for key in ["RANDOM_SEED", "FILTER_LOW_FREQ", "PROJECT_ROOT"]:
            os.environ.pop(key, None)
    
    def teardown_method(self):
        """Clear env vars after each test."""
        for key in ["RANDOM_SEED", "FILTER_LOW_FREQ", "PROJECT_ROOT"]:
            os.environ.pop(key, None)
    
    def test_env_override_seed(self):
        """Environment variable should override default seed."""
        os.environ["RANDOM_SEED"] = "777"
        config = get_config()
        assert config.seed == 777
    
    def test_env_override_filter_low_freq(self):
        """Environment variable should override filter low frequency."""
        os.environ["FILTER_LOW_FREQ"] = "2.5"
        config = get_config()
        assert config.filter_low_freq == 2.5
    
    def test_env_invalid_integer_raises_error(self):
        """Invalid integer in env var should raise ValueError."""
        os.environ["RANDOM_SEED"] = "not_a_number"
        with pytest.raises(ValueError):
            get_config()
    
    def test_env_invalid_float_raises_error(self):
        """Invalid float in env var should raise ValueError."""
        os.environ["FILTER_LOW_FREQ"] = "not_a_number"
        with pytest.raises(ValueError):
            get_config()


class TestConvenienceFunctions:
    """Test convenience functions for path access."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
    
    def test_get_project_root_returns_path(self):
        """get_project_root() should return a Path object."""
        path = get_project_root()
        assert isinstance(path, Path)
    
    def test_get_data_dir_returns_path(self):
        """get_data_dir() should return a Path object."""
        path = get_data_dir()
        assert isinstance(path, Path)
    
    def test_get_logs_dir_returns_path(self):
        """get_logs_dir() should return a Path object."""
        path = get_logs_dir()
        assert isinstance(path, Path)
    
    def test_get_analysis_dir_returns_path(self):
        """get_analysis_dir() should return a Path object."""
        path = get_analysis_dir()
        assert isinstance(path, Path)
    
    def test_get_figures_dir_returns_path(self):
        """get_figures_dir() should return a Path object."""
        path = get_figures_dir()
        assert isinstance(path, Path)
    
    def test_get_cache_dir_returns_path(self):
        """get_cache_dir() should return a Path object."""
        path = get_cache_dir()
        assert isinstance(path, Path)
    
    def test_all_paths_are_absolute(self):
        """All convenience paths should be absolute."""
        assert get_project_root().is_absolute()
        assert get_data_dir().is_absolute()
        assert get_logs_dir().is_absolute()
        assert get_analysis_dir().is_absolute()
        assert get_figures_dir().is_absolute()
        assert get_cache_dir().is_absolute()
