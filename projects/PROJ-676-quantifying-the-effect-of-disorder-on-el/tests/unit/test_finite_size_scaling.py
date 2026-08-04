"""
Unit tests for finite-size scaling fit logic.
"""
import json
import numpy as np
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.finite_size_scaling import (
    saturation_model, 
    fit_scaling_curve, 
    run_scaling_analysis
)


class TestSaturationModel:
    """Tests for the saturation model function."""

    def test_model_basic(self):
        """Test basic model behavior."""
        L = np.array([100, 200, 400, 800])
        PR_inf = 100.0
        xi = 200.0
        
        result = saturation_model(L, PR_inf, xi)
        
        # At L=0, PR should be 0
        assert saturation_model(np.array([0]), PR_inf, xi)[0] == 0.0
        
        # As L -> infinity, PR -> PR_inf
        assert result[-1] < PR_inf
        assert all(result > 0)

    def test_model_monotonic(self):
        """Test that model is monotonically increasing."""
        L = np.linspace(10, 1000, 100)
        PR_inf = 50.0
        xi = 100.0
        
        result = saturation_model(L, PR_inf, xi)
        
        # Check monotonicity
        assert np.all(np.diff(result) >= 0)


class TestFitScalingCurve:
    """Tests for the curve fitting function."""

    def test_perfect_fit(self):
        """Test fitting with perfect data."""
        L_true = np.array([100, 200, 400, 800, 1600])
        PR_inf_true = 100.0
        xi_true = 200.0
        
        # Generate data with the model
        PR_true = saturation_model(L_true, PR_inf_true, xi_true)
        
        # Add small noise
        PR_noisy = PR_true + np.random.normal(0, 0.1, size=L_true.shape)
        
        result = fit_scaling_curve(L_true, PR_noisy)
        
        assert result is not None
        PR_inf_fit, xi_fit, xi_unc, r2 = result
        
        assert r2 >= 0.95
        assert abs(PR_inf_fit - PR_inf_true) / PR_inf_true < 0.1
        assert abs(xi_fit - xi_true) / xi_true < 0.1

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        L = np.array([100])
        PR = np.array([10.0])
        
        result = fit_scaling_curve(L, PR)
        assert result is None

    def test_non_convergence(self):
        """Test with data that doesn't fit the model."""
        # Linear data instead of saturation
        L = np.array([100, 200, 400, 800])
        PR = np.array([10, 20, 30, 40])
        
        # This might still fit, but with low R^2
        result = fit_scaling_curve(L, PR)
        # We don't assert None because it might find a poor fit
        # The important thing is it doesn't crash

    def test_negative_xi_rejected(self):
        """Test that negative xi is rejected."""
        # Force a situation where fit might try negative xi
        L = np.array([100, 200, 400])
        PR = np.array([100, 100, 100])  # Flat data
        
        result = fit_scaling_curve(L, PR)
        
        if result is not None:
            PR_inf, xi, xi_unc, r2 = result
            assert xi > 0


class TestRunScalingAnalysis:
    """Tests for the full analysis pipeline."""

    def test_end_to_end(self, tmp_path):
        """Test the full analysis pipeline with mock data."""
        # Create mock input data
        mock_data = []
        for W in [1.0, 2.0]:
            for L in [100, 200, 400, 800]:
                # Generate PR values that follow the model
                PR_inf = 100.0
                xi = 200.0
                PR = saturation_model(np.array([L]), PR_inf, xi)[0]
                # Add some noise
                PR += np.random.normal(0, 0.5)
                
                mock_data.append({
                    "W": W,
                    "L": L,
                    "realization_index": 0,
                    "energy": 0.0,
                    "pr": PR
                })
        
        input_file = tmp_path / "pr_raw_multiL.json"
        with open(input_file, 'w') as f:
            json.dump(mock_data, f)
        
        # Temporarily override paths
        import code.finite_size_scaling as fs
        original_input = fs.InputPath
        fs.InputPath = input_file
        
        try:
            results = run_scaling_analysis()
            assert len(results) == 2  # Two W values
            
            for result in results:
                assert "disorder_width" in result
                assert "xi" in result
                assert "uncertainty" in result
                assert result["xi"] > 0
        finally:
            fs.InputPath = original_input