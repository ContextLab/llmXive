"""
Tests for utility functions in code/utils/.

These tests verify the functionality of seed management and memory monitoring.
"""

import os
import sys
import pytest
import random
import numpy as np
import torch

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.seed import set_seed, get_seed_value, DEFAULT_SEED
from utils.memory_monitor import (
    MemoryLimitExceededError,
    get_memory_usage_mb,
    get_peak_memory_mb,
    memory_limit,
    check_memory_limit,
    start_monitoring,
    stop_monitoring,
    memory_limit_context,
    enforce_memory_limit
)


class TestSeedManagement:
    """Tests for seed management functionality."""
    
    def test_set_seed_default(self):
        """Test that set_seed uses default when no argument provided."""
        seed = set_seed()
        assert seed == DEFAULT_SEED
        
        # Verify randomness is controlled
        val1 = random.random()
        set_seed(seed)
        val2 = random.random()
        assert val1 == val2
    
    def test_set_seed_custom(self):
        """Test setting a custom seed value."""
        custom_seed = 12345
        seed = set_seed(custom_seed)
        assert seed == custom_seed
        
        # Verify reproducibility
        random.seed(custom_seed)
        val1 = np.random.rand()
        set_seed(custom_seed)
        val2 = np.random.rand()
        assert val1 == val2
    
    def test_get_seed_from_env(self):
        """Test getting seed from environment variable."""
        original = os.getenv('SEED')
        try:
            os.environ['SEED'] = '999'
            assert get_seed_value() == 999
        finally:
            if original is not None:
                os.environ['SEED'] = original
            elif 'SEED' in os.environ:
                del os.environ['SEED']
    
    def test_get_seed_default_when_env_invalid(self):
        """Test default seed when env variable is invalid."""
        original = os.getenv('SEED')
        try:
            os.environ['SEED'] = 'invalid'
            assert get_seed_value() == DEFAULT_SEED
        finally:
            if original is not None:
                os.environ['SEED'] = original
            elif 'SEED' in os.environ:
                del os.environ['SEED']

class TestMemoryMonitoring:
    """Tests for memory monitoring functionality."""
    
    def setup_method(self):
        """Start monitoring before each test."""
        start_monitoring()
    
    def teardown_method(self):
        """Stop monitoring after each test."""
        stop_monitoring()
    
    def test_memory_usage_starts_at_zero(self):
        """Test that memory usage is tracked."""
        # Usage should be > 0 after starting and doing some work
        _ = [i for i in range(1000)]
        usage = get_memory_usage_mb()
        assert usage >= 0
    
    def test_peak_memory_greater_than_current(self):
        """Test that peak memory is at least current memory."""
        current = get_memory_usage_mb()
        peak = get_peak_memory_mb()
        assert peak >= current
    
    def test_check_memory_limit_no_error(self):
        """Test that check_memory_limit doesn't raise when under limit."""
        # This should not raise
        check_memory_limit()
    
    def test_memory_limit_context(self):
        """Test memory limit context manager."""
        # Should not raise with reasonable limit
        with memory_limit_context(10000):  # 10GB limit
            _ = [i for i in range(10000)]
    
    def test_memory_limit_exceeded(self):
        """Test that MemoryLimitExceededError is raised when limit exceeded."""
        # Set a very low limit for testing
        with pytest.raises(MemoryLimitExceededError):
            with memory_limit_context(0.0001):  # 0.1KB limit
                _ = [i for i in range(100000)]
    
    def test_enforce_memory_limit_context(self):
        """Test enforce_memory_limit context manager."""
        with enforce_memory_limit(10000):
            _ = [i for i in range(1000)]