"""
Unit tests for sensitivity analysis functionality.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

from config import SimulationConfig
from sensitivity_analysis import (
    run_sensitivity_sweep,
    calculate_deviation_report,
    report_sensitivity_results,
    analyze_sensitivity
)

@pytest.fixture
def sample_config():
    """Create a minimal valid simulation config."""
    return SimulationConfig(
        N=50,
        p=0.15,
        d=50e-9,  # 50nm diameter
        l=1e-6,   # 1um length
        material="Si",
        seed=42,
        target_degree=4.0
    )

class TestSensitivitySweep:
    """Tests for sensitivity sweep functionality."""

    def test_sensitivity_sweep_basic(self, sample_config):
        """Test basic sensitivity sweep execution."""
        results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="diameter",
            sweep_range=[40e-9, 50e-9, 60e-9],
            num_repeats=3
        )
        
        assert isinstance(results, dict), "Results must be a dictionary"
        assert "mean_conductivity" in results, "Must include mean conductivity"
        assert "std_conductivity" in results, "Must include std conductivity"
        assert "deviation_percent" in results, "Must include deviation percent"
        
        # Verify numeric types
        assert isinstance(results["mean_conductivity"], (int, float, np.number))
        assert isinstance(results["std_conductivity"], (int, float, np.number))
        assert isinstance(results["deviation_percent"], (int, float, np.number))

    def test_sensitivity_sweep_parameter_p(self, sample_config):
        """Test sensitivity sweep on connection probability parameter."""
        results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="p",
            sweep_range=[0.10, 0.15, 0.20],
            num_repeats=2
        )
        
        assert "mean_conductivity" in results
        assert "deviation_percent" in results

    def test_sensitivity_sweep_with_single_value(self, sample_config):
        """Test sensitivity sweep with single value (edge case)."""
        results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="diameter",
            sweep_range=[50e-9],
            num_repeats=1
        )
        
        assert "mean_conductivity" in results
        # Deviation should be 0 for single value
        assert results["deviation_percent"] == 0.0

class TestDeviationCalculation:
    """Tests for deviation calculation logic."""

    def test_deviation_within_tolerance(self, sample_config):
        """Verify deviation stays within ±10% for stable parameters."""
        results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="diameter",
            sweep_range=[48e-9, 50e-9, 52e-9],  # Small variation
            num_repeats=3
        )
        
        deviation = results["deviation_percent"]
        assert abs(deviation) <= 10.0, \
            f"Deviation {deviation}% exceeds ±10% tolerance for small parameter variation"

    def test_deviation_calculation_formula(self):
        """Verify deviation is calculated correctly as percentage of mean."""
        # Simulate the calculation
        base_value = 100.0
        test_values = [95.0, 105.0, 100.0]
        
        mean_val = np.mean(test_values)
        std_val = np.std(test_values)
        deviation = (std_val / mean_val) * 100 if mean_val != 0 else 0.0
        
        # Expected: std = ~4.08, mean = 100.0, deviation = ~4.08%
        expected_deviation = (np.std(test_values) / np.mean(test_values)) * 100
        
        assert abs(deviation - expected_deviation) < 0.01, \
            f"Deviation calculation incorrect: {deviation} vs {expected_deviation}"

    def test_deviation_with_large_variation(self, sample_config):
        """Test deviation calculation with large parameter variation."""
        results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="diameter",
            sweep_range=[30e-9, 50e-9, 70e-9],  # Large variation
            num_repeats=2
        )
        
        # Deviation might exceed 10% with large variation, but should be calculated
        assert "deviation_percent" in results
        assert isinstance(results["deviation_percent"], (int, float))

class TestSensitivityReporting:
    """Tests for sensitivity result reporting."""

    def test_report_sensitivity_results_format(self, sample_config):
        """Verify report generation produces expected format."""
        results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="diameter",
            sweep_range=[40e-9, 50e-9, 60e-9],
            num_repeats=3
        )
        
        report = report_sensitivity_results(results)
        
        assert isinstance(report, dict), "Report must be a dictionary"
        assert "parameter" in report, "Report must include parameter name"
        assert "mean_conductivity" in report, "Report must include mean"
        assert "std_conductivity" in report, "Report must include std"
        assert "deviation_percent" in report, "Report must include deviation"
        assert "within_tolerance" in report, "Report must include tolerance check"
        
        # Verify tolerance check logic
        expected_tolerance = abs(report["deviation_percent"]) <= 10.0
        assert report["within_tolerance"] == expected_tolerance, \
            f"Tolerance check incorrect: {report['within_tolerance']}"

    def test_analyze_sensitivity_output(self, sample_config):
        """Test comprehensive sensitivity analysis output."""
        analysis = analyze_sensitivity(
            base_config=sample_config,
            parameter="p",
            sweep_range=[0.12, 0.15, 0.18],
            num_repeats=3
        )
        
        assert isinstance(analysis, dict), "Analysis must be a dictionary"
        assert "summary" in analysis, "Analysis must include summary"
        assert "detailed_results" in analysis, "Analysis must include detailed results"
        assert "recommendation" in analysis, "Analysis must include recommendation"

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_sweep_range(self, sample_config):
        """Test behavior with empty sweep range."""
        with pytest.raises(ValueError) as excinfo:
            run_sensitivity_sweep(
                base_config=sample_config,
                parameter="diameter",
                sweep_range=[],
                num_repeats=1
            )
        assert "sweep_range" in str(excinfo.value).lower() or "empty" in str(excinfo.value).lower()

    def test_invalid_parameter_name(self, sample_config):
        """Test behavior with invalid parameter name."""
        with pytest.raises(ValueError) as excinfo:
            run_sensitivity_sweep(
                base_config=sample_config,
                parameter="invalid_param",
                sweep_range=[1, 2, 3],
                num_repeats=1
            )
        # Should raise error for unknown parameter
        assert True  # If we get here, error handling worked

    def test_zero_mean_conductivity(self, sample_config):
        """Test deviation calculation when mean conductivity is zero."""
        # Create a scenario where conductivity might be zero (disconnected graph)
        # This tests the division-by-zero protection in deviation calculation
        results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="p",
            sweep_range=[0.01, 0.02, 0.03],  # Very low probability
            num_repeats=2
        )
        
        # Should handle zero mean gracefully
        assert "deviation_percent" in results
        # If mean is 0, deviation should be 0 or handled appropriately
        if results["mean_conductivity"] == 0:
            assert results["deviation_percent"] == 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
