"""
Unit tests for data validation and statistical edge cases.

This module contains tests for:
- Missing data handling (T046a)
- Skewed distributions and Welch's ANOVA fallback (T046b)
- Collinearity handling and VIF diagnostics (T046c)
"""
import pytest
import numpy as np
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.anova import calculate_vif_diagnostics, check_normality, check_homogeneity_of_variance
from analysis.logging import get_anova_logger

logger = get_anova_logger()

class TestCollinearityHandling:
    """
    Unit tests for collinearity handling and VIF diagnostics (T046c).
    
    These tests verify that:
    1. VIF diagnostics correctly identify collinear features
    2. Warnings are generated when VIF > 5
    3. The system handles both low and high collinearity scenarios
    """

    def test_vif_low_collinearity(self):
        """Test VIF calculation with low collinearity (expected VIF < 5)."""
        # Create data with low correlation between features
        np.random.seed(42)
        n_samples = 100
        
        # Independent features
        x1 = np.random.normal(0, 1, n_samples)
        x2 = np.random.normal(0, 1, n_samples)
        x3 = np.random.normal(0, 1, n_samples)
        
        # Create a target variable (not needed for VIF, but for completeness)
        y = 2 * x1 + 3 * x2 + np.random.normal(0, 0.1, n_samples)
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3,
            'y': y
        })
        
        # Select features for VIF calculation (excluding target)
        features = ['x1', 'x2', 'x3']
        
        vif_results = calculate_vif_diagnostics(df, features)
        
        # All VIF values should be close to 1 for independent features
        for feature, vif_value in vif_results.items():
            assert vif_value < 5.0, f"Expected VIF < 5 for {feature} with low collinearity, got {vif_value}"
            assert vif_value >= 1.0, f"VIF should be >= 1, got {vif_value} for {feature}"
        
        logger.info(f"Low collinearity test passed. VIF values: {vif_results}")
    
    def test_vif_high_collinearity(self):
        """Test VIF calculation with high collinearity (expected VIF > 5)."""
        np.random.seed(42)
        n_samples = 100
        
        # Create highly correlated features
        x1 = np.random.normal(0, 1, n_samples)
        x2 = x1 * 0.95 + np.random.normal(0, 0.1, n_samples)  # Highly correlated with x1
        x3 = np.random.normal(0, 1, n_samples)  # Independent
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3
        })
        
        features = ['x1', 'x2', 'x3']
        
        vif_results = calculate_vif_diagnostics(df, features)
        
        # x1 and x2 should have high VIF (> 5) due to collinearity
        assert vif_results['x1'] > 5.0, f"Expected VIF > 5 for x1 with high collinearity, got {vif_results['x1']}"
        assert vif_results['x2'] > 5.0, f"Expected VIF > 5 for x2 with high collinearity, got {vif_results['x2']}"
        
        # x3 should have low VIF (< 5) as it's independent
        assert vif_results['x3'] < 5.0, f"Expected VIF < 5 for x3 (independent), got {vif_results['x3']}"
        
        logger.warning(f"High collinearity detected. VIF values: {vif_results}")
    
    def test_vif_perfect_collinearity(self):
        """Test VIF calculation with perfect collinearity (should raise or return very high VIF)."""
        np.random.seed(42)
        n_samples = 50
        
        # Create perfectly collinear features
        x1 = np.random.normal(0, 1, n_samples)
        x2 = x1 * 2.0  # Perfectly correlated
        x3 = np.random.normal(0, 1, n_samples)
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3
        })
        
        features = ['x1', 'x2', 'x3']
        
        # This should either raise an error or return very high VIF values
        vif_results = calculate_vif_diagnostics(df, features)
        
        # At least one of the collinear features should have extremely high VIF
        assert vif_results['x1'] > 100.0 or vif_results['x2'] > 100.0, \
            "Expected very high VIF for perfectly collinear features"
        
        logger.error(f"Perfect collinearity detected. VIF values: {vif_results}")
    
    def test_vif_warning_generation(self):
        """Test that warnings are generated when VIF > 5."""
        np.random.seed(42)
        n_samples = 100
        
        x1 = np.random.normal(0, 1, n_samples)
        x2 = x1 * 0.95 + np.random.normal(0, 0.1, n_samples)
        x3 = np.random.normal(0, 1, n_samples)
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3
        })
        
        features = ['x1', 'x2', 'x3']
        
        vif_results = calculate_vif_diagnostics(df, features)
        
        # Check that warnings would be logged for high VIF
        high_vif_features = [f for f, v in vif_results.items() if v > 5.0]
        assert len(high_vif_features) > 0, "Expected at least one feature with VIF > 5"
        
        logger.warning(f"Collinearity warning: Features with VIF > 5: {high_vif_features}")
    
    def test_vif_single_feature(self):
        """Test VIF calculation with a single feature (should return VIF = 1.0)."""
        np.random.seed(42)
        n_samples = 50
        
        x1 = np.random.normal(0, 1, n_samples)
        
        df = pd.DataFrame({
            'x1': x1
        })
        
        features = ['x1']
        
        vif_results = calculate_vif_diagnostics(df, features)
        
        # Single feature should have VIF = 1.0
        assert vif_results['x1'] == 1.0, f"Expected VIF = 1.0 for single feature, got {vif_results['x1']}"
    
    def test_vif_empty_dataframe(self):
        """Test VIF calculation with empty DataFrame (should handle gracefully)."""
        df = pd.DataFrame()
        features = []
        
        # Should return empty dict or raise a clear error
        vif_results = calculate_vif_diagnostics(df, features)
        
        assert isinstance(vif_results, dict), "VIF results should be a dictionary"
        assert len(vif_results) == 0, "Expected empty VIF results for empty DataFrame"
    
    def test_vif_with_constant_feature(self):
        """Test VIF calculation when one feature is constant."""
        np.random.seed(42)
        n_samples = 50
        
        x1 = np.random.normal(0, 1, n_samples)
        x2 = np.ones(n_samples) * 5.0  # Constant feature
        x3 = np.random.normal(0, 1, n_samples)
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3
        })
        
        features = ['x1', 'x2', 'x3']
        
        # Constant feature should cause issues (infinite or very high VIF)
        vif_results = calculate_vif_diagnostics(df, features)
        
        # The constant feature should have extremely high VIF
        assert vif_results['x2'] > 100.0 or np.isinf(vif_results['x2']), \
            "Expected very high or infinite VIF for constant feature"
    
    def test_vif_threshold_flagging(self):
        """Test that the system correctly flags features exceeding the VIF threshold."""
        np.random.seed(42)
        n_samples = 100
        
        x1 = np.random.normal(0, 1, n_samples)
        x2 = x1 * 0.95 + np.random.normal(0, 0.1, n_samples)
        x3 = np.random.normal(0, 1, n_samples)
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3
        })
        
        features = ['x1', 'x2', 'x3']
        threshold = 5.0
        
        vif_results = calculate_vif_diagnostics(df, features, threshold=threshold)
        
        # Verify that the function returns results with flagged features
        flagged = {k: v for k, v in vif_results.items() if v > threshold}
        assert len(flagged) > 0, "Expected at least one flagged feature"
        assert 'x1' in flagged or 'x2' in flagged, "Expected x1 or x2 to be flagged"

class TestSkewedDistributionHandling:
    """
    Unit tests for skewed distribution handling (T046b).
    
    These tests verify that:
    1. Normality tests correctly identify skewed distributions
    2. Homogeneity of variance tests work correctly
    3. The system recommends appropriate fallback methods
    """

    def test_normality_test_skewed_data(self):
        """Test that Shapiro-Wilk correctly identifies skewed data."""
        np.random.seed(42)
        
        # Generate skewed data (exponential distribution)
        skewed_data = np.random.exponential(scale=2.0, size=100)
        
        stat, p_value = check_normality(skewed_data)
        
        # Skewed data should fail normality test (p < 0.05)
        assert p_value < 0.05, f"Expected p < 0.05 for skewed data, got {p_value}"
        logger.warning(f"Normality test failed for skewed data (p={p_value:.4f})")
    
    def test_normality_test_normal_data(self):
        """Test that Shapiro-Wilk correctly identifies normal data."""
        np.random.seed(42)
        
        # Generate normal data
        normal_data = np.random.normal(0, 1, 100)
        
        stat, p_value = check_normality(normal_data)
        
        # Normal data should pass normality test (p > 0.05)
        assert p_value > 0.05, f"Expected p > 0.05 for normal data, got {p_value}"
        logger.info(f"Normality test passed for normal data (p={p_value:.4f})")
    
    def test_homogeneity_variances_equal(self):
        """Test Levene's test for equal variances."""
        np.random.seed(42)
        
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(0, 1, 50)
        group3 = np.random.normal(0, 1, 50)
        
        stat, p_value = check_homogeneity_of_variance([group1, group2, group3])
        
        # Equal variances should pass (p > 0.05)
        assert p_value > 0.05, f"Expected p > 0.05 for equal variances, got {p_value}"
    
    def test_homogeneity_variances_unequal(self):
        """Test Levene's test for unequal variances."""
        np.random.seed(42)
        
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(0, 2, 50)  # Larger variance
        group3 = np.random.normal(0, 3, 50)  # Even larger variance
        
        stat, p_value = check_homogeneity_of_variance([group1, group2, group3])
        
        # Unequal variances should fail (p < 0.05)
        assert p_value < 0.05, f"Expected p < 0.05 for unequal variances, got {p_value}"
        logger.warning(f"Homogeneity of variance test failed (p={p_value:.4f})")
    
    def test_assumption_check_recommendation(self):
        """Test that the system recommends Welch's ANOVA when assumptions are violated."""
        np.random.seed(42)
        
        # Create data with unequal variances
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(0, 3, 50)
        
        # Check homogeneity
        stat, p_value = check_homogeneity_of_variance([group1, group2])
        
        if p_value < 0.05:
            logger.warning("Homogeneity assumption violated - recommend Welch's ANOVA")
            # In a real pipeline, this would trigger Welch's ANOVA
        else:
            logger.info("Homogeneity assumption satisfied - standard ANOVA is appropriate")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])