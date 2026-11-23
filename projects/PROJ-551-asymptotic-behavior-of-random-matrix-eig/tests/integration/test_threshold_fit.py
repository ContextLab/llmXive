"""
Integration test for threshold curve fitting functionality.

Tests that the curve fitting module can:
1. Load valid sweep results data
2. Fit the sigmoid model successfully
3. Produce reasonable parameter estimates
4. Write valid JSON output
"""
import os
import json
import tempfile
import shutil
import csv
import pytest
import numpy as np
from pathlib import Path

# Add code directory to path for imports
import sys
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / 'code'
sys.path.insert(0, str(code_dir))

from analysis.threshold_fit import (
    sigmoid_function,
    load_sweep_results,
    fit_critical_threshold,
    run_curve_fitting
)

class TestSigmoidFunction:
    """Unit tests for the sigmoid model function."""

    def test_sigmoid_bounds(self):
        """Test that sigmoid outputs are always in [0, 1]."""
        theta = np.linspace(0.5, 3.5, 100)
        theta_c = 1.5
        slope = 5.0
        
        result = sigmoid_function(theta, theta_c, slope)
        
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)
        assert result.shape == theta.shape

    def test_sigmoid_midpoint(self):
        """Test that sigmoid equals 0.5 at theta = theta_c."""
        theta = np.array([1.0, 1.5, 2.0])
        theta_c = 1.5
        slope = 10.0
        
        result = sigmoid_function(theta, theta_c, slope)
        
        # At theta = theta_c, sigmoid should be 0.5
        assert np.isclose(result[1], 0.5, atol=1e-10)

    def test_sigmoid_asymptotes(self):
        """Test asymptotic behavior for large positive/negative slopes."""
        theta_c = 2.0
        
        # Far below theta_c -> probability ~ 0
        theta_low = np.array([1.0])
        result_low = sigmoid_function(theta_low, theta_c, 100.0)
        assert result_low[0] < 0.01
        
        # Far above theta_c -> probability ~ 1
        theta_high = np.array([3.0])
        result_high = sigmoid_function(theta_high, theta_c, 100.0)
        assert result_high[0] > 0.99

class TestLoadSweepResults:
    """Tests for loading sweep result data."""

    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_path = tmp_path / "test_results.csv"
        
        # Write test data
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['theta', 'N', 'outlier_probability'])
            writer.writeheader()
            writer.writerow({'theta': 1.0, 'N': 500, 'outlier_probability': 0.1})
            writer.writerow({'theta': 1.5, 'N': 500, 'outlier_probability': 0.5})
            writer.writerow({'theta': 2.0, 'N': 500, 'outlier_probability': 0.9})
        
        theta, n, prob = load_sweep_results(str(csv_path))
        
        assert len(theta) == 3
        assert len(n) == 3
        assert len(prob) == 3
        assert np.allclose(theta, [1.0, 1.5, 2.0])
        assert np.allclose(prob, [0.1, 0.5, 0.9])

    def test_load_missing_file(self, tmp_path):
        """Test that loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_sweep_results(str(tmp_path / "nonexistent.csv"))

    def test_load_invalid_columns(self, tmp_path):
        """Test that loading a CSV with missing columns raises ValueError."""
        csv_path = tmp_path / "bad.csv"
        with open(csv_path, 'w') as f:
            f.write("theta,other_col\n1.0,0.5\n")
        
        with pytest.raises(ValueError):
            load_sweep_results(str(csv_path))

class TestFitCriticalThreshold:
    """Tests for the curve fitting routine."""

    def test_fit_perfect_data(self):
        """Test fitting with perfectly sigmoidal data."""
        theta_c_true = 1.8
        slope_true = 8.0
        theta = np.linspace(1.0, 2.6, 20)
        prob = sigmoid_function(theta, theta_c_true, slope_true)
        
        theta_c_fit, slope_fit, info = fit_critical_threshold(theta, prob)
        
        assert np.isclose(theta_c_fit, theta_c_true, rtol=0.01)
        assert np.isclose(slope_fit, slope_true, rtol=0.05)
        assert info['converged']
        assert info['r_squared'] > 0.99

    def test_fit_noisy_data(self):
        """Test fitting with noisy probability data."""
        theta_c_true = 1.5
        slope_true = 5.0
        theta = np.linspace(1.0, 2.0, 15)
        prob = sigmoid_function(theta, theta_c_true, slope_true)
        
        # Add small noise
        np.random.seed(42)
        prob_noisy = prob + np.random.normal(0, 0.05, size=prob.shape)
        prob_noisy = np.clip(prob_noisy, 0.0, 1.0)
        
        theta_c_fit, slope_fit, info = fit_critical_threshold(theta, prob_noisy)
        
        # Should be within reasonable tolerance
        assert abs(theta_c_fit - theta_c_true) < 0.2
        assert abs(slope_fit - slope_true) < 1.0
        assert info['converged']

    def test_fit_insufficient_data(self):
        """Test that fitting with < 2 points raises ValueError."""
        with pytest.raises(ValueError):
            fit_critical_threshold(np.array([1.0]), np.array([0.5]))

class TestRunCurveFitting:
    """Integration tests for the full curve fitting pipeline."""

    def test_full_pipeline(self, tmp_path):
        """Test the complete pipeline from CSV to JSON output."""
        # Create input CSV
        input_csv = tmp_path / "sweep_results.csv"
        with open(input_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['theta', 'N', 'outlier_probability'])
            writer.writeheader()
            # Generate data that follows sigmoid with known parameters
            theta_vals = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8]
            for t in theta_vals:
                prob = 1.0 / (1.0 + np.exp(-6.0 * (t - 1.7)))
                writer.writerow({'theta': t, 'N': 1000, 'outlier_probability': prob})
        
        output_json = tmp_path / "fit_params.json"
        
        result = run_curve_fitting(str(input_csv), str(output_json))
        
        # Verify output file exists
        assert os.path.exists(output_json)
        
        # Verify JSON structure
        with open(output_json, 'r') as f:
            loaded = json.load(f)
        
        assert 'fit_parameters' in loaded
        assert 'data_summary' in loaded
        assert 'metadata' in loaded
        
        # Verify fitted parameters are reasonable
        fit_params = loaded['fit_parameters']
        assert 1.5 < fit_params['theta_c'] < 1.9  # Should be close to 1.7
        assert 4.0 < fit_params['slope'] < 8.0   # Should be close to 6.0
        assert fit_params['r_squared'] > 0.95

    def test_with_matrix_size_filter(self, tmp_path):
        """Test filtering by matrix size."""
        input_csv = tmp_path / "sweep_results.csv"
        with open(input_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['theta', 'N', 'outlier_probability'])
            writer.writeheader()
            # Mix of N values
            for N in [500, 1000, 1500]:
                for t in [1.0, 1.5, 2.0]:
                    prob = 0.3 if t < 1.5 else 0.8
                    writer.writerow({'theta': t, 'N': N, 'outlier_probability': prob})
        
        output_json = tmp_path / "fit_params.json"
        
        # Fit only for N=1000
        result = run_curve_fitting(str(input_csv), str(output_json), matrix_size=1000)
        
        assert result['data_summary']['matrix_size_filter'] == 1000
        # Should have 3 unique theta values
        assert len(result['data_summary']['unique_thetas']) == 3

if __name__ == '__main__':
    pytest.main([__file__, '-v'])