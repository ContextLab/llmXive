"""
Unit tests for the configuration loader (code/utils/config.py).
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.config import (
    Config,
    get_config,
    PROJECT_ROOT,
    ENV_DATA_DIR,
    ENV_CODE_DIR,
    ENV_DEBUG_MODE,
    ENV_LOG_LEVEL,
)


class TestConfig:
    """Test cases for the Config class."""

    def test_default_data_dir(self):
        """Test that default data directory is set correctly."""
        config = Config()
        expected = PROJECT_ROOT / "data"
        assert config.data_dir == expected

    def test_default_code_dir(self):
        """Test that default code directory is set correctly."""
        config = Config()
        expected = PROJECT_ROOT / "code"
        assert config.code_dir == expected

    def test_debug_mode_default(self):
        """Test that debug mode defaults to False."""
        config = Config()
        assert config.debug is False

    def test_log_level_default(self):
        """Test that log level defaults to INFO."""
        config = Config()
        assert config.log_level == "INFO"

    def test_custom_data_dir_from_env(self, monkeypatch):
        """Test that data directory can be overridden via environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ENV_DATA_DIR, tmpdir)
            config = Config()
            assert config.data_dir == Path(tmpdir)

    def test_custom_code_dir_from_env(self, monkeypatch):
        """Test that code directory can be overridden via environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ENV_CODE_DIR, tmpdir)
            config = Config()
            assert config.code_dir == Path(tmpdir)

    def test_debug_mode_true(self, monkeypatch):
        """Test that debug mode can be set to True."""
        monkeypatch.setenv(ENV_DEBUG_MODE, "true")
        config = Config()
        assert config.debug is True

    def test_debug_mode_1(self, monkeypatch):
        """Test that debug mode can be set to True via '1'."""
        monkeypatch.setenv(ENV_DEBUG_MODE, "1")
        config = Config()
        assert config.debug is True

    def test_debug_mode_yes(self, monkeypatch):
        """Test that debug mode can be set to True via 'yes'."""
        monkeypatch.setenv(ENV_DEBUG_MODE, "yes")
        config = Config()
        assert config.debug is True

    def test_custom_log_level(self, monkeypatch):
        """Test that log level can be overridden via environment variable."""
        monkeypatch.setenv(ENV_LOG_LEVEL, "DEBUG")
        config = Config()
        assert config.log_level == "DEBUG"

    def test_raw_data_dir(self):
        """Test that raw data directory is correctly constructed."""
        config = Config()
        expected = config.data_dir / "data/raw"
        assert config.raw_data_dir == expected

    def test_processed_data_dir(self):
        """Test that processed data directory is correctly constructed."""
        config = Config()
        expected = config.data_dir / "data/processed"
        assert config.processed_data_dir == expected

    def test_cleaned_data_dir(self):
        """Test that cleaned data directory is correctly constructed."""
        config = Config()
        expected = config.data_dir / "data/cleaned"
        assert config.cleaned_data_dir == expected

    def test_model_results_path(self):
        """Test that model results path is correctly constructed."""
        config = Config()
        expected = config.processed_data_dir / "model_results.json"
        assert config.model_results_path == expected

    def test_pipeline_log_path(self):
        """Test that pipeline log path is correctly constructed."""
        config = Config()
        expected = config.processed_data_dir / "pipeline_run_log.json"
        assert config.pipeline_log_path == expected

    def test_scatter_plot_path(self):
        """Test that scatter plot path is correctly constructed."""
        config = Config()
        expected = config.processed_data_dir / "scatter_plot.png"
        assert config.scatter_plot_path == expected

    def test_residuals_plot_path(self):
        """Test that residuals plot path is correctly constructed."""
        config = Config()
        expected = config.processed_data_dir / "residuals.png"
        assert config.residuals_plot_path == expected

    def test_figures_dir(self):
        """Test that figures directory is correctly constructed."""
        config = Config()
        expected = config.data_dir / "figures"
        assert config.figures_dir == expected

    def test_ensure_directories_exist_creates_dirs(self, tmp_path):
        """Test that ensure_directories_exist creates the necessary directories."""
        # Create a temporary config with a custom data dir
        old_data_dir = Config.data_dir.fget(Config)

        # We'll monkeypatch the data_dir property to point to tmp_path
        # But since it's a property, we'll just test the method directly
        # by creating a config and modifying its internal state

        # Simpler approach: create a config and ensure it creates dirs
        # We'll use a temporary directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config()
            # Temporarily override data_dir for this test instance
            # We can't easily override the property, so we'll test
            # the mkdir behavior by checking if directories exist after
            # calling ensure_directories_exist on a fresh path

            # Create a test config with a custom path
            test_config = object.__new__(Config)
            test_config._data_dir = Path(tmpdir)
            test_config._code_dir = Path(tmpdir) / "code"
            test_config._debug = False
            test_config._log_level = "INFO"
            test_config._figures_dir = Path(tmpdir) / "figures"

            # Call the method
            test_config.ensure_directories_exist()

            # Verify directories were created
            assert (Path(tmpdir) / "data").exists()
            assert (Path(tmpdir) / "data/raw").exists()
            assert (Path(tmpdir) / "data/processed").exists()
            assert (Path(tmpdir) / "data/cleaned").exists()
            assert (Path(tmpdir) / "figures").exists()
            assert (Path(tmpdir) / "code").exists()

    def test_get_method(self):
        """Test the get method for retrieving configuration values."""
        config = Config()
        assert config.get("data_dir") == config.data_dir
        assert config.get("debug") == config.debug
        assert config.get("log_level") == config.log_level
        assert config.get("nonexistent_key", "default") == "default"

class TestGetConfig:
    """Test cases for the get_config function."""

    def test_get_config_returns_instance(self):
        """Test that get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_returns_singleton(self):
        """Test that get_config returns the same instance each time."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2