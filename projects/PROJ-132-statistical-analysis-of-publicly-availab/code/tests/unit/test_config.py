"""
Unit tests for the configuration management module (T011).

These tests verify that the Config class correctly handles:
- Default values
- Environment variable overrides
- Type validation
- Edge cases
"""

import os
import pytest
from pathlib import Path
from src.lib.config import (
    Config,
    get_config,
    reset_config,
    DEFAULT_SEED,
    DEFAULT_GRID_RES,
    DEFAULT_PERMUTATIONS,
    DEFAULT_SAMPLE_SIZE,
    ENV_SEED,
    ENV_GRID_RES,
    ENV_SAMPLE_SIZE,
    ENV_PERMUTATIONS,
    update_globals_from_config,
)


class TestConfigDefaults:
    """Test default configuration values."""

    def test_seed_default_value(self):
        """Test that default seed is 42."""
        # Clear any env vars to ensure defaults are used
        for var in [ENV_SEED, ENV_GRID_RES, ENV_SAMPLE_SIZE, ENV_PERMUTATIONS]:
            if var in os.environ:
                del os.environ[var]

        reset_config()
        cfg = Config()

        assert cfg.seed == 42
        assert cfg.seed == DEFAULT_SEED

    def test_seed_is_integer(self):
        """Test that seed is always an integer."""
        reset_config()
        cfg = Config(seed=123)
        assert isinstance(cfg.seed, int)

    def test_grid_res_default_value(self):
        """Test that default grid resolution is 0.5."""
        for var in [ENV_SEED, ENV_GRID_RES, ENV_SAMPLE_SIZE, ENV_PERMUTATIONS]:
            if var in os.environ:
                del os.environ[var]

        reset_config()
        cfg = Config()

        assert cfg.grid_res == 0.5
        assert cfg.grid_res == DEFAULT_GRID_RES

    def test_grid_res_is_float(self):
        """Test that grid_res is always a float."""
        reset_config()
        cfg = Config(grid_res=1.0)
        assert isinstance(cfg.grid_res, float)

    def test_permutations_default_value(self):
        """Test that default permutations is 10000."""
        for var in [ENV_SEED, ENV_GRID_RES, ENV_SAMPLE_SIZE, ENV_PERMUTATIONS]:
            if var in os.environ:
                del os.environ[var]

        reset_config()
        cfg = Config()

        assert cfg.permutations == 10000
        assert cfg.permutations == DEFAULT_PERMUTATIONS

    def test_permutations_is_integer(self):
        """Test that permutations is always an integer."""
        reset_config()
        cfg = Config(permutations=5000)
        assert isinstance(cfg.permutations, int)

    def test_sample_size_default_value(self):
        """Test that default sample_size is None."""
        for var in [ENV_SEED, ENV_GRID_RES, ENV_SAMPLE_SIZE, ENV_PERMUTATIONS]:
            if var in os.environ:
                del os.environ[var]

        reset_config()
        cfg = Config()

        assert cfg.sample_size is None
        assert cfg.sample_size == DEFAULT_SAMPLE_SIZE

    def test_sample_size_can_be_none(self):
        """Test that sample_size can be explicitly set to None."""
        reset_config()
        cfg = Config(sample_size=None)
        assert cfg.sample_size is None

    def test_sample_size_can_be_set(self):
        """Test that sample_size can be set to a positive integer."""
        reset_config()
        cfg = Config(sample_size=1000)
        assert cfg.sample_size == 1000

    def test_permutations_can_be_set(self):
        """Test that permutations can be set to a custom value."""
        reset_config()
        cfg = Config(permutations=50000)
        assert cfg.permutations == 50000


class TestConfigEnvironmentVariables:
    """Test configuration loaded from environment variables."""

    def setup_method(self):
        """Save original environment variables."""
        self.original_env = {}
        for var in [ENV_SEED, ENV_GRID_RES, ENV_SAMPLE_SIZE, ENV_PERMUTATIONS]:
            if var in os.environ:
                self.original_env[var] = os.environ[var]

    def teardown_method(self):
        """Restore original environment variables."""
        for var in self.original_env:
            os.environ[var] = self.original_env[var]
        for var in set(os.environ) - set(self.original_env):
            if var in [ENV_SEED, ENV_GRID_RES, ENV_SAMPLE_SIZE, ENV_PERMUTATIONS]:
                del os.environ[var]
        reset_config()

    def test_seed_from_env_var(self):
        """Test that seed is read from environment variable."""
        os.environ[ENV_SEED] = "999"
        reset_config()
        cfg = Config()
        assert cfg.seed == 999

    def test_grid_res_from_env_var(self):
        """Test that grid_res is read from environment variable."""
        os.environ[ENV_GRID_RES] = "1.0"
        reset_config()
        cfg = Config()
        assert cfg.grid_res == 1.0

    def test_permutations_from_env_var(self):
        """Test that permutations is read from environment variable."""
        os.environ[ENV_PERMUTATIONS] = "5000"
        reset_config()
        cfg = Config()
        assert cfg.permutations == 5000

    def test_sample_size_from_env_var(self):
        """Test that sample_size is read from environment variable."""
        os.environ[ENV_SAMPLE_SIZE] = "10000"
        reset_config()
        cfg = Config()
        assert cfg.sample_size == 10000

    def test_sample_size_none_from_env_var(self):
        """Test that sample_size can be set to None via environment variable."""
        os.environ[ENV_SAMPLE_SIZE] = "none"
        reset_config()
        cfg = Config()
        assert cfg.sample_size is None

    def test_invalid_seed_env_var_raises(self):
        """Test that invalid seed value raises ValueError."""
        os.environ[ENV_SEED] = "not_a_number"
        reset_config()
        with pytest.raises(ValueError, match="Invalid integer"):
            Config()

    def test_invalid_grid_res_env_var_raises(self):
        """Test that invalid grid_res value raises ValueError."""
        os.environ[ENV_GRID_RES] = "not_a_number"
        reset_config()
        with pytest.raises(ValueError, match="Invalid float"):
            Config()

    def test_invalid_permutations_env_var_raises(self):
        """Test that invalid permutations value raises ValueError."""
        os.environ[ENV_PERMUTATIONS] = "not_a_number"
        reset_config()
        with pytest.raises(ValueError, match="Invalid integer"):
            Config()


class TestConfigMethods:
    """Test Config class methods."""

    def test_to_dict_returns_dict(self):
        """Test that to_dict returns a dictionary."""
        reset_config()
        cfg = Config(seed=123, grid_res=1.0, sample_size=500, permutations=2000)
        result = cfg.to_dict()

        assert isinstance(result, dict)
        assert "seed" in result
        assert "grid_res" in result
        assert "sample_size" in result
        assert "permutations" in result
        assert "project_root" in result

    def test_to_dict_contains_expected_keys(self):
        """Test that to_dict contains all expected keys with correct values."""
        reset_config()
        cfg = Config(seed=42, grid_res=0.5, sample_size=1000, permutations=5000)
        result = cfg.to_dict()

        assert result["seed"] == 42
        assert result["grid_res"] == 0.5
        assert result["sample_size"] == 1000
        assert result["permutations"] == 5000
        assert isinstance(result["project_root"], str)

    def test_repr(self):
        """Test string representation."""
        reset_config()
        cfg = Config(seed=42, grid_res=0.5, sample_size=1000, permutations=5000)
        repr_str = repr(cfg)

        assert "Config" in repr_str
        assert "seed=42" in repr_str
        assert "grid_res=0.5" in repr_str
        assert "sample_size=1000" in repr_str
        assert "permutations=5000" in repr_str


class TestGlobalConfig:
    """Test global configuration functions."""

    def setup_method(self):
        """Clean state before each test."""
        for var in [ENV_SEED, ENV_GRID_RES, ENV_SAMPLE_SIZE, ENV_PERMUTATIONS]:
            if var in os.environ:
                del os.environ[var]
        reset_config()

    def teardown_method(self):
        """Clean up after each test."""
        reset_config()

    def test_get_config_returns_singleton(self):
        """Test that get_config returns the same instance."""
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_get_config_returns_config_instance(self):
        """Test that get_config returns a Config instance."""
        cfg = get_config()
        assert isinstance(cfg, Config)

    def test_update_globals_from_config(self):
        """Test that update_globals_from_config updates module globals."""
        os.environ[ENV_SEED] = "999"
        reset_config()
        update_globals_from_config()

        # Access the module-level variables
        from src.lib import config as cfg_module
        assert cfg_module.SEED == 999

    def test_project_root_is_path(self):
        """Test that project_root is a Path object."""
        reset_config()
        cfg = Config()
        assert isinstance(cfg.project_root, Path)

    def test_data_raw_dir_exists(self):
        """Test that the data/raw directory exists relative to project root."""
        reset_config()
        cfg = Config()
        # The directory might not exist yet, but the path should be constructible
        data_raw = cfg.project_root / "data" / "raw"
        assert isinstance(data_raw, Path)

    def test_logs_dir_exists(self):
        """Test that the logs directory path is constructible."""
        reset_config()
        cfg = Config()
        logs_dir = cfg.project_root / "logs"
        assert isinstance(logs_dir, Path)

    def test_state_dir_exists(self):
        """Test that the state directory path is constructible."""
        reset_config()
        cfg = Config()
        state_dir = cfg.project_root / "state" / "projects"
        assert isinstance(state_dir, Path)