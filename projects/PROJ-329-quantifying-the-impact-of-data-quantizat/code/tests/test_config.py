"""
Tests for environment configuration and constraint calculations.
"""
import pytest
import sys
from pathlib import Path

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    get_seed,
    set_seed,
    get_resource_limits,
    calculate_batch_constraints,
    verify_pilot_feasibility,
    TOTAL_PILOT_SIGNALS,
    MAX_CPU_CORES,
    MAX_RAM_GB,
    SAFE_BATCH_SIZE,
    BIT_DEPTHS,
    SNR_BINS
)
import numpy as np

class TestConfigConstants:
    def test_max_cpu_is_two(self):
        assert MAX_CPU_CORES == 2

    def test_max_ram_is_seven_gb(self):
        assert MAX_RAM_GB == 7.0

    def test_pilot_signal_count(self):
        # 6 depths * 4 bins * 50 signals
        expected = 6 * 4 * 50
        assert TOTAL_PILOT_SIGNALS == expected

    def test_bit_depths_correct(self):
        expected = [1, 8, 10, 12, 14, 16]
        assert BIT_DEPTHS == expected

    def test_snr_bins_correct(self):
        expected = [(8, 14), (14, 20), (20, 30), (30, 50)]
        assert SNR_BINS == expected

class TestSeedManagement:
    def test_default_seed(self):
        # Should be 42 unless env var overrides
        seed = get_seed()
        assert isinstance(seed, int)

    def test_set_seed_updates_numpy(self):
        original_seed = get_seed()
        set_seed(12345)
        assert get_seed() == 12345
        
        # Verify numpy seed is set
        arr1 = np.random.rand(5)
        set_seed(12345)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_almost_equal(arr1, arr2)
        
        # Reset
        set_seed(original_seed)

class TestResourceConstraints:
    def test_batch_constraints_returns_tuple(self):
        result = calculate_batch_constraints()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)

    def test_safe_batch_size_is_positive(self):
        size = SAFE_BATCH_SIZE
        assert size > 0

    def test_resource_limits_structure(self):
        limits = get_resource_limits()
        assert "max_cpu" in limits
        assert "max_ram_gb" in limits
        assert "max_batch_size" in limits
        assert "total_signals" in limits
        assert limits["total_signals"] == TOTAL_PILOT_SIGNALS

class TestPilotFeasibility:
    def test_feasibility_check_runs(self):
        # This should not raise
        result = verify_pilot_feasibility()
        assert isinstance(result, bool)

    def test_feasibility_logic(self):
        # If constraints are too tight, it should return False
        # Since we defined SAFE_BATCH_SIZE based on constraints,
        # the check essentially verifies TOTAL_PILOT_SIGNALS <= SAFE_BATCH_SIZE
        feasible = verify_pilot_feasibility()
        if not feasible:
            # If not feasible, we expect the pilot to be too large
            assert TOTAL_PILOT_SIGNALS > SAFE_BATCH_SIZE
        else:
            assert TOTAL_PILOT_SIGNALS <= SAFE_BATCH_SIZE