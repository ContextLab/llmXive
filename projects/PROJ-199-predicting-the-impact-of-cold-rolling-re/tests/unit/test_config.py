"""
Unit tests for configuration loading and seed management.
"""
import os
import pytest
from pathlib import Path
import numpy as np
import random

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code import (
    get_seed,
    set_seed,
    get_log_level,
    get_data_path,
    get_reductions,
    ConfigurationError,
    DEFAULT_SEED,
    DEFAULT_LOG_LEVEL,
    DEFAULT_DATA_PATH,
    DEFAULT_REDUCTION_LEVELS
)

class TestGetSeed:
    """Tests for get_seed function."""

    def test_default_seed(self):
        """Test that default seed is returned when env var is not set."""
        # Ensure env var is not set
        if ENV_SEED in os.environ:
            del os.environ[ENV_SEED]
        
        seed = get_seed()
        assert seed == DEFAULT_SEED

    def test_custom_seed_from_env(self):
        """Test that custom seed is returned when env var is set."""
        os.environ[ENV_SEED] = "12345"
        try:
            seed = get_seed()
            assert seed == 12345
        finally:
            del os.environ[ENV_SEED]

    def test_invalid_seed_raises_error(self):
        """Test that invalid seed value raises ConfigurationError."""
        os.environ[ENV_SEED] = "not_a_number"
        try:
            with pytest.raises(ConfigurationError):
                get_seed()
        finally:
            del os.environ[ENV_SEED]

class TestSetSeed:
    """Tests for set_seed function."""

    def test_set_seed_affects_random(self):
        """Test that set_seed affects random module."""
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2

    def test_set_seed_affects_numpy(self):
        """Test that set_seed affects numpy."""
        set_seed(42)
        arr1 = np.random.rand(5)
        
        set_seed(42)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2)

    def test_set_seed_with_custom_value(self):
        """Test that set_seed works with custom value."""
        set_seed(999)
        val = random.random()
        
        set_seed(999)
        val2 = random.random()
        
        assert val == val2

class TestGetLogLevel:
    """Tests for get_log_level function."""

    def test_default_log_level(self):
        """Test that default log level is returned when env var is not set."""
        if ENV_LOG_LEVEL in os.environ:
            del os.environ[ENV_LOG_LEVEL]
        
        level = get_log_level()
        assert level == DEFAULT_LOG_LEVEL

    def test_custom_log_level_from_env(self):
        """Test that custom log level is returned when env var is set."""
        os.environ[ENV_LOG_LEVEL] = "DEBUG"
        try:
            level = get_log_level()
            assert level == "DEBUG"
        finally:
            del os.environ[ENV_LOG_LEVEL]

class TestGetDataPath:
    """Tests for get_data_path function."""

    def test_default_data_path(self):
        """Test that default data path is returned when env var is not set."""
        if ENV_DATA_PATH in os.environ:
            del os.environ[ENV_DATA_PATH]
        
        path = get_data_path()
        assert path == Path(DEFAULT_DATA_PATH)

    def test_custom_data_path_from_env(self):
        """Test that custom data path is returned when env var is set."""
        os.environ[ENV_DATA_PATH] = "/custom/data/path"
        try:
            path = get_data_path()
            assert path == Path("/custom/data/path")
        finally:
            del os.environ[ENV_DATA_PATH]

class TestGetReductions:
    """Tests for get_reductions function."""

    def test_default_reductions(self):
        """Test that default reductions are returned when env var is not set."""
        if ENV_REDUCTION_LEVELS in os.environ:
            del os.environ[ENV_REDUCTION_LEVELS]
        
        reductions = get_reductions()
        assert reductions == DEFAULT_REDUCTION_LEVELS

    def test_custom_reductions_from_env(self):
        """Test that custom reductions are returned when env var is set."""
        os.environ[ENV_REDUCTION_LEVELS] = "0, 10, 20, 30"
        try:
            reductions = get_reductions()
            assert reductions == [0, 10, 20, 30]
        finally:
            del os.environ[ENV_REDUCTION_LEVELS]

    def test_invalid_reductions_raises_error(self):
        """Test that invalid reduction values raise ConfigurationError."""
        os.environ[ENV_REDUCTION_LEVELS] = "0, abc, 20"
        try:
            with pytest.raises(ConfigurationError):
                get_reductions()
        finally:
            del os.environ[ENV_REDUCTION_LEVELS]

    def test_empty_reductions_uses_default(self):
        """Test that empty reduction string uses default."""
        os.environ[ENV_REDUCTION_LEVELS] = ""
        try:
            reductions = get_reductions()
            assert reductions == DEFAULT_REDUCTION_LEVELS
        finally:
            del os.environ[ENV_REDUCTION_LEVELS]

# Environment variable names
ENV_SEED = "LLMXIVE_SEED"
ENV_LOG_LEVEL = "LLMXIVE_LOG_LEVEL"
ENV_DATA_PATH = "LLMXIVE_DATA_PATH"
ENV_REDUCTION_LEVELS = "LLMXIVE_REDUCTION_LEVELS"
