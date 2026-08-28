"""
Unit tests for the deterministic seed configuration module.
"""
import os
import random
import pytest

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Import the module under test
import sys
import importlib
# Ensure we are importing from the code directory
if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from config import (
    get_seed_from_env, 
    set_seed, 
    initialize_reproducibility, 
    DEFAULT_SEED, 
    SEED_ENV_VAR,
    get_config_hash
)


class TestSeedInitialization:
    """Tests for seed retrieval and setting."""

    def test_get_seed_from_env_default(self, monkeypatch):
        """Test that default seed is returned when env var is missing."""
        monkeypatch.delenv(SEED_ENV_VAR, raising=False)
        seed = get_seed_from_env()
        assert seed == DEFAULT_SEED

    def test_get_seed_from_env_custom(self, monkeypatch):
        """Test that custom seed is returned when env var is set."""
        custom_seed = 12345
        monkeypatch.setenv(SEED_ENV_VAR, str(custom_seed))
        seed = get_seed_from_env()
        assert seed == custom_seed

    def test_get_seed_from_env_invalid_fallback(self, monkeypatch):
        """Test fallback to default when env var is not an integer."""
        monkeypatch.setenv(SEED_ENV_VAR, "not_a_number")
        seed = get_seed_from_env(default=999)
        assert seed == 999

    def test_set_seed_random(self):
        """Test that random module is seeded correctly."""
        seed = 42
        set_seed(seed)
        val1 = random.random()
        
        set_seed(seed)
        val2 = random.random()
        
        assert val1 == val2

    @pytest.mark.skipif(not HAS_NUMPY, reason="NumPy not installed")
    def test_set_seed_numpy(self):
        """Test that numpy random is seeded correctly."""
        seed = 42
        set_seed(seed)
        arr1 = np.random.rand(5)
        
        set_seed(seed)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2)

    @pytest.mark.skipif(not HAS_TORCH, reason="PyTorch not installed")
    def test_set_seed_torch(self):
        """Test that torch random is seeded correctly."""
        seed = 42
        set_seed(seed)
        tensor1 = torch.rand(5)
        
        set_seed(seed)
        tensor2 = torch.rand(5)
        
        assert torch.equal(tensor1, tensor2)

    def test_set_seed_returns_status(self):
        """Test that set_seed returns a status dictionary."""
        status = set_seed(42)
        assert isinstance(status, dict)
        assert "random" in status
        assert status["random"] is True
        if HAS_NUMPY:
            assert status["numpy"] is True
        else:
            assert status["numpy"] is False
        if HAS_TORCH:
            assert status["torch"] is True
        else:
            assert status["torch"] is False

    def test_initialize_reproducibility(self, monkeypatch):
        """Test the main initialization function."""
        monkeypatch.delenv(SEED_ENV_VAR, raising=False)
        result = initialize_reproducibility(seed=999)
        
        assert result["seed"] == 999
        assert "status" in result
        assert "message" in result
        assert "Reproducibility initialized" in result["message"]

class TestConfigHash:
    """Tests for configuration hashing."""

    def test_config_hash_deterministic(self):
        """Test that the same config produces the same hash."""
        config = {"learning_rate": 0.01, "epochs": 10}
        hash1 = get_config_hash(config)
        hash2 = get_config_hash(config)
        assert hash1 == hash2

    def test_config_hash_different(self):
        """Test that different configs produce different hashes."""
        config1 = {"learning_rate": 0.01}
        config2 = {"learning_rate": 0.02}
        assert get_config_hash(config1) != get_config_hash(config2)

    def test_config_hash_order_independent(self):
        """Test that key order does not affect the hash."""
        config1 = {"a": 1, "b": 2}
        config2 = {"b": 2, "a": 1}
        assert get_config_hash(config1) == get_config_hash(config2)

class TestReproducibilityIntegration:
    """Integration test to verify reproducibility across multiple calls."""

    def test_full_reproducibility_cycle(self, monkeypatch):
        """Verify that a full cycle of seeding produces identical results."""
        monkeypatch.delenv(SEED_ENV_VAR, raising=False)
        
        # First run
        initialize_reproducibility(seed=123)
        r1 = random.random()
        if HAS_NUMPY:
            n1 = np.random.rand(3)
        if HAS_TORCH:
            t1 = torch.rand(3)

        # Second run with same seed
        initialize_reproducibility(seed=123)
        r2 = random.random()
        if HAS_NUMPY:
            n2 = np.random.rand(3)
        if HAS_TORCH:
            t2 = torch.rand(3)

        # Verify equality
        assert r1 == r2
        if HAS_NUMPY:
            assert np.array_equal(n1, n2)
        if HAS_TORCH:
            assert torch.equal(t1, t2)
