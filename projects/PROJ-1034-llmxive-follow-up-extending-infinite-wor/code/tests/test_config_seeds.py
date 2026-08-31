"""
Tests for the configuration and seed management module.

These tests verify that:
1. Seeds are correctly initialized from environment variables
2. Random number generation is deterministic across runs
3. Configuration hashing works correctly for reproducibility tracking
"""
import os
import random
import pytest
import sys
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import (
    get_seed_from_env,
    set_seed,
    initialize_reproducibility,
    get_config_hash,
    is_seed_initialized,
    get_current_seed
)


class TestSeedInitialization:
    """Tests for basic seed initialization functionality."""

    def test_get_seed_from_env_default(self):
        """Test that default seed is returned when env var is not set."""
        # Ensure env var is not set
        if 'LLMXIVE_SEED' in os.environ:
            del os.environ['LLMXIVE_SEED']
        
        seed = get_seed_from_env()
        assert seed == 42

    def test_get_seed_from_env_custom(self):
        """Test that custom seed is returned from environment variable."""
        with patch.dict(os.environ, {'LLMXIVE_SEED': '12345'}):
            seed = get_seed_from_env()
            assert seed == 12345

    def test_get_seed_from_env_invalid(self):
        """Test that invalid seed value raises ValueError."""
        with patch.dict(os.environ, {'LLMXIVE_SEED': 'not_a_number'}):
            with pytest.raises(ValueError):
                get_seed_from_env()

    def test_set_seed_python_random(self):
        """Test that set_seed affects Python's random module."""
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2

    def test_set_seed_numpy_random(self):
        """Test that set_seed affects NumPy's random module."""
        set_seed(42)
        val1 = np.random.random()
        
        set_seed(42)
        val2 = np.random.random()
        
        assert val1 == val2

    def test_is_seed_initialized(self):
        """Test that is_seed_initialized returns correct state."""
        assert not is_seed_initialized()
        
        set_seed(42)
        assert is_seed_initialized()

    def test_get_current_seed(self):
        """Test that get_current_seed returns the correct value."""
        assert get_current_seed() is None
        
        set_seed(123)
        assert get_current_seed() == 123


class TestConfigHash:
    """Tests for configuration hashing functionality."""

    def test_get_config_hash_empty(self):
        """Test hashing with empty configuration."""
        hash1 = get_config_hash({})
        hash2 = get_config_hash({})
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_get_config_hash_consistency(self):
        """Test that same config produces same hash."""
        config = {'seed': 42, 'steps': 1000, 'param': 0.5}
        hash1 = get_config_hash(config)
        hash2 = get_config_hash(config)
        assert hash1 == hash2

    def test_get_config_hash_different(self):
        """Test that different configs produce different hashes."""
        config1 = {'seed': 42, 'steps': 1000}
        config2 = {'seed': 42, 'steps': 2000}
        
        hash1 = get_config_hash(config1)
        hash2 = get_config_hash(config2)
        
        assert hash1 != hash2

    def test_get_config_hash_order_independent(self):
        """Test that config key order doesn't affect hash."""
        config1 = {'seed': 42, 'steps': 1000, 'param': 0.5}
        config2 = {'param': 0.5, 'seed': 42, 'steps': 1000}
        
        hash1 = get_config_hash(config1)
        hash2 = get_config_hash(config2)
        
        assert hash1 == hash2


class TestReproducibilityIntegration:
    """Integration tests for full reproducibility workflow."""

    def test_initialize_reproducibility_from_env(self):
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {'LLMXIVE_SEED': '999'}):
            seed, config_hash = initialize_reproducibility()
            assert seed == 999
            assert get_current_seed() == 999
            assert is_seed_initialized()

    def test_initialize_reproducibility_from_config(self):
        """Test initialization from config dictionary."""
        config = {'seed': 777, 'other_param': 'value'}
        seed, config_hash = initialize_reproducibility(config)
        
        assert seed == 777
        assert get_current_seed() == 777
        assert config_hash is not None

    def test_initialize_reproducibility_default(self):
        """Test initialization with default seed."""
        if 'LLMXIVE_SEED' in os.environ:
            del os.environ['LLMXIVE_SEED']
        
        seed, config_hash = initialize_reproducibility()
        assert seed == 42

    def test_initialize_reproducibility_invalid_seed(self):
        """Test that invalid seed raises ValueError."""
        with pytest.raises(ValueError):
            initialize_reproducibility({'seed': -1})

    def test_reproducibility_across_multiple_generations(self):
        """Test that multiple random generations are reproducible."""
        # First run
        initialize_reproducibility({'seed': 42})
        run1_data = [random.random() for _ in range(10)]
        run1_np = np.random.random(10).tolist()
        
        # Second run with same seed
        initialize_reproducibility({'seed': 42})
        run2_data = [random.random() for _ in range(10)]
        run2_np = np.random.random(10).tolist()
        
        # Verify reproducibility
        assert run1_data == run2_data
        assert run1_np == run2_np

    def test_reproducibility_with_numpy_and_random(self):
        """Test reproducibility when using both random modules."""
        initialize_reproducibility({'seed': 123})
        data1 = [random.random() for _ in range(5)]
        np_data1 = np.random.random(5).tolist()
        
        initialize_reproducibility({'seed': 123})
        data2 = [random.random() for _ in range(5)]
        np_data2 = np.random.random(5).tolist()
        
        assert data1 == data2
        assert np_data1 == np_data2

    def test_config_hash_includes_seed(self):
        """Test that config hash changes with seed."""
        config1 = {'seed': 42}
        config2 = {'seed': 99}
        
        hash1 = get_config_hash(config1)
        hash2 = get_config_hash(config2)
        
        assert hash1 != hash2
