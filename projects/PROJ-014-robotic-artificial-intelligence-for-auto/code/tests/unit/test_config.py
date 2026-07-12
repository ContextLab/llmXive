"""
Unit tests for the configuration management module.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from utils.config import (
    Config, get_config, get_path, get_hyperparameter, 
    set_hyperparameter, set_seed, init_config
)


class TestConfigSingleton:
    """Tests for the Config singleton pattern."""

    def test_singleton_instance(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_init_config_creates_new_instance(self):
        """Test that init_config creates a new instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            new_config = init_config(config_path)
            assert new_config is not None
            assert isinstance(new_config, Config)


class TestPathManagement:
    """Tests for path management functionality."""

    def test_get_path_root(self):
        """Test getting the root path."""
        path = get_path("root")
        assert isinstance(path, Path)
        assert path.exists()

    def test_get_path_data(self):
        """Test getting the data path."""
        path = get_path("data")
        assert isinstance(path, Path)
        assert path.exists()

    def test_get_path_invalid_key(self):
        """Test getting a path with an invalid key raises KeyError."""
        with pytest.raises(KeyError):
            get_path("invalid_key")

    def test_paths_exist(self):
        """Test that all configured paths exist."""
        config = get_config()
        paths = config.get_all_paths()
        for path in paths.values():
            assert path.exists(), f"Path {path} does not exist"


class TestHyperparameterManagement:
    """Tests for hyperparameter management functionality."""

    def test_get_hyperparameter_seed(self):
        """Test getting a specific hyperparameter."""
        seed = get_hyperparameter("seed")
        assert isinstance(seed, int)

    def test_set_hyperparameter(self):
        """Test setting a hyperparameter."""
        set_hyperparameter("test_param", 123)
        assert get_hyperparameter("test_param") == 123

    def test_get_hyperparameter_invalid_key(self):
        """Test getting an invalid hyperparameter raises KeyError."""
        with pytest.raises(KeyError):
            get_hyperparameter("invalid_param")

    def test_all_hyperparameters(self):
        """Test getting all hyperparameters."""
        hparams = get_config().get_all_hyperparameters()
        assert isinstance(hparams, dict)
        assert "seed" in hparams
        assert "num_seeds" in hparams


class TestSeedManagement:
    """Tests for seed management functionality."""

    def test_set_seed(self):
        """Test setting a random seed."""
        seed = set_seed(12345)
        assert seed == 12345
        assert get_hyperparameter("seed") == 12345

    def test_set_seed_default(self):
        """Test setting seed with default value."""
        seed = set_seed()
        assert isinstance(seed, int)

    def test_seed_reproducibility(self):
        """Test that setting the same seed produces the same random sequence."""
        import random
        import numpy as np

        set_seed(42)
        random_val1 = random.random()
        np_val1 = np.random.random()

        set_seed(42)
        random_val2 = random.random()
        np_val2 = np.random.random()

        assert random_val1 == random_val2
        assert np_val1 == np_val2


class TestConfigIO:
    """Tests for configuration save/load functionality."""

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            
            # Create a new config instance for testing
            config = init_config(config_path)
            config.set_hyperparameter("test_save", 42)
            config.save_config()

            # Verify file exists
            assert config_path.exists()

            # Load into a new instance
            new_config = Config(config_path)
            assert new_config.get_hyperparameter("test_save") == 42

    def test_load_nonexistent_config_creates_default(self):
        """Test loading a nonexistent config creates it with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.json"
            
            # Load should create the file
            config = Config(config_path)
            config.load_config()
            
            assert config_path.exists()


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_get_path_function(self):
        """Test the global get_path function."""
        path = get_path("results")
        assert isinstance(path, Path)
        assert path.exists()

    def test_get_hyperparameter_function(self):
        """Test the global get_hyperparameter function."""
        hparam = get_hyperparameter("gamma")
        assert isinstance(hparam, float)
        assert 0.0 < hparam < 1.0

    def test_set_hyperparameter_function(self):
        """Test the global set_hyperparameter function."""
        set_hyperparameter("test_global", "value")
        assert get_hyperparameter("test_global") == "value"