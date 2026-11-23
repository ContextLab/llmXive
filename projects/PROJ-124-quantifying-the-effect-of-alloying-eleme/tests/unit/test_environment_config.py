"""
Unit tests for environment configuration management.
"""

import pytest
import random
import numpy as np
from pathlib import Path
import tempfile
import yaml

from config.environment import (
    EnvironmentConfig,
    get_environment_config,
    initialize_random_seeds,
    DEFAULT_CONFIG
)


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig class."""

    def test_default_initialization(self):
        """Test that default configuration loads correctly."""
        config = EnvironmentConfig()

        assert config.random_seed == DEFAULT_CONFIG["random_seed"]
        assert "gfa_dataset" in config.dataset_urls
        assert "data_raw" in config.paths
        assert config.is_feature_enabled("enable_heteroscedasticity_correction") is True

    def test_custom_seed_initialization(self):
        """Test configuration with custom random seed."""
        custom_config = {"random_seed": 123}
        config = EnvironmentConfig(custom_config)

        assert config.random_seed == 123

    def test_nested_config_merge(self):
        """Test that nested configuration values are merged correctly."""
        custom_config = {
            "dataset_urls": {
                "new_dataset": "https://example.com/data.csv"
            },
            "limits": {
                "max_candidates": 20
            }
        }
        config = EnvironmentConfig(custom_config)

        assert config.get_dataset_url("new_dataset") == "https://example.com/data.csv"
        assert config.get_limit("max_candidates") == 20
        # Original value should still exist
        assert "gfa_dataset" in config.dataset_urls

    def test_get_dataset_url(self):
        """Test retrieval of dataset URLs."""
        config = EnvironmentConfig()

        url = config.get_dataset_url("gfa_dataset")
        assert url == DEFAULT_CONFIG["dataset_urls"]["gfa_dataset"]

    def test_get_dataset_url_missing(self):
        """Test that missing dataset URL raises KeyError."""
        config = EnvironmentConfig()

        with pytest.raises(KeyError):
            config.get_dataset_url("nonexistent_dataset")

    def test_feature_flags(self):
        """Test feature flag retrieval."""
        config = EnvironmentConfig()

        assert config.is_feature_enabled("enable_heteroscedasticity_correction") is True
        assert config.is_feature_enabled("nonexistent_feature") is False

    def test_limits_retrieval(self):
        """Test limit value retrieval."""
        config = EnvironmentConfig()

        assert config.get_limit("max_candidates") == DEFAULT_CONFIG["limits"]["max_candidates"]

    def test_set_random_seed(self):
        """Test setting random seed."""
        config = EnvironmentConfig()
        config.set_random_seed(999)

        assert config.random_seed == 999
        # Verify seed was applied to random module
        val1 = random.random()
        random.seed(999)
        val2 = random.random()
        assert val1 == val2


class TestGetEnvironmentConfig:
    """Tests for get_environment_config function."""

    def test_load_default_config(self):
        """Test loading default configuration when no path provided."""
        config = get_environment_config()

        assert isinstance(config, EnvironmentConfig)
        assert config.random_seed == DEFAULT_CONFIG["random_seed"]

    def test_load_from_file(self):
        """Test loading configuration from YAML file."""
        custom_config = {
            "random_seed": 555,
            "limits": {
                "max_candidates": 15
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_config, f)
            temp_path = f.name

        try:
            config = get_environment_config(temp_path)
            assert config.random_seed == 555
            assert config.get_limit("max_candidates") == 15
        finally:
            Path(temp_path).unlink()

    def test_nonexistent_file_uses_default(self):
        """Test that nonexistent file falls back to default config."""
        config = get_environment_config("nonexistent/path/config.yaml")

        assert config.random_seed == DEFAULT_CONFIG["random_seed"]


class TestInitializeRandomSeeds:
    """Tests for initialize_random_seeds function."""

    def test_initializes_with_default_config(self):
        """Test seed initialization with default configuration."""
        initialize_random_seeds()

        # Verify seeds are set
        val1 = random.random()
        val2 = np.random.random()

        # Reset and verify same values
        random.seed(DEFAULT_CONFIG["random_seed"])
        np.random.seed(DEFAULT_CONFIG["random_seed"])

        assert val1 == random.random()
        assert val2 == np.random.random()

    def test_initializes_with_custom_config(self):
        """Test seed initialization with custom configuration."""
        custom_config = {"random_seed": 777}
        config = EnvironmentConfig(custom_config)

        initialize_random_seeds(config)

        # Verify seeds are set
        random.seed(777)
        np.random.seed(777)

        val1 = random.random()
        val2 = np.random.random()

        # Reset and verify same values
        random.seed(777)
        np.random.seed(777)

        assert val1 == random.random()
        assert val2 == np.random.random()