"""
Unit tests for code/config.py
"""
import pytest
import os
import tempfile
from code.config import Config, get_config, set_random_seed
import numpy as np


class TestConfig:
    def test_config_creation(self):
        config = Config(
            agp_url="https://example.com/agp",
            hrs_url="https://example.com/hrs",
            random_seed=42,
            max_ram_gb=7
        )
        assert config.agp_url == "https://example.com/agp"
        assert config.hrs_url == "https://example.com/hrs"
        assert config.random_seed == 42
        assert config.max_ram_gb == 7

    def test_config_defaults(self):
        config = Config()
        assert config.random_seed is not None
        assert config.max_ram_gb == 7

    def test_config_to_dict(self):
        config = Config(random_seed=123, max_ram_gb=6)
        result = config.to_dict()
        assert result["random_seed"] == 123
        assert result["max_ram_gb"] == 6

    def test_config_from_dict(self):
        data = {
            "agp_url": "https://test.com",
            "hrs_url": "https://test.com",
            "random_seed": 999,
            "max_ram_gb": 5
        }
        config = Config.from_dict(data)
        assert config.random_seed == 999
        assert config.max_ram_gb == 5


class TestGetConfig:
    def test_get_config_returns_instance(self):
        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_singleton(self):
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2


class TestSetRandomSeed:
    def test_set_random_seed_affects_numpy(self):
        set_random_seed(42)
        val1 = np.random.rand()
        
        set_random_seed(42)
        val2 = np.random.rand()
        
        assert val1 == val2

    def test_set_random_seed_sets_config(self):
        set_random_seed(12345)
        config = get_config()
        assert config.random_seed == 12345