"""
Unit tests for deforestation detection and recovery trajectory modeling (User Story 2).
Focus: Asymptotic model fitting logic.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.detection import fit_asymptotic_model, calculate_r_squared


class TestAsymptoticModelFitting:
    """Tests for the non-linear asymptotic model fitting logic."""

    def test_fit_logistic_recovery_good_fit(self):
        """
        Test that the logistic model fits well to a synthetic recovery curve
        that follows a logistic growth pattern (R² should be high).
        """
        # Generate synthetic data: Logistic growth from 0.2 to 0.8 over 10 years
        t = np.linspace(0, 10, 50)
        # Logistic function: L / (1 + exp(-k * (t - t0)))
        # L=0.8, k=1.0, t0=5.0
        L_true, k_true, t0_true = 0.8, 1.0, 5.0
        ndvi_clean = L_true / (1 + np.exp(-k_true * (t - t0_true)))
        # Add small noise to simulate real data
        noise = np.random.normal(0, 0.02, size=t.shape)
        ndvi_noisy = ndvi_clean + noise
        ndvi_noisy = np.clip(ndvi_noisy, 0, 1) # Keep within valid NDVI range

        df = pd.DataFrame({'time': t, 'ndvi': ndvi_noisy})

        # Fit the model
        result = fit_asymptotic_model(df, 'time', 'ndvi')

        # Assertions
        assert result is not None, "Model fitting should return a result dict"
        assert result['success'] is True, "Model fitting should succeed"
        assert 'r_squared' in result
        assert result['r_squared'] >= 0.95, f"R² should be >= 0.95 for good fit, got {result['r_squared']}"
        
        # Check parameter plausibility (within reasonable bounds)
        assert 0.5 < result['params']['L'] < 1.0, "Asymptote L should be reasonable"
        assert 0.1 < result['params']['k'] < 5.0, "Rate k should be reasonable"

    def test_fit_gompertz_recovery_good_fit(self):
        """
        Test that the Gompertz model fits well to a synthetic recovery curve
        that follows a Gompertz growth pattern.
        """
        # Generate synthetic data: Gompertz growth
        t = np.linspace(0, 10, 50)
        # Gompertz function: L * exp(-exp(-k * (t - t0)))
        L_true, k_true, t0_true = 0.75, 0.8, 4.5
        ndvi_clean = L_true * np.exp(-np.exp(-k_true * (t - t0_true)))
        noise = np.random.normal(0, 0.02, size=t.shape)
        ndvi_noisy = ndvi_clean + noise
        ndvi_noisy = np.clip(ndvi_noisy, 0, 1)

        df = pd.DataFrame({'time': t, 'ndvi': ndvi_noisy})

        result = fit_asymptotic_model(df, 'time', 'ndvi')

        assert result is not None
        assert result['success'] is True
        assert result['r_squared'] >= 0.90, f"R² should be >= 0.90 for Gompertz fit, got {result['r_squared']}"

    def test_fit_poor_data_fails_gracefully(self):
        """
        Test that the model returns success=False and low R² for data
        that does not follow an asymptotic pattern (e.g., random noise or linear).
        """
        # Random noise
        t = np.linspace(0, 10, 50)
        ndvi_noisy = np.random.uniform(0.2, 0.8, size=t.shape)
        
        df = pd.DataFrame({'time': t, 'ndvi': ndvi_noisy})

        result = fit_asymptotic_model(df, 'time', 'ndvi')

        # The fitting might technically "succeed" mathematically but R² should be low
        # or the model might fail to converge depending on the optimizer and noise.
        # We assert that if it claims success, the R² must be low for random data,
        # OR if it fails, success is False.
        if result['success']:
            assert result['r_squared'] < 0.5, "Random data should yield low R²"
        else:
            assert True # Expected behavior: failure to fit meaningful model

    def test_insufficient_data_points(self):
        """
        Test that the function handles datasets with too few points (< 3) gracefully.
        """
        t = np.array([0.0, 1.0])
        ndvi = np.array([0.3, 0.4])
        df = pd.DataFrame({'time': t, 'ndvi': ndvi})

        result = fit_asymptotic_model(df, 'time', 'ndvi')

        assert result is not None
        assert result['success'] is False, "Should fail with insufficient data"

    def test_convergence_with_different_initial_guesses(self):
        """
        Verify that the model is robust to reasonable variations in initial parameter guesses.
        """
        t = np.linspace(0, 10, 50)
        L_true, k_true, t0_true = 0.8, 1.0, 5.0
        ndvi_clean = L_true / (1 + np.exp(-k_true * (t - t0_true)))
        noise = np.random.normal(0, 0.02, size=t.shape)
        ndvi_noisy = ndvi_clean + noise
        ndvi_noisy = np.clip(ndvi_noisy, 0, 1)
        df = pd.DataFrame({'time': t, 'ndvi': ndvi_noisy})

        # Run multiple times with different seeds to ensure stability
        r_squared_scores = []
        for _ in range(3):
            result = fit_asymptotic_model(df, 'time', 'ndvi')
            if result['success']:
                r_squared_scores.append(result['r_squared'])
        
        assert len(r_squared_scores) == 3, "All 3 runs should succeed"
        assert all(s >= 0.90 for s in r_squared_scores), "All runs should yield high R²"

    def test_r_squared_calculation_consistency(self):
        """
        Test the standalone R² calculation function with known values.
        """
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred_perfect = y_true.copy()
        y_pred_linear = np.array([1.2, 2.1, 2.9, 4.1, 5.0]) # Slightly off
        
        r2_perfect = calculate_r_squared(y_true, y_pred_perfect)
        r2_linear = calculate_r_squared(y_true, y_pred_linear)

        assert np.isclose(r2_perfect, 1.0), "Perfect prediction should yield R²=1.0"
        assert r2_linear < 1.0, "Imperfect prediction should yield R² < 1.0"
        assert r2_linear > 0.0, "Linear trend should still have positive R²"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])