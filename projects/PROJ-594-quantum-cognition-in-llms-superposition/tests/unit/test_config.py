"""
Unit tests for the configuration management module.
"""
import os
import random
import torch
import numpy as np
import pytest

from utils.config import Config, get_config, set_environment


class TestConfigInitialization:
    """Tests for Config class initialization."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = Config()
        assert config.seed == 42
        assert config.device == "cpu"
        assert config.batch_size == 8
        assert config.num_workers == 0
        assert config.max_length == 128
        assert config.learning_rate == 1e-4
        assert config.num_epochs == 3
        assert config.lambda_phase == 0.5

    def test_custom_values(self):
        """Test that custom values override defaults."""
        config = Config(
            seed=123,
            device="cpu",
            batch_size=16,
            num_workers=2,
            max_length=256,
            learning_rate=5e-5,
            num_epochs=5,
            lambda_phase=0.8
        )
        assert config.seed == 123
        assert config.batch_size == 16
        assert config.num_workers == 2
        assert config.max_length == 256
        assert config.learning_rate == 5e-5
        assert config.num_epochs == 5
        assert config.lambda_phase == 0.8

    def test_cpu_only_enforcement(self):
        """Test that GPU devices are rejected."""
        with pytest.raises(ValueError) as excinfo:
            Config(device="cuda")
        assert "GPU devices are not supported" in str(excinfo.value)
        assert "cpu" in str(excinfo.value).lower()

    def test_none_device_defaults_to_cpu(self):
        """Test that None device defaults to CPU."""
        config = Config(device=None)
        assert config.device == "cpu"


class TestSeedPinning:
    """Tests for seed pinning functionality."""

    def test_python_random_seed_pinned(self):
        """Test that Python random seed is pinned."""
        config = Config(seed=42)
        val1 = random.random()
        config2 = Config(seed=42)
        val2 = random.random()
        assert val1 == val2

    def test_numpy_seed_pinned(self):
        """Test that NumPy random seed is pinned."""
        config = Config(seed=42)
        val1 = np.random.rand()
        config2 = Config(seed=42)
        val2 = np.random.rand()
        assert val1 == val2

    def test_torch_seed_pinned(self):
        """Test that PyTorch random seed is pinned."""
        config = Config(seed=42)
        val1 = torch.rand(1).item()
        config2 = Config(seed=42)
        val2 = torch.rand(1).item()
        assert val1 == val2

    def test_deterministic_backends(self):
        """Test that deterministic backends are enabled."""
        config = Config()
        assert torch.backends.cudnn.deterministic is True
        assert torch.backends.cudnn.benchmark is False


class TestConfigToDict:
    """Tests for Config.to_dict() method."""

    def test_to_dict_contains_all_fields(self):
        """Test that to_dict returns all configuration fields."""
        config = Config()
        config_dict = config.to_dict()
        expected_keys = [
            "seed", "device", "batch_size", "num_workers",
            "max_length", "learning_rate", "num_epochs", "lambda_phase"
        ]
        for key in expected_keys:
            assert key in config_dict

    def test_to_dict_values_match_attributes(self):
        """Test that to_dict values match object attributes."""
        config = Config(seed=123, batch_size=16)
        config_dict = config.to_dict()
        assert config_dict["seed"] == config.seed
        assert config_dict["batch_size"] == config.batch_size
        assert config_dict["device"] == config.device


class TestGetConfigFactory:
    """Tests for get_config factory function."""

    def test_get_config_returns_config_instance(self):
        """Test that get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_with_overrides(self):
        """Test that get_config applies overrides."""
        config = get_config(seed=999, batch_size=32)
        assert config.seed == 999
        assert config.batch_size == 32

    def test_get_config_with_device_override(self):
        """Test that get_config enforces CPU-only device."""
        with pytest.raises(ValueError):
            get_config(device="cuda")


class TestSetEnvironment:
    """Tests for set_environment function."""

    def test_sets_pythonhashseed(self):
        """Test that set_environment sets PYTHONHASHSEED."""
        # Clear the env var first
        if "PYTHONHASHSEED" in os.environ:
            del os.environ["PYTHONHASHSEED"]

        set_environment()
        assert "PYTHONHASHSEED" in os.environ
        assert os.environ["PYTHONHASHSEED"] == "42"