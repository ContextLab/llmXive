"""
Unit tests for the configuration management module.
"""
import os
import pytest
from unittest.mock import patch
from code.config import Config, get_config, reload_config

class TestConfig:
    """Tests for the Config class."""

    def test_default_values(self):
        """Test that default values are set correctly when no env vars are present."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert len(config.dataset_urls) == 2
            assert "UCI-HAR-Dataset" in config.dataset_urls[0]
            assert config.output_path == "data/processed"
            assert config.random_seed == 42
            assert config.bootstrap_iterations == 1000

    def test_custom_dataset_urls(self):
        """Test custom DATASET_URLS from environment variable."""
        custom_urls = "http://example.com/d1.zip,http://example.com/d2.zip"
        with patch.dict(os.environ, {"DATASET_URLS": custom_urls}):
            config = Config()
            assert config.dataset_urls == ["http://example.com/d1.zip", "http://example.com/d2.zip"]

    def test_custom_output_path(self):
        """Test custom OUTPUT_PATH from environment variable."""
        with patch.dict(os.environ, {"OUTPUT_PATH": "custom/output/path"}):
            config = Config()
            assert config.output_path == "custom/output/path"

    def test_custom_random_seed(self):
        """Test custom RANDOM_SEED from environment variable."""
        with patch.dict(os.environ, {"RANDOM_SEED": "123"}):
            config = Config()
            assert config.random_seed == 123

    def test_custom_bootstrap_iterations(self):
        """Test custom BOOTSTRAP_ITERATIONS from environment variable."""
        with patch.dict(os.environ, {"BOOTSTRAP_ITERATIONS": "2500"}):
            config = Config()
            assert config.bootstrap_iterations == 2500

    def test_invalid_random_seed(self):
        """Test that negative random seed raises ValueError."""
        with patch.dict(os.environ, {"RANDOM_SEED": "-1"}):
            with pytest.raises(ValueError, match="RANDOM_SEED must be non-negative"):
                Config()

    def test_invalid_bootstrap_iterations(self):
        """Test that bootstrap iterations < 100 raises ValueError."""
        with patch.dict(os.environ, {"BOOTSTRAP_ITERATIONS": "50"}):
            with pytest.raises(ValueError, match="BOOTSTRAP_ITERATIONS must be at least 100"):
                Config()

    def test_empty_dataset_urls(self):
        """Test that empty DATASET_URLS raises ValueError."""
        with patch.dict(os.environ, {"DATASET_URLS": ""}):
            with pytest.raises(ValueError, match="DATASET_URLS cannot be empty"):
                Config()

    def test_get_config_singleton(self):
        """Test that get_config returns a singleton instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reload_config(self):
        """Test that reload_config creates a new instance."""
        config1 = reload_config()
        with patch.dict(os.environ, {"RANDOM_SEED": "999"}):
            config2 = reload_config()
            assert config2.random_seed == 999
            assert config1.random_seed != config2.random_seed

    def test_repr(self):
        """Test the __repr__ method."""
        with patch.dict(os.environ, {"RANDOM_SEED": "100"}):
            config = Config()
            repr_str = repr(config)
            assert "random_seed=100" in repr_str
            assert "data/processed" in repr_str
            assert "dataset_urls" in repr_str
            assert "bootstrap_iterations" in repr_str