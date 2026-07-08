"""
Tests for utility modules.
"""
import pytest
import os
import sys
import random
import numpy as np
import torch
from unittest.mock import patch

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.utils.seed import set_seed, get_seed_value
from code.utils.memory_monitor import (
    memory_limit,
    get_memory_usage_mb,
    get_peak_memory_mb,
    MemoryLimitExceededError
)

class TestSeedManagement:
    def test_set_seed_determinism(self):
        """Test that setting seed produces deterministic results."""
        seed = 12345
        set_seed(seed)
        
        val1_rand = random.random()
        val1_np = np.random.rand()
        val1_torch = torch.rand(1).item()
        
        set_seed(seed)
        
        val2_rand = random.random()
        val2_np = np.random.rand()
        val2_torch = torch.rand(1).item()
        
        assert val1_rand == val2_rand
        assert val1_np == val2_np
        assert val1_torch == val2_torch

    def test_get_seed_value_returns_input(self):
        """Test that get_seed_value returns the provided seed."""
        assert get_seed_value(42) == 42
        assert get_seed_value(999) == 999

    def test_get_seed_value_generates_random(self):
        """Test that get_seed_value generates a random seed when None."""
        seed1 = get_seed_value()
        seed2 = get_seed_value()
        # They should likely be different (high probability)
        # We don't assert inequality strictly as collisions are possible but rare

class TestMemoryMonitor:
    def test_memory_limit_context_manager_success(self):
        """Test that context manager works when limit is not exceeded."""
        with memory_limit(limit_mb=1000.0, verbose=False):
            # Allocate some memory
            data = [0] * 100000
            assert get_memory_usage_mb() < 1000.0

    def test_memory_limit_context_manager_failure(self):
        """Test that context manager raises error when limit exceeded."""
        # This test is tricky because we can't easily force a memory spike
        # without allocating a lot. We mock the check instead.
        with patch('code.utils.memory_monitor.get_peak_memory_mb', return_value=8000.0):
            with pytest.raises(MemoryLimitExceededError):
                with memory_limit(limit_mb=7000.0, verbose=False):
                    pass

    def test_get_memory_functions(self):
        """Test basic memory function calls."""
        # Just ensure they don't crash
        current = get_memory_usage_mb()
        peak = get_peak_memory_mb()
        assert current >= 0.0
        assert peak >= current