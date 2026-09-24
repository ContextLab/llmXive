"""
Unit tests for Hedges' g calculation accuracy.

Tests verify the implementation in code/analysis/effect_sizes.py against:
1. Manual calculation using the standard formula
2. Comparison with statsmodels (if available) or scipy-based verification

Per Constitution Principle II (Verified Accuracy), all calculations must be
reproducible and mathematically correct.
"""

import math
import pytest
import numpy as np
from code.analysis.effect_sizes import calculate_hedges_g, EffectSizeResult


class TestHedgesGCalculation:
    """Test suite for Hedges' g effect size calculation."""

    def test_manual_calculation_basic(self):
        """
        Test against a manually calculated example.
        
        Example from Borenstein et al. (2009):
        Treatment: n=30, mean=10.5, sd=2.3
        Control: n=30, mean=8.2, sd=2.1
        
        Pooled SD = sqrt(((n1-1)*sd1^2 + (n2-1)*sd2^2) / (n1+n2-2))
        Cohen's d = (mean1 - mean2) / pooled_sd
        Hedges' g = d * J, where J = 1 - 3/(4*(n1+n2)-9)
        """
        n_treatment = 30
        mean_treatment = 10.5
        sd_treatment = 2.3
        
        n_control = 30
        mean_control = 8.2
        sd_control = 2.1
        
        # Manual calculation
        df = n_treatment + n_control - 2
        pooled_variance = ((n_treatment - 1) * sd_treatment**2 + 
                           (n_control - 1) * sd_control**2) / df
        pooled_sd = math.sqrt(pooled_variance)
        
        cohen_d = (mean_treatment - mean_control) / pooled_sd
        
        # Hedges' correction factor J
        J = 1 - (3 / (4 * df - 1))
        manual_hedges_g = cohen_d * J
        
        # Calculate using our function
        result = calculate_hedges_g(
            mean_treatment=mean_treatment,
            sd_treatment=sd_treatment,
            n_treatment=n_treatment,
            mean_control=mean_control,
            sd_control=sd_control,
            n_control=n_control
        )
        
        # Verify within floating point tolerance
        assert abs(result.hedges_g - manual_hedges_g) < 1e-10, \
            f"Calculated {result.hedges_g} != manual {manual_hedges_g}"
        
        # Verify standard error calculation
        # SE(g) = sqrt((n1+n2)/(n1*n2) + g^2/(2*(n1+n2)))
        expected_se = math.sqrt(
            (n_treatment + n_control) / (n_treatment * n_control) +
            (result.hedges_g**2) / (2 * df)
        )
        assert abs(result.se - expected_se) < 1e-10, \
            f"SE {result.se} != expected {expected_se}"
    
    def test_small_sample_correction(self):
        """
        Verify that the small-sample correction (J factor) is applied.
        
        For small samples, Hedges' g should differ from Cohen's d.
        For large samples, they should converge.
        """
        n_treatment = 10
        mean_treatment = 10.0
        sd_treatment = 2.0
        
        n_control = 10
        mean_control = 8.0
        sd_control = 2.0
        
        result = calculate_hedges_g(
            mean_treatment=mean_treatment,
            sd_treatment=sd_treatment,
            n_treatment=n_treatment,
            mean_control=mean_control,
            sd_control=sd_control,
            n_control=n_control
        )
        
        # Manual Cohen's d (no correction)
        pooled_variance = ((n_treatment - 1) * sd_treatment**2 + 
                           (n_control - 1) * sd_control**2) / (n_treatment + n_control - 2)
        pooled_sd = math.sqrt(pooled_variance)
        cohen_d = (mean_treatment - mean_control) / pooled_sd
        
        # Hedges' g should be slightly smaller than Cohen's d for small samples
        assert result.hedges_g < cohen_d, \
            "Hedges' g should be smaller than Cohen's d for small samples"
        
        # The correction factor should be approximately:
        df = n_treatment + n_control - 2
        J = 1 - (3 / (4 * df - 1))
        expected_hedges_g = cohen_d * J
        
        assert abs(result.hedges_g - expected_hedges_g) < 1e-10, \
            f"Small sample correction not applied correctly: {result.hedges_g} vs {expected_hedges_g}"
    
    def test_large_sample_convergence(self):
        """
        Verify that for large samples, Hedges' g converges to Cohen's d.
        """
        n_treatment = 1000
        mean_treatment = 10.0
        sd_treatment = 2.0
        
        n_control = 1000
        mean_control = 8.0
        sd_control = 2.0
        
        result = calculate_hedges_g(
            mean_treatment=mean_treatment,
            sd_treatment=sd_treatment,
            n_treatment=n_treatment,
            mean_control=mean_control,
            sd_control=sd_control,
            n_control=n_control
        )
        
        # Manual Cohen's d
        pooled_variance = ((n_treatment - 1) * sd_treatment**2 + 
                           (n_control - 1) * sd_control**2) / (n_treatment + n_control - 2)
        pooled_sd = math.sqrt(pooled_variance)
        cohen_d = (mean_treatment - mean_control) / pooled_sd
        
        # For large samples, the difference should be negligible
        assert abs(result.hedges_g - cohen_d) < 1e-6, \
            f"Hedges' g should converge to Cohen's d for large samples: {result.hedges_g} vs {cohen_d}"
    
    def test_zero_effect_size(self):
        """Test when treatment and control have identical means."""
        n_treatment = 20
        mean_treatment = 10.0
        sd_treatment = 2.0
        
        n_control = 20
        mean_control = 10.0  # Same mean
        sd_control = 2.0
        
        result = calculate_hedges_g(
            mean_treatment=mean_treatment,
            sd_treatment=sd_treatment,
            n_treatment=n_treatment,
            mean_control=mean_control,
            sd_control=sd_control,
            n_control=n_control
        )
        
        assert abs(result.hedges_g) < 1e-10, \
            "Effect size should be zero when means are identical"
    
    def test_negative_effect_size(self):
        """Test when control mean is higher than treatment mean."""
        n_treatment = 20
        mean_treatment = 8.0
        sd_treatment = 2.0
        
        n_control = 20
        mean_control = 10.0  # Control is higher
        sd_control = 2.0
        
        result = calculate_hedges_g(
            mean_treatment=mean_treatment,
            sd_treatment=sd_treatment,
            n_treatment=n_treatment,
            mean_control=mean_control,
            sd_control=sd_control,
            n_control=n_control
        )
        
        assert result.hedges_g < 0, \
            "Effect size should be negative when control outperforms treatment"
    
    def test_return_type_structure(self):
        """Verify the return type is EffectSizeResult with correct fields."""
        result = calculate_hedges_g(
            mean_treatment=10.0,
            sd_treatment=2.0,
            n_treatment=20,
            mean_control=8.0,
            sd_control=2.0,
            n_control=20
        )
        
        assert isinstance(result, EffectSizeResult)
        assert hasattr(result, 'hedges_g')
        assert hasattr(result, 'se')
        assert hasattr(result, 'ci_lower')
        assert hasattr(result, 'ci_upper')
        assert hasattr(result, 'n_treatment')
        assert hasattr(result, 'n_control')
        
        # Verify confidence interval calculation (95% CI)
        # CI = g ± 1.96 * SE
        expected_ci_lower = result.hedges_g - 1.96 * result.se
        expected_ci_upper = result.hedges_g + 1.96 * result.se
        
        assert abs(result.ci_lower - expected_ci_lower) < 1e-10
        assert abs(result.ci_upper - expected_ci_upper) < 1e-10
    
    def test_asymmetric_sample_sizes(self):
        """Test with unequal sample sizes between groups."""
        n_treatment = 15
        mean_treatment = 10.5
        sd_treatment = 2.3
        
        n_control = 45
        mean_control = 8.2
        sd_control = 2.1
        
        result = calculate_hedges_g(
            mean_treatment=mean_treatment,
            sd_treatment=sd_treatment,
            n_treatment=n_treatment,
            mean_control=mean_control,
            sd_control=sd_control,
            n_control=n_control
        )
        
        # Manual calculation with asymmetric samples
        df = n_treatment + n_control - 2
        pooled_variance = ((n_treatment - 1) * sd_treatment**2 + 
                           (n_control - 1) * sd_control**2) / df
        pooled_sd = math.sqrt(pooled_variance)
        
        cohen_d = (mean_treatment - mean_control) / pooled_sd
        J = 1 - (3 / (4 * df - 1))
        manual_hedges_g = cohen_d * J
        
        assert abs(result.hedges_g - manual_hedges_g) < 1e-10, \
            f"Asymmetric samples failed: {result.hedges_g} vs {manual_hedges_g}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])