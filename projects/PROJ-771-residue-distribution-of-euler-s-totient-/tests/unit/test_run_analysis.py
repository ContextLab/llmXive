"""
Unit tests for the configuration loader in code/run_analysis.py.

Tests verify:
- Default configuration values are applied correctly.
- Override values are accepted.
- Validation logic rejects invalid primes.
- Validation logic rejects invalid N.
"""

import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from run_analysis import Config, load_config, DEFAULT_PRIMES, DEFAULT_N, DEFAULT_MEMORY_LIMIT_MB


class TestConfigValidation:
    """Tests for Config class validation logic."""
    
    def test_default_config(self):
        """Test that default config uses standard values."""
        config = Config()
        assert config.N == DEFAULT_N
        assert config.primes == DEFAULT_PRIMES
        assert config.memory_limit_mb == DEFAULT_MEMORY_LIMIT_MB
        assert config.seed is not None  # Default seed should be set
    
    def test_custom_config(self):
        """Test that custom values are applied."""
        config = Config(N=500000, primes=[3, 7], memory_limit_mb=2048, seed=123)
        assert config.N == 500000
        assert config.primes == [3, 7]
        assert config.memory_limit_mb == 2048
        assert config.seed == 123
    
    def test_invalid_prime_rejected(self):
        """Test that primes outside {3, 5, 7, 11} raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Config(primes=[3, 13])
        assert "13" in str(exc_info.value)
    
    def test_invalid_n_rejected(self):
        """Test that N < 1 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Config(N=0)
        assert "positive" in str(exc_info.value).lower()
        
        with pytest.raises(ValueError) as exc_info:
            Config(N=-100)
        assert "positive" in str(exc_info.value).lower()
    
    def test_low_memory_limit_rejected(self):
        """Test that memory_limit < 64 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Config(memory_limit_mb=10)
        assert "64" in str(exc_info.value)
    
    def test_load_config_factory(self):
        """Test the load_config factory function."""
        config = load_config(N=100, primes=[5], memory_limit_mb=1000, seed=99)
        assert config.N == 100
        assert config.primes == [5]
        assert config.memory_limit_mb == 1000
        assert config.seed == 99
    
    def test_load_config_defaults(self):
        """Test load_config with no arguments uses defaults."""
        config = load_config()
        assert config.N == DEFAULT_N
        assert config.primes == DEFAULT_PRIMES
        assert config.memory_limit_mb == DEFAULT_MEMORY_LIMIT_MB