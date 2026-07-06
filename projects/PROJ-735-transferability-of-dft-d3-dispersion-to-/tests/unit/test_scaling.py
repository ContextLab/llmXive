"""
Unit tests for linear scaling optimization in derive_scaling.py.

Tests verify that the scaling factor optimization correctly minimizes MAE
and that the optimization logic handles edge cases appropriately.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.derive_scaling import optimize_scaling_factor, compute_scaled_metrics
from code.utils import calculate_metrics


class TestOptimizeScalingFactor:
    """Tests for the optimize_scaling_factor function."""

    def test_optimization_reduces_mae(self):
        """Test that optimization finds a scaling factor that reduces MAE compared to s=1.0."""
        # Create synthetic data where s != 1.0 is optimal
        # E_base = reference - 10 (systematic underestimation without scaling)
        # E_D3 = 20 (positive dispersion contribution)
        # Reference = E_base + 1.5 * E_D3 (true scaling factor is 1.5)
        n = 50
        rng = np.random.default_rng(42)
        
        reference_energies = rng.uniform(-50, -20, n)
        e_base = reference_energies - 10 + rng.normal(0, 0.5, n)  # Systematic offset
        e_d3 = rng.uniform(15, 25, n)
        
        df = pd.DataFrame({
            'reference_energy': reference_energies,
            'dft_total_energy': e_base,
            'd3_dispersion_energy': e_d3
        })
        
        # Find optimal scaling factor
        s_opt, mae_opt = optimize_scaling_factor(df)
        
        # Compare with s=1.0 (no scaling)
        _, mae_unscaled = compute_scaled_metrics(df, s=1.0)
        
        # Optimal MAE should be lower than unscaled MAE
        assert mae_opt < mae_unscaled, f"Optimization failed: MAE {mae_opt:.4f} >= unscaled MAE {mae_unscaled:.4f}"
        assert s_opt > 0, "Optimal scaling factor must be positive"

    def test_optimization_with_perfect_data(self):
        """Test optimization when s=1.0 is already optimal."""
        n = 30
        rng = np.random.default_rng(123)
        
        reference_energies = rng.uniform(-60, -30, n)
        # When s=1.0 is optimal, E_DFT + 1.0 * E_D3 should match reference
        e_d3 = rng.uniform(10, 20, n)
        e_base = reference_energies - e_d3 + rng.normal(0, 0.1, n)  # Small noise
        
        df = pd.DataFrame({
            'reference_energy': reference_energies,
            'dft_total_energy': e_base,
            'd3_dispersion_energy': e_d3
        })
        
        s_opt, mae_opt = optimize_scaling_factor(df)
        
        # Optimal s should be close to 1.0
        assert abs(s_opt - 1.0) < 0.2, f"Expected s≈1.0, got {s_opt:.4f}"

    def test_optimization_bounds(self):
        """Test that optimization respects bounds (s > 0)."""
        n = 20
        rng = np.random.default_rng(456)
        
        reference_energies = rng.uniform(-50, -20, n)
        e_d3 = rng.uniform(15, 25, n)
        e_base = reference_energies + e_d3 + rng.normal(0, 0.5, n)  # Negative correlation
        
        df = pd.DataFrame({
            'reference_energy': reference_energies,
            'dft_total_energy': e_base,
            'd3_dispersion_energy': e_d3
        })
        
        s_opt, mae_opt = optimize_scaling_factor(df)
        
        # Should find a negative scaling factor (or close to zero)
        # But the function should enforce s > 0
        assert s_opt > 0, f"Scaling factor must be positive, got {s_opt}"
        assert s_opt < 10, f"Scaling factor should be bounded, got {s_opt}"

    def test_single_point_data(self):
        """Test optimization with minimal dataset (single point)."""
        df = pd.DataFrame({
            'reference_energy': [-40.0],
            'dft_total_energy': [-45.0],
            'd3_dispersion_energy': [10.0]
        })
        
        s_opt, mae_opt = optimize_scaling_factor(df)
        
        # With one point: -45 + s*10 = -40 => s = 0.5
        assert abs(s_opt - 0.5) < 0.01, f"Expected s≈0.5, got {s_opt:.4f}"
        assert mae_opt == 0.0, "With one point and optimal s, MAE should be 0"

    def test_large_dataset(self):
        """Test optimization performance with larger dataset."""
        n = 200
        rng = np.random.default_rng(789)
        
        reference_energies = rng.uniform(-80, -20, n)
        e_d3 = rng.uniform(10, 30, n)
        true_s = 1.3
        e_base = reference_energies - true_s * e_d3 + rng.normal(0, 1.0, n)
        
        df = pd.DataFrame({
            'reference_energy': reference_energies,
            'dft_total_energy': e_base,
            'd3_dispersion_energy': e_d3
        })
        
        s_opt, mae_opt = optimize_scaling_factor(df)
        
        # Optimal s should be close to true_s
        assert abs(s_opt - true_s) < 0.15, f"Expected s≈{true_s}, got {s_opt:.4f}"


class TestComputeScaledMetrics:
    """Tests for the compute_scaled_metrics function."""

    def test_correct_energy_calculation(self):
        """Test that scaled energies are calculated correctly."""
        df = pd.DataFrame({
            'reference_energy': [-40.0, -50.0],
            'dft_total_energy': [-45.0, -55.0],
            'd3_dispersion_energy': [10.0, 15.0]
        })
        
        s = 2.0
        _, mae, rmse, mse, signed_errors = compute_scaled_metrics(df, s=s)
        
        # Expected: E_corrected = E_base + s * E_D3
        # Point 1: -45 + 2*10 = -25, error = -25 - (-40) = 15
        # Point 2: -55 + 2*15 = -25, error = -25 - (-50) = 25
        expected_errors = [15.0, 25.0]
        expected_mae = np.mean(np.abs(expected_errors))
        expected_rmse = np.sqrt(np.mean(np.square(expected_errors)))
        
        assert np.isclose(mae, expected_mae), f"MAE mismatch: {mae} vs {expected_mae}"
        assert np.isclose(rmse, expected_rmse), f"RMSE mismatch: {rmse} vs {expected_rmse}"

    def test_zero_scaling(self):
        """Test with s=0 (no dispersion correction)."""
        df = pd.DataFrame({
            'reference_energy': [-40.0],
            'dft_total_energy': [-45.0],
            'd3_dispersion_energy': [10.0]
        })
        
        _, mae, _, _, _ = compute_scaled_metrics(df, s=0.0)
        
        # With s=0: error = -45 - (-40) = -5, MAE = 5
        assert np.isclose(mae, 5.0), f"Expected MAE=5.0, got {mae}"

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['reference_energy', 'dft_total_energy', 'd3_dispersion_energy'])
        
        with pytest.raises((ValueError, IndexError)):
            compute_scaled_metrics(df, s=1.0)

    def test_missing_columns(self):
        """Test handling of dataframe with missing required columns."""
        df = pd.DataFrame({
            'reference_energy': [-40.0],
            'dft_total_energy': [-45.0]
            # Missing 'd3_dispersion_energy'
        })
        
        with pytest.raises(KeyError):
            compute_scaled_metrics(df, s=1.0)


class TestIntegrationWithUtils:
    """Integration tests with utils.py functions."""

    def test_metrics_consistency(self):
        """Test that compute_scaled_metrics agrees with calculate_metrics."""
        df = pd.DataFrame({
            'reference_energy': [-40.0, -50.0, -45.0],
            'dft_total_energy': [-45.0, -55.0, -50.0],
            'd3_dispersion_energy': [10.0, 15.0, 12.0]
        })
        
        s = 1.5
        _, mae_scaled, rmse_scaled, mse_scaled, signed_errors = compute_scaled_metrics(df, s=s)
        
        # Recalculate using utils
        expected_mae = calculate_metrics(signed_errors, 'mae')
        expected_rmse = calculate_metrics(signed_errors, 'rmse')
        expected_mse = calculate_metrics(signed_errors, 'mse')
        
        assert np.isclose(mae_scaled, expected_mae), "MAE mismatch with utils"
        assert np.isclose(rmse_scaled, expected_rmse), "RMSE mismatch with utils"
        assert np.isclose(mse_scaled, expected_mse), "MSE mismatch with utils"

    def test_bootstrap_compatibility(self):
        """Test that output is compatible with bootstrap resampling."""
        from code.utils import bootstrap_resample
        
        df = pd.DataFrame({
            'reference_energy': np.random.uniform(-50, -20, 50),
            'dft_total_energy': np.random.uniform(-55, -25, 50),
            'd3_dispersion_energy': np.random.uniform(10, 20, 50)
        })
        
        s = 1.2
        _, mae, _, _, signed_errors = compute_scaled_metrics(df, s=s)
        
        # Verify we can resample the signed errors
        resampled = bootstrap_resample(signed_errors, n_bootstrap=10)
        assert len(resampled) == 10, "Bootstrap should return 10 resamples"
        assert all(len(r) == len(signed_errors) for r in resampled), "Each resample should have same length"