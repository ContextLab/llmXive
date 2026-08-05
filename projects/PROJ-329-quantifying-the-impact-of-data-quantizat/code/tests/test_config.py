"""
Tests for T009: Environment configuration and batch constraints.
"""
import pytest
import sys
from pathlib import Path
from src.config import (
    get_seed, set_seed, get_resource_limits, 
    calculate_batch_constraints, verify_pilot_feasibility,
    DEFAULT_SEED, CI_CPU_LIMIT, CI_RAM_LIMIT_GB, PILOT_N_SIGNALS
)
import numpy as np
import os

class TestConfigConstants:
    def test_default_seed(self):
        assert DEFAULT_SEED == 42
    
    def test_cpu_limit(self):
        assert CI_CPU_LIMIT == 2
    
    def test_ram_limit(self):
        assert CI_RAM_LIMIT_GB == 7.0
    
    def test_pilot_n(self):
        assert PILOT_N_SIGNALS == 1200

class TestSeedManagement:
    def test_get_seed_default(self):
        # Ensure env var is not set for this test
        if "GW_QUANT_SEED" in os.environ:
            del os.environ["GW_QUANT_SEED"]
        assert get_seed() == DEFAULT_SEED
    
    def test_get_seed_override(self):
        assert get_seed(seed_override=123) == 123
    
    def test_get_seed_env_var(self, monkeypatch):
        monkeypatch.setenv("GW_QUANT_SEED", "999")
        assert get_seed() == 999
    
    def test_set_seed(self, monkeypatch):
        monkeypatch.setenv("NOW", "test_time")
        set_seed(555)
        # Check that numpy seed is set
        assert np.random.get_state()[1][0] == 555

class TestResourceConstraints:
    def test_get_resource_limits(self):
        limits = get_resource_limits()
        assert limits["cpu"] == 2
        assert limits["ram_gb"] == 7.0
        assert limits["time_hours"] == 6.0

class TestPilotFeasibility:
    def test_calculate_batch_constraints(self):
        constraints = calculate_batch_constraints()
        assert constraints["pilot_n_signals"] == 1200
        assert len(constraints["bit_depths"]) == 6
        assert len(constraints["snr_bins"]) == 4
        assert "feasibility_status" in constraints
        assert "estimates" in constraints
    
    def test_feasibility_check(self):
        is_feasible, message = verify_pilot_feasibility()
        assert isinstance(is_feasible, bool)
        assert isinstance(message, str)
        assert "N=1200" in message or "Pilot" in message

    def test_batch_size_logic(self):
        constraints = calculate_batch_constraints()
        # Ensure safe batch size is reasonable relative to pilot
        assert constraints["constraints"]["safe_batch_size"] > 0
        # Theoretical max should be at least the pilot size for feasibility
        if constraints["feasibility_status"] == "FEASIBLE":
            assert constraints["constraints"]["theoretical_max_batch"] >= 1200
