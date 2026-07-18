"""
Unit tests for the Power Analysis module (T045).
"""
import pytest
import math
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.power_analysis import (
    calculate_standard_error,
    calculate_mdes,
    run_power_analysis,
    validate_ground_truth_effect
)

class TestPowerAnalysis:
    """Tests for power analysis calculations."""

    def test_standard_error_independence(self):
        """Test SE calculation assuming independent observations (ICC=0)."""
        # N=100, J=10, sigma=1 -> Total=1000
        # SE = 1 / sqrt(1000) ≈ 0.0316
        se = calculate_standard_error(100, 10, 1.0, 0.0)
        expected = 1.0 / math.sqrt(1000)
        assert math.isclose(se, expected, rel_tol=1e-5)

    def test_standard_error_with_icc(self):
        """Test SE calculation with non-zero ICC (clustered data)."""
        # ICC > 0 should increase SE (reduce effective N)
        se_icc0 = calculate_standard_error(100, 10, 1.0, 0.0)
        se_icc_high = calculate_standard_error(100, 10, 1.0, 0.5)
        assert se_icc_high > se_icc0

    def test_mdes_calculation(self):
        """Test MDES formula: (Z_alpha + Z_power) * SE."""
        se = 0.01
        mdes = calculate_mdes(se, alpha=0.05, power=0.80)
        # Z_alpha=1.96, Z_power=0.84 -> Sum = 2.8
        expected = 2.8 * se
        assert math.isclose(mdes, expected, rel_tol=1e-5)

    def test_run_power_analysis_structure(self):
        """Test that run_power_analysis returns expected keys."""
        result = run_power_analysis(n_participants=200, n_vignettes=50)
        required_keys = [
            "n_participants", "n_vignettes", "total_observations",
            "standard_deviation", "alpha", "power_target",
            "intraclass_correlation", "standard_error",
            "minimum_detectable_effect_size"
        ]
        for key in required_keys:
            assert key in result

    def test_validate_ground_truth_pass(self):
        """Test validation when effect > MDES."""
        is_valid, msg = validate_ground_truth_effect(0.05, 0.1)
        assert is_valid is True
        assert "PASS" in msg or "above" in msg.lower()

    def test_validate_ground_truth_fail(self):
        """Test validation when effect < MDES."""
        is_valid, msg = validate_ground_truth_effect(0.1, 0.01)
        assert is_valid is False
        assert "FAIL" in msg or "below" in msg.lower()

    def test_mdes_magnitude_for_task_params(self):
        """
        Verify the MDES for the specific task parameters:
        N=200, J=50, sigma=1.0.
        Expected SE = 1/sqrt(10000) = 0.01
        Expected MDES = 2.8 * 0.01 = 0.028
        """
        result = run_power_analysis(n_participants=200, n_vignettes=50, sigma=1.0)
        expected_mdes = 0.028
        assert math.isclose(result["minimum_detectable_effect_size"], expected_mdes, rel_tol=1e-3)
