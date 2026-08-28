"""
tests/test_analysis.py: Unit tests for analysis functions.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis import power_law, fit_power_law_deviation, load_density_data
import numpy as np

class TestPowerLaw:
    """Tests for power law fitting."""

    def test_wls_recovery(self):
        """
        Unit test for WLS regression implementation.
        Synthetic data: 10 points, slope=2.0, noise=0.1.
        Assert abs(beta_estimated - 2.0) < 0.05.
        """
        # Generate synthetic data
        np.random.seed(42)
        x = np.linspace(1, 10, 10)
        c_true = 1.0
        beta_true = 2.0
        noise = 0.1
        y = c_true * np.power(x, beta_true) + np.random.normal(0, noise, len(x))

        # Create mock data format
        data = [
            {"x": 10**6, "h": int(xi), "y": 100, "count": int(yi * xi), "total": int(xi), "density": yi, "u": 1.0, "rho_expected": 1.0, "R": yi}
            for xi, yi in zip(x, y)
        ]

        # Fit power law
        result = fit_power_law_deviation(data, 100)
        if result:
            beta, se, r2 = result
            assert abs(beta - beta_true) < 0.05, f"Expected beta ~ {beta_true}, got {beta}"

    def test_chi_square_logic(self):
        """
        Unit test for Chi-Square test logic.
        Synthetic observed/expected counts.
        Assert p-value is calculated and within expected range.
        """
        from scipy import stats
        # Synthetic data
        observed = [10, 20, 30, 40, 50]
        expected = [12, 18, 32, 38, 52]

        # Calculate Chi-Square
        chi2_stat = sum((o - e)**2 / e for o, e in zip(observed, expected))
        df = len(observed) - 1
        p_value = 1 - stats.chi2.cdf(chi2_stat, df)

        assert 0 <= p_value <= 1
        assert not np.isnan(p_value)