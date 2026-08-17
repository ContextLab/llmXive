"""
Tests for the configuration management module (src/config.py).
Verifies seed management, resource limits, and batch constraint calculations.
"""
import pytest
import sys
from pathlib import Path
from src.config import (
    get_seed, set_seed, get_resource_limits, 
    calculate_batch_constraints, verify_pilot_feasibility,
    CI_RAM_LIMIT_GB, CI_CPU_LIMIT, PILOT_N_SIGNALS
)
import numpy as np
import os

class TestConfigConstants:
    """Test that hardcoded CI limits match the specification."""
    
    def test_cpu_limit_is_two(self):
        assert CI_CPU_LIMIT == 2, "CI CPU limit must be 2 as per specification."
    
    def test_ram_limit_is_seven_gb(self):
        assert CI_RAM_LIMIT_GB == 7.0, "CI RAM limit must be 7.0 GB as per specification."

class TestSeedManagement:
    """Test random seed retrieval and setting."""
    
    def test_get_seed_default(self):
        # Ensure env var is not set
        if "QUANTIZATION_SEED" in os.environ:
            del os.environ["QUANTIZATION_SEED"]
        seed = get_seed()
        assert seed == 42, "Default seed should be 42."
    
    def test_get_seed_from_env(self):
        os.environ["QUANTIZATION_SEED"] = "12345"
        seed = get_seed()
        assert seed == 12345, "Seed should be read from environment variable."
        del os.environ["QUANTIZATION_SEED"]
    
    def test_set_seed_affects_numpy(self):
        set_seed(42)
        val1 = np.random.random()
        set_seed(42)
        val2 = np.random.random()
        assert val1 == val2, "Setting the same seed should produce same numpy random values."

class TestResourceConstraints:
    """Test resource limit reporting."""
    
    def test_resource_limits_format(self):
        limits = get_resource_limits()
        assert "cpu_limit" in limits
        assert "ram_limit_gb" in limits
        assert "ram_limit_bytes" in limits
        assert "time_limit_seconds" in limits
        assert limits["cpu_limit"] == 2
        assert limits["ram_limit_gb"] == 7.0

class TestPilotFeasibility:
    """Test batch size calculations and feasibility checks."""
    
    def test_calculate_batch_constraints_returns_dict(self):
        constraints = calculate_batch_constraints()
        assert isinstance(constraints, dict)
        assert "max_batch_size" in constraints
        assert "recommended_batch_size" in constraints
        assert "pilot_n_signals" in constraints
        assert constraints["pilot_n_signals"] == 1200
    
    def test_pilot_feasibility_logic(self):
        feasible, message = verify_pilot_feasibility()
        # We expect the pilot to be feasible based on our memory estimates
        # If this fails, it means our memory estimation constants are too high
        # or the CI limits are too low.
        assert feasible, f"Pilot feasibility check failed: {message}"
    
    def test_batch_size_within_ram_limit(self):
        constraints = calculate_batch_constraints()
        # The recommended batch size should definitely fit in RAM
        # (Total RAM for batch < 7GB * 0.8 safety factor)
        batch_memory_gb = (constraints["recommended_batch_size"] * 0.5) / 1024 # 0.5MB per signal
        assert batch_memory_gb < CI_RAM_LIMIT_GB, "Recommended batch size exceeds RAM limit."