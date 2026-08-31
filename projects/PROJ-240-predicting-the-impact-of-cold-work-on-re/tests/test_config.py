"""
Unit tests for the configuration management module.
"""
import os
import pytest
from pathlib import Path
from code.config import (
    load_env_config,
    get_config_value,
    N_PERMUTATIONS,
    RANDOM_SEED,
    TEST_SIZE,
    MAX_DATASET_ROWS,
    MIN_DATASET_ROWS,
    COLD_WORK_MIN,
    COLD_WORK_MAX,
    PROJECT_ROOT,
    DATA_RAW_DIR,
    ARTIFACTS_REPORTS_DIR
)


class TestConfigConstants:
    """Test that configuration constants are correctly defined."""

    def test_n_permutations_default(self):
        """Test that N_PERMUTATIONS defaults to 1000."""
        assert N_PERMUTATIONS == 1000

    def test_random_seed_default(self):
        """Test that RANDOM_SEED defaults to 42."""
        assert RANDOM_SEED == 42

    def test_test_size_default(self):
        """Test that TEST_SIZE defaults to 0.2."""
        assert TEST_SIZE == 0.2

    def test_max_dataset_rows_default(self):
        """Test that MAX_DATASET_ROWS defaults to 10000."""
        assert MAX_DATASET_ROWS == 10000

    def test_min_dataset_rows_default(self):
        """Test that MIN_DATASET_ROWS defaults to 50."""
        assert MIN_DATASET_ROWS == 50

    def test_cold_work_bounds(self):
        """Test that cold work bounds are correctly defined."""
        assert COLD_WORK_MIN == 0.0
        assert COLD_WORK_MAX == 100.0

    def test_project_root_exists(self):
        """Test that PROJECT_ROOT is a valid Path."""
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()

    def test_data_dirs_exist(self):
        """Test that expected data directories are configured."""
        assert isinstance(DATA_RAW_DIR, Path)
        assert isinstance(ARTIFACTS_REPORTS_DIR, Path)


class TestConfigFunctions:
    """Test configuration utility functions."""

    def test_get_config_value_with_env(self, monkeypatch):
        """Test get_config_value retrieves environment variables."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = get_config_value("TEST_VAR")
        assert result == "test_value"

    def test_get_config_value_default(self):
        """Test get_config_value returns default when key missing."""
        result = get_config_value("NON_EXISTENT_VAR", "default_value")
        assert result == "default_value"

    def test_load_env_config_nonexistent_file(self, tmp_path):
        """Test load_env_config with non-existent file."""
        result = load_env_config(tmp_path / "nonexistent.env")
        assert result == {}

    def test_load_env_config_with_content(self, tmp_path):
        """Test load_env_config parses .env file correctly."""
        env_file = tmp_path / "test.env"
        env_file.write_text(
            "KEY1=value1\n"
            "KEY2=value2\n"
            "# Comment line\n"
            "KEY3=value3\n"
        )
        result = load_env_config(env_file)
        assert result == {
            "KEY1": "value1",
            "KEY2": "value2",
            "KEY3": "value3"
        }

    def test_load_env_config_ignores_comments(self, tmp_path):
        """Test load_env_config ignores comment lines."""
        env_file = tmp_path / "test.env"
        env_file.write_text(
            "# This is a comment\n"
            "KEY=value\n"
            "  # Indented comment\n"
        )
        result = load_env_config(env_file)
        assert result == {"KEY": "value"}

    def test_load_env_config_handles_spaces(self, tmp_path):
        """Test load_env_config handles spaces around keys and values."""
        env_file = tmp_path / "test.env"
        env_file.write_text(
            "KEY1 = value1\n"
            "KEY2= value2\n"
            "KEY3 =value3\n"
        )
        result = load_env_config(env_file)
        assert result == {
            "KEY1": "value1",
            "KEY2": "value2",
            "KEY3": "value3"
        }


class TestConfigEnvironmentOverride:
    """Test that environment variables override defaults."""

    def test_n_permutations_override(self, monkeypatch):
        """Test N_PERMUTATIONS can be overridden via environment."""
        monkeypatch.setenv("N_PERMUTATIONS", "2000")
        # Reload the module to pick up the new environment variable
        import importlib
        import code.config
        importlib.reload(code.config)
        assert code.config.N_PERMUTATIONS == 2000
        # Reload back to original for other tests
        monkeypatch.delenv("N_PERMUTATIONS")
        importlib.reload(code.config)
        assert code.config.N_PERMUTATIONS == 1000

    def test_random_seed_override(self, monkeypatch):
        """Test RANDOM_SEED can be overridden via environment."""
        monkeypatch.setenv("RANDOM_SEED", "123")
        import importlib
        import code.config
        importlib.reload(code.config)
        assert code.config.RANDOM_SEED == 123
        monkeypatch.delenv("RANDOM_SEED")
        importlib.reload(code.config)
        assert code.config.RANDOM_SEED == 42
