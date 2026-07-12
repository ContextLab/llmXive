"""
Unit tests for Hellinger distance calculation and bias metrics.
Tests against known analytical distributions and numerical edge cases.
"""
import pytest
import numpy as np
from scipy.stats import norm
import sys
from pathlib import Path

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.metrics import hellinger_distance, calculate_mass_bias

class TestHellingerDistance:
    """Tests for the Hellinger distance metric implementation."""

    def test_identical_distributions(self):
        """Hellinger distance between identical distributions should be 0."""
        # Two identical normal distributions
        mean, std = 0.0, 1.0
        x = np.linspace(-10, 10, 10000)
        p = norm.pdf(x, mean, std)
        q = norm.pdf(x, mean, std)

        distance = hellinger_distance(p, q)
        assert np.isclose(distance, 0.0, atol=1e-6), \
            f"Expected 0.0, got {distance}"

    def test_disjoint_distributions(self):
        """Hellinger distance between well-separated distributions approaches 1."""
        # Two normal distributions with means far apart relative to std
        p = norm.pdf(np.linspace(-10, 10, 10000), -5, 0.5)
        q = norm.pdf(np.linspace(-10, 10, 10000), 5, 0.5)

        distance = hellinger_distance(p, q)
        # Should be close to 1 (max distance)
        assert distance > 0.95, f"Expected > 0.95, got {distance}"
        assert distance <= 1.0, f"Distance cannot exceed 1.0, got {distance}"

    def test_analytical_normal_hellinger(self):
        """
        Test against analytical formula for Hellinger distance between two normals.
        H^2 = 1 - sqrt(2*sigma1*sigma2 / (sigma1^2 + sigma2^2)) * exp(-(mu1-mu2)^2 / (4*(sigma1^2+sigma2^2)))
        """
        mu1, sigma1 = 0.0, 1.0
        mu2, sigma2 = 0.0, 2.0

        # Analytical calculation
        term1 = np.sqrt(2 * sigma1 * sigma2 / (sigma1**2 + sigma2**2))
        term2 = np.exp(-(mu1 - mu2)**2 / (4 * (sigma1**2 + sigma2**2)))
        analytical_h_sq = 1 - term1 * term2
        analytical_h = np.sqrt(analytical_h_sq)

        # Numerical calculation
        x = np.linspace(-20, 20, 100000)
        p = norm.pdf(x, mu1, sigma1)
        q = norm.pdf(x, mu2, sigma2)
        numerical_h = hellinger_distance(p, q)

        assert np.isclose(numerical_h, analytical_h, atol=1e-4), \
            f"Numerical {numerical_h} != Analytical {analytical_h}"

    def test_symmetry(self):
        """Hellinger distance should be symmetric: H(P, Q) == H(Q, P)."""
        x = np.linspace(-10, 10, 5000)
        p = norm.pdf(x, 0, 1)
        q = norm.pdf(x, 2, 0.5)

        h_pq = hellinger_distance(p, q)
        h_qp = hellinger_distance(q, p)

        assert np.isclose(h_pq, h_qp, atol=1e-10), \
            f"Not symmetric: H(P,Q)={h_pq}, H(Q,P)={h_qp}"

    def test_invalid_inputs(self):
        """Test handling of invalid inputs (negative probabilities, mismatched lengths)."""
        x = np.linspace(-10, 10, 100)
        p = norm.pdf(x, 0, 1)
        q = norm.pdf(x, 0, 1)

        # Mismatched lengths
        with pytest.raises(ValueError):
            hellinger_distance(p, q[:50])

        # Negative values (not valid probability densities)
        p_neg = p.copy()
        p_neg[0] = -0.1
        with pytest.raises(ValueError):
            hellinger_distance(p_neg, q)

class TestMassBias:
    """Tests for the mass bias calculation logic."""

    def test_zero_bias(self):
        """Bias should be 0 when estimated equals true value."""
        estimated = 30.0
        true_value = 30.0
        uncertainty = 1.0

        bias = calculate_mass_bias(estimated, true_value, uncertainty)
        assert np.isclose(bias, 0.0, atol=1e-9), f"Expected 0.0, got {bias}"

    def test_positive_bias(self):
        """Bias should be positive when estimated > true."""
        estimated = 35.0
        true_value = 30.0
        uncertainty = 1.0

        bias = calculate_mass_bias(estimated, true_value, uncertainty)
        # (35-30)/1 = 5.0 sigma
        assert np.isclose(bias, 5.0, atol=1e-9), f"Expected 5.0, got {bias}"

    def test_negative_bias(self):
        """Bias should be negative when estimated < true."""
        estimated = 25.0
        true_value = 30.0
        uncertainty = 1.0

        bias = calculate_mass_bias(estimated, true_value, uncertainty)
        # (25-30)/1 = -5.0 sigma
        assert np.isclose(bias, -5.0, atol=1e-9), f"Expected -5.0, got {bias}"

    def test_bias_within_uncertainty(self):
        """Bias should be < 1.0 when difference is within uncertainty."""
        estimated = 30.5
        true_value = 30.0
        uncertainty = 1.0

        bias = calculate_mass_bias(estimated, true_value, uncertainty)
        assert abs(bias) < 1.0, f"Expected |bias| < 1.0, got {bias}"

    def test_bias_exceeds_uncertainty(self):
        """Bias should be > 1.0 when difference exceeds uncertainty."""
        estimated = 32.0
        true_value = 30.0
        uncertainty = 1.0

        bias = calculate_mass_bias(estimated, true_value, uncertainty)
        assert bias > 1.0, f"Expected bias > 1.0, got {bias}"

    def test_zero_uncertainty_raises(self):
        """Should raise ValueError if uncertainty is zero."""
        with pytest.raises(ValueError):
            calculate_mass_bias(30.0, 30.0, 0.0)

    def test_negative_uncertainty_raises(self):
        """Should raise ValueError if uncertainty is negative."""
        with pytest.raises(ValueError):
            calculate_mass_bias(30.0, 30.0, -1.0)

    def test_catalog_90_ci_scaling(self):
        """
        Test bias calculation logic against catalog 90% CI scaling.
        
        Per FR-006 and Assumptions:
        - Catalog uncertainties are typically 1-sigma (68% CI).
        - We must scale to 90% CI for comparison.
        - Standard normality assumption: 90% CI width = 1.645 * sigma.
        - Bias is calculated as (estimated - true) / uncertainty.
        - When comparing against 90% CI, the threshold is 1.0 (bias > 1.0 means
          the difference exceeds the 90% CI).
        
        This test verifies that when we scale the uncertainty by 1.645,
        the calculated bias correctly reflects the relationship to the 90% CI.
        """
        # Simulate a catalog-reported 1-sigma uncertainty
        catalog_sigma = 1.0
        
        # True value and estimated value
        true_value = 30.0
        estimated = 30.0 + 1.645  # Difference equals 1.645 * sigma (90% CI boundary)
        
        # Calculate 90% CI uncertainty (1.645 * sigma)
        uncertainty_90ci = catalog_sigma * 1.645
        
        # Calculate bias using 90% CI uncertainty
        bias = calculate_mass_bias(estimated, true_value, uncertainty_90ci)
        
        # The difference (1.645) divided by 90% CI uncertainty (1.645) should be exactly 1.0
        assert np.isclose(bias, 1.0, atol=1e-9), \
            f"Expected bias of 1.0 at 90% CI boundary, got {bias}"
        
        # Test with difference exceeding 90% CI
        estimated_exceeds = 30.0 + 2.0 * catalog_sigma * 1.645
        bias_exceeds = calculate_mass_bias(estimated_exceeds, true_value, uncertainty_90ci)
        assert bias_exceeds > 1.0, \
            f"Expected bias > 1.0 when difference exceeds 90% CI, got {bias_exceeds}"
        
        # Test with difference within 90% CI
        estimated_within = 30.0 + 0.5 * catalog_sigma * 1.645
        bias_within = calculate_mass_bias(estimated_within, true_value, uncertainty_90ci)
        assert abs(bias_within) < 1.0, \
            f"Expected |bias| < 1.0 when difference within 90% CI, got {bias_within}"

    def test_catalog_90_ci_scaling_edge_cases(self):
        """
        Test edge cases for catalog 90% CI scaling.
        
        Verifies that the scaling logic handles:
        1. Very small uncertainties
        2. Very large uncertainties
        3. Zero difference between estimated and true
        """
        catalog_sigma = 0.001  # Very small uncertainty
        true_value = 30.0
        
        # Difference equals 90% CI boundary
        estimated = true_value + 1.645 * catalog_sigma
        uncertainty_90ci = catalog_sigma * 1.645
        
        bias = calculate_mass_bias(estimated, true_value, uncertainty_90ci)
        assert np.isclose(bias, 1.0, atol=1e-9), \
            f"Expected bias of 1.0 for small uncertainty, got {bias}"
        
        # Very large uncertainty
        catalog_sigma_large = 100.0
        estimated_large = true_value + 1.645 * catalog_sigma_large
        uncertainty_90ci_large = catalog_sigma_large * 1.645
        
        bias_large = calculate_mass_bias(estimated_large, true_value, uncertainty_90ci_large)
        assert np.isclose(bias_large, 1.0, atol=1e-9), \
            f"Expected bias of 1.0 for large uncertainty, got {bias_large}"
        
        # Zero difference
        bias_zero = calculate_mass_bias(true_value, true_value, uncertainty_90ci)
        assert np.isclose(bias_zero, 0.0, atol=1e-9), \
            f"Expected bias of 0.0 for zero difference, got {bias_zero}"