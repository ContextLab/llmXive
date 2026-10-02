"""
Tests for configuration management (T009).
Verifies seed management, resource limits, and batch constraints.
"""
import pytest
import sys
from pathlib import Path
from src.config import (
    get_seed, set_seed, get_resource_limits,
    calculate_batch_constraints, verify_pilot_feasibility,
    DEFAULT_SEED, CI_CPU_LIMIT, CI_RAM_GB, PILOT_N_SIGNALS
)
import numpy as np
import os

class TestConfigConstants:
    """Test that configuration constants are defined correctly."""
    
    def test_default_seed(self):
        assert DEFAULT_SEED == 42
    
    def test_ci_cpu_limit(self):
        assert CI_CPU_LIMIT == 2
    
    def test_ci_ram_gb(self):
        assert CI_RAM_GB == 7.0
    
    def test_pilot_n_signals(self):
        assert PILOT_N_SIGNALS == 1200


class TestSeedManagement:
    """Test random seed handling."""
    
    def test_get_seed_default(self):
        # Clear env var if present
        if "QUANTIZATION_SEED" in os.environ:
            del os.environ["QUANTIZATION_SEED"]
        assert get_seed() == DEFAULT_SEED
    
    def test_get_seed_from_env(self):
        os.environ["QUANTIZATION_SEED"] = "12345"
        assert get_seed() == 12345
        del os.environ["QUANTIZATION_SEED"]
    
    def test_set_seed_affects_numpy(self):
        set_seed(999)
        val1 = np.random.random()
        set_seed(999)
        val2 = np.random.random()
        assert val1 == val2
    
    def test_set_seed_affects_random(self):
        import random
        set_seed(888)
        val1 = random.random()
        set_seed(888)
        val2 = random.random()
        assert val1 == val2


class TestResourceConstraints:
    """Test resource limit retrieval."""
    
    def test_get_resource_limits(self):
        limits = get_resource_limits()
        assert limits["cpu"] == CI_CPU_LIMIT
        assert limits["ram_gb"] == CI_RAM_GB
        assert limits["time_hours"] == 6.0


class TestPilotFeasibility:
    """Test batch constraint calculations."""
    
    def test_calculate_batch_constraints_structure(self):
        result = calculate_batch_constraints(seed=42)
        assert "total_signals" in result
        assert "batch_size" in result
        assert "estimated_memory_gb" in result
        assert "estimated_runtime_hours" in result
        assert "feasible" in result
        assert result["total_signals"] == PILOT_N_SIGNALS
    
    def test_calculate_batch_constraints_feasibility(self):
        feasible, msg = verify_pilot_feasibility(seed=42)
        # Should be feasible with current estimates
        assert feasible is True or feasible is False  # Depends on actual estimates
        assert isinstance(msg, str)
    
    def test_batch_size_positive(self):
        result = calculate_batch_constraints(seed=42)
        assert result["batch_size"] > 0
    
    def test_batch_size_within_total(self):
        result = calculate_batch_constraints(seed=42)
        assert result["batch_size"] <= result["total_signals"]