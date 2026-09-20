"""
Unit tests for Hedges' g calculation accuracy.

This module verifies that the `calculate_hedges_g` function in
`code.analysis.effect_sizes` produces results consistent with
manual calculations and the `statsmodels` implementation.

Constitution Principle II (Verified Accuracy) and FR-004 require
that effect size calculations are mathematically correct and
reproducible.
"""

import math
import pytest
import numpy as np
from statsmodels.stats.meta_analysis import effectsize_mean
from code.analysis.effect_sizes import calculate_hedges_g, EffectSizeResult


class TestHedgesGCalculation:
    """Tests for Hedges' g calculation accuracy."""

    def test_manual_calculation_simple_case(self):
        """
        Verify Hedges' g against a known manual calculation.
        
        Data:
        - Treatment: n1=10, mean1=5.0, std1=1.5
        - Control: n2=10, mean2=4.0, std2=1.5
        
        Manual calculation steps:
        1. Pooled SD = sqrt(((n1-1)*s1^2 + (n2-1)*s2^2) / (n1+n2-2))
        2. Cohen's d = (mean1 - mean2) / Pooled SD
        3. Correction factor J = 1 - 3/(4*(n1+n2)-9)
        4. Hedges' g = d * J
        """
        n1, mean1, std1 = 10, 5.0, 1.5
        n2, mean2, std2 = 10, 4.0, 1.5
        
        # Manual calculation
        df = n1 + n2 - 2
        pooled_var = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / df
        pooled_std = math.sqrt(pooled_var)
        cohens_d = (mean1 - mean2) / pooled_std
        correction_factor = 1 - (3 / (4 * df - 1))
        expected_hedges_g = cohens_d * correction_factor
        
        # Function under test
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        # Assert
        assert isinstance(result, EffectSizeResult)
        assert result.study_id is None  # No study ID provided
        assert np.isclose(result.hedges_g, expected_hedges_g, rtol=1e-5)
        # Standard error calculation check (approximate)
        # SE = sqrt((n1+n2)/(n1*n2) + d^2/(2*(n1+n2)))
        expected_se = math.sqrt(
            (n1 + n2) / (n1 * n2) + cohens_d**2 / (2 * (n1 + n2))
        )
        assert np.isclose(result.se, expected_se, rtol=1e-3)

    def test_statsmodels_comparison(self):
        """
        Compare our implementation against statsmodels' effectsize_mean.
        
        Note: statsmodels effectsize_mean computes Cohen's d by default.
        We must apply the small-sample correction to compare with Hedges' g.
        """
        # Generate synthetic data for two groups
        np.random.seed(42)
        treatment = np.random.normal(loc=5.0, scale=1.5, size=25)
        control = np.random.normal(loc=4.0, scale=1.5, size=25)
        
        # Calculate statistics
        n1, mean1, std1 = len(treatment), np.mean(treatment), np.std(treatment, ddof=1)
        n2, mean2, std2 = len(control), np.mean(control), np.std(control, ddof=1)
        
        # Our implementation
        our_result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        # Statsmodels implementation (Cohen's d)
        # statsmodels uses unbiased estimator for pooled variance
        stats_d, _ = effectsize_mean(
            mean1, mean2, std1**2, std2**2, n1, n2, 
            method='cohen'
        )
        
        # Convert Cohen's d to Hedges' g using the correction factor
        df = n1 + n2 - 2
        correction = 1 - (3 / (4 * df - 1))
        expected_hedges_g = stats_d * correction
        
        # Assert
        assert np.isclose(our_result.hedges_g, expected_hedges_g, rtol=1e-5)

    def test_zero_effect(self):
        """Test that identical means result in Hedges' g = 0."""
        n1, mean1, std1 = 15, 5.0, 1.0
        n2, mean2, std2 = 15, 5.0, 1.0
        
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        assert np.isclose(result.hedges_g, 0.0, atol=1e-10)
        assert result.hedges_g == 0.0

    def test_negative_effect(self):
        """Test that treatment mean < control mean results in negative Hedges' g."""
        n1, mean1, std1 = 20, 4.0, 1.2
        n2, mean2, std2 = 20, 5.5, 1.2
        
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        assert result.hedges_g < 0
        # Verify magnitude is reasonable
        assert abs(result.hedges_g) < 10  # Sanity check

    def test_small_sample_correction(self):
        """
        Verify that the small-sample correction is applied correctly.
        
        For very small samples, the difference between Cohen's d and Hedges' g
        should be noticeable.
        """
        n1, mean1, std1 = 5, 5.0, 1.0
        n2, mean2, std2 = 5, 4.0, 1.0
        
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        # Calculate Cohen's d manually
        df = n1 + n2 - 2
        pooled_var = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / df
        pooled_std = math.sqrt(pooled_var)
        cohens_d = (mean1 - mean2) / pooled_std
        
        # The correction factor for small samples
        correction = 1 - (3 / (4 * df - 1))
        
        # Hedges' g should be smaller in magnitude than Cohen's d
        assert abs(result.hedges_g) < abs(cohens_d)
        assert np.isclose(result.hedges_g, cohens_d * correction, rtol=1e-5)

    def test_large_sample_convergence(self):
        """
        Verify that for large samples, Hedges' g converges to Cohen's d.
        """
        n1, mean1, std1 = 1000, 5.0, 1.5
        n2, mean2, std2 = 1000, 4.0, 1.5
        
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        # Calculate Cohen's d
        df = n1 + n2 - 2
        pooled_var = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / df
        pooled_std = math.sqrt(pooled_var)
        cohens_d = (mean1 - mean2) / pooled_std
        
        # For large samples, the correction factor approaches 1
        correction = 1 - (3 / (4 * df - 1))
        expected_hedges_g = cohens_d * correction
        
        assert np.isclose(result.hedges_g, expected_hedges_g, rtol=1e-5)
        # The difference should be very small
        assert abs(result.hedges_g - cohens_d) < 0.01

    def test_unequal_sample_sizes(self):
        """Test calculation with unequal sample sizes."""
        n1, mean1, std1 = 15, 5.0, 1.2
        n2, mean2, std2 = 25, 4.0, 1.2
        
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        # Manual calculation
        df = n1 + n2 - 2
        pooled_var = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / df
        pooled_std = math.sqrt(pooled_var)
        cohens_d = (mean1 - mean2) / pooled_std
        correction = 1 - (3 / (4 * df - 1))
        expected = cohens_d * correction
        
        assert np.isclose(result.hedges_g, expected, rtol=1e-5)

    def test_unequal_variances(self):
        """Test calculation with unequal variances (pooled variance used)."""
        n1, mean1, std1 = 20, 5.0, 1.0
        n2, mean2, std2 = 20, 4.0, 2.0
        
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        # Manual calculation using pooled variance
        df = n1 + n2 - 2
        pooled_var = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / df
        pooled_std = math.sqrt(pooled_var)
        cohens_d = (mean1 - mean2) / pooled_std
        correction = 1 - (3 / (4 * df - 1))
        expected = cohens_d * correction
        
        assert np.isclose(result.hedges_g, expected, rtol=1e-5)

    def test_result_structure(self):
        """Verify that the returned EffectSizeResult has the correct structure."""
        n1, mean1, std1 = 10, 5.0, 1.0
        n2, mean2, std2 = 10, 4.0, 1.0
        
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2)
        
        assert hasattr(result, 'hedges_g')
        assert hasattr(result, 'se')
        assert hasattr(result, 'ci_lower')
        assert hasattr(result, 'ci_upper')
        assert hasattr(result, 'study_id')
        
        # Check that CI is calculated (approx 95% CI: g ± 1.96 * SE)
        expected_lower = result.hedges_g - 1.96 * result.se
        expected_upper = result.hedges_g + 1.96 * result.se
        
        assert np.isclose(result.ci_lower, expected_lower, rtol=1e-3)
        assert np.isclose(result.ci_upper, expected_upper, rtol=1e-3)

    def test_single_study_id(self):
        """Test that study_id is propagated correctly."""
        study_id = "NCT12345678"
        n1, mean1, std1 = 10, 5.0, 1.0
        n2, mean2, std2 = 10, 4.0, 1.0
        
        result = calculate_hedges_g(n1, mean1, std1, n2, mean2, std2, study_id=study_id)
        
        assert result.study_id == study_id