"""
Unit tests for sensitivity analysis logic.
"""
import pytest
import numpy as np
import os
import sys
import json
import tempfile

# Ensure project root is in path if running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_sweep_results
from src.models import SensitivitySweep


class TestSensitivitySweepLogic:
    """Tests for the run_sensitivity_sweep function."""

    def test_insufficient_data_returns_empty(self):
        """Test that N < 30 returns an empty list."""
        small_embodied = [1.0, 2.0, 3.0]
        small_static = [4.0, 5.0]
        thresholds = [0.05]

        result = run_sensitivity_sweep(small_embodied, small_static, thresholds)
        
        assert result == [], "Expected empty list for N < 30"

    def test_sufficient_data_returns_results(self):
        """Test that N >= 30 returns a list of SensitivitySweep objects."""
        # Create enough data points (N=30)
        np.random.seed(42)
        embodied = np.random.normal(10, 2, 15).tolist()
        static = np.random.normal(8, 2, 15).tolist()
        thresholds = [0.01, 0.05, 0.10]

        result = run_sensitivity_sweep(embodied, static, thresholds)
        
        assert len(result) == 3, f"Expected 3 results for 3 thresholds, got {len(result)}"
        assert all(isinstance(r, SensitivitySweep) for r in result), "All items must be SensitivitySweep instances"
        
        # Verify threshold values
        thresholds_found = [r.threshold for r in result]
        assert thresholds_found == thresholds, f"Thresholds mismatch: {thresholds_found} vs {thresholds}"

    def test_effect_size_calculation(self):
        """Verify effect sizes are calculated and non-random."""
        np.random.seed(123)
        # Distinct groups with known difference
        embodied = [10.0] * 15
        static = [5.0] * 15
        thresholds = [0.05]

        result = run_sensitivity_sweep(embodied, static, thresholds)
        
        assert len(result) == 1
        # Effect size should be positive and significant (large difference)
        assert result[0].effect_size > 0, "Effect size should be positive for distinct groups"

    def test_p_value_in_results(self):
        """Verify p-values are included in results."""
        np.random.seed(456)
        embodied = np.random.normal(10, 2, 20).tolist()
        static = np.random.normal(10, 2, 10).tolist() # Same mean, should be non-significant
        thresholds = [0.05]

        result = run_sensitivity_sweep(embodied, static, thresholds)
        
        assert len(result) == 1
        assert 0.0 <= result[0].p_value <= 1.0, "P-value must be between 0 and 1"

class TestRobustnessWarning:
    """Tests for the check_robustness_warning function."""

    def test_warning_when_effect_drops(self):
        """Test warning triggers when effect size < minimum."""
        # Create a mock result with small effect
        mock_result = SensitivitySweep(
            threshold=0.05,
            effect_size=0.1, # Below default 0.2
            p_value=0.03,
            sample_size=50
        )
        
        assert check_robustness_warning([mock_result]) is True

    def test_no_warning_when_effect_stable(self):
        """Test no warning when effect size >= minimum."""
        mock_result = SensitivitySweep(
            threshold=0.05,
            effect_size=0.5, # Above default 0.2
            p_value=0.01,
            sample_size=50
        )
        
        assert check_robustness_warning([mock_result]) is False

    def test_warning_on_any_drop(self):
        """Test warning triggers if ANY result in list is below threshold."""
        good_result = SensitivitySweep(threshold=0.01, effect_size=0.5, p_value=0.01, sample_size=50)
        bad_result = SensitivitySweep(threshold=0.05, effect_size=0.1, p_value=0.04, sample_size=50)
        
        assert check_robustness_warning([good_result, bad_result]) is True

class TestAggregateSweepResults:
    """Tests for aggregation logic."""

    def test_aggregates_empty_list(self):
        """Test aggregation of empty list returns error state."""
        result = aggregate_sweep_results([])
        
        assert result["robustness_warning"] is True
        assert "reason" in result

    def test_aggregates_valid_results(self):
        """Test aggregation of valid results."""
        results = [
            SensitivitySweep(threshold=0.01, effect_size=0.5, p_value=0.01, sample_size=50),
            SensitivitySweep(threshold=0.05, effect_size=0.4, p_value=0.04, sample_size=50)
        ]
        
        summary = aggregate_sweep_results(results)
        
        assert "sweep_data" in summary
        assert len(summary["sweep_data"]) == 2
        assert isinstance(summary["sweep_data"][0], dict)
        assert "effect_size" in summary["sweep_data"][0]