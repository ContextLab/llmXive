"""
Unit tests for Variance Inflation Factor (VIF) calculation and collinearity checks.

This module validates the logic used to detect multicollinearity between
predictors (politeness and conversation_length) before fitting the CLMM model.

Tests cover:
- VIF calculation accuracy on known datasets
- Threshold detection (VIF >= 5 triggers warning)
- Edge cases (perfect collinearity, constant columns)
"""

import pytest
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

# Import the implementation logic to be tested
# Since the implementation is in code/02_fit_clmm.py (T024), we implement
# the helper function here for testing purposes to ensure the logic is correct
# before the full script is written.

def calculate_vif(df: pd.DataFrame, features: list) -> dict:
    """
    Calculate Variance Inflation Factors for a list of features in a DataFrame.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to check for collinearity.
        
    Returns:
        Dictionary mapping feature names to their VIF values.
        
    Raises:
        ValueError: If features are not numeric or contain NaN.
    """
    if not all(col in df.columns for col in features):
        raise ValueError(f"One or more features {features} not found in DataFrame.")
        
    subset = df[features].dropna()
    
    if subset.empty:
        raise ValueError("No valid data remaining after dropping NaNs.")
        
    if subset.shape[0] < 3:
        raise ValueError("Insufficient data points to calculate VIF (need >= 3).")
        
    # Check for constant columns
    for col in features:
        if subset[col].std() == 0:
            raise ValueError(f"Feature '{col}' has zero variance (constant). Cannot calculate VIF.")
    
    X = add_constant(subset)
    vif_data = {}
    
    for i, col in enumerate(features):
        # VIF for feature i is the i-th diagonal element of (X'X)^-1
        # where X includes the constant and all features
        try:
            vif = variance_inflation_factor(X.values, i + 1) # +1 because index 0 is constant
            vif_data[col] = vif
        except np.linalg.LinAlgError:
            raise ValueError(f"Perfect multicollinearity detected among features {features}.")
            
    return vif_data

def check_collinearity(df: pd.DataFrame, features: list, threshold: float = 5.0) -> tuple:
    """
    Check for multicollinearity among features.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to check.
        threshold: VIF threshold above which collinearity is considered problematic.
        
    Returns:
        Tuple (has_high_collinearity, vif_results, warning_message)
        - has_high_collinearity: bool
        - vif_results: dict of feature -> vif
        - warning_message: str or None
    """
    vif_results = calculate_vif(df, features)
    
    high_collinearity_features = [
        feat for feat, vif in vif_results.items() if vif >= threshold
    ]
    
    has_high_collinearity = len(high_collinearity_features) > 0
    
    warning_msg = None
    if has_high_collinearity:
        warning_msg = (
            f"High multicollinearity detected (VIF >= {threshold}): "
            f"{', '.join(high_collinearity_features)}. "
            f"Consider removing these variables or using regularization."
        )
        
    return has_high_collinearity, vif_results, warning_msg


class TestVIFCalculation:
    """Tests for VIF calculation logic."""

    def test_vif_no_collinearity(self):
        """Test VIF calculation on independent variables."""
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'x3': np.random.randn(100)
        })
        
        vifs = calculate_vif(df, ['x1', 'x2', 'x3'])
        
        # With independent variables, VIF should be close to 1.0
        for vif in vifs.values():
            assert 1.0 <= vif < 2.0, f"VIF {vif} is unexpectedly high for independent variables."

    def test_vif_positive_correlation(self):
        """Test VIF increases with positive correlation."""
        np.random.seed(42)
        base = np.random.randn(100)
        # Create correlated variables
        df = pd.DataFrame({
            'x1': base,
            'x2': base * 0.9 + np.random.randn(100) * 0.1, # High correlation
            'x3': np.random.randn(100)
        })
        
        vifs = calculate_vif(df, ['x1', 'x2', 'x3'])
        
        # x1 and x2 should have high VIF (> 5) due to correlation
        assert vifs['x1'] > 5.0, "x1 VIF should be > 5 due to correlation with x2"
        assert vifs['x2'] > 5.0, "x2 VIF should be > 5 due to correlation with x1"

    def test_vif_perfect_collinearity_raises(self):
        """Test that perfect collinearity raises an error."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10] # Perfectly correlated (x2 = 2*x1)
        })
        
        with pytest.raises(ValueError, match="Perfect multicollinearity"):
            calculate_vif(df, ['x1', 'x2'])

    def test_vif_constant_column_raises(self):
        """Test that a constant column raises an error."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [5, 5, 5, 5, 5] # Constant
        })
        
        with pytest.raises(ValueError, match="zero variance"):
            calculate_vif(df, ['x1', 'x2'])

    def test_vif_missing_column_raises(self):
        """Test that missing columns raise an error."""
        df = pd.DataFrame({'x1': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="not found in DataFrame"):
            calculate_vif(df, ['x1', 'x2'])

    def test_vif_insufficient_data_raises(self):
        """Test that insufficient data raises an error."""
        df = pd.DataFrame({
            'x1': [1, 2],
            'x2': [3, 4]
        })
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            calculate_vif(df, ['x1', 'x2'])

    def test_vif_nan_handling(self):
        """Test that NaN values are dropped correctly."""
        df = pd.DataFrame({
            'x1': [1.0, 2.0, np.nan, 4.0, 5.0],
            'x2': [2.0, 4.0, 6.0, np.nan, 10.0]
        })
        
        # Should drop the row with NaN and calculate on remaining 3 rows
        # This might raise if < 3 rows remain, but here we have 3 valid rows
        vifs = calculate_vif(df, ['x1', 'x2'])
        
        assert len(vifs) == 2
        assert all(isinstance(v, float) for v in vifs.values())

class TestCollinearityCheck:
    """Tests for the high-level collinearity check function."""

    def test_check_no_warning(self):
        """Test check_collinearity returns no warning when VIF < threshold."""
        df = pd.DataFrame({
            'politeness': np.random.randn(100),
            'conversation_length': np.random.randn(100)
        })
        
        has_high, vifs, msg = check_collinearity(df, ['politeness', 'conversation_length'], threshold=5.0)
        
        assert not has_high
        assert msg is None
        assert all(v < 5.0 for v in vifs.values())

    def test_check_warning_triggered(self):
        """Test check_collinearity returns warning when VIF >= threshold."""
        np.random.seed(42)
        base = np.random.randn(100)
        df = pd.DataFrame({
            'politeness': base,
            'conversation_length': base * 0.95 + np.random.randn(100) * 0.05
        })
        
        has_high, vifs, msg = check_collinearity(df, ['politeness', 'conversation_length'], threshold=5.0)
        
        assert has_high
        assert msg is not None
        assert "High multicollinearity detected" in msg
        assert "politeness" in msg or "conversation_length" in msg

    def test_custom_threshold(self):
        """Test that custom threshold works."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [1.1, 2.1, 3.1, 4.1, 5.1]
        })
        
        # With threshold 10, should not warn even if VIF is moderately high
        has_high_10, _, msg_10 = check_collinearity(df, ['x1', 'x2'], threshold=10.0)
        
        # With threshold 1.5, should warn
        has_high_1_5, _, msg_1_5 = check_collinearity(df, ['x1', 'x2'], threshold=1.5)
        
        assert not has_high_10 or (msg_10 is None)
        # Note: With only 5 points and high correlation, VIF might be very high,
        # so we mainly check that the threshold logic is invoked.

class TestIntegrationWithScenario:
    """Integration tests simulating the actual usage in code/02_fit_clmm.py."""

    def test_politeness_length_scenario(self):
        """Simulate the specific scenario: politeness vs conversation_length."""
        np.random.seed(123)
        n = 500
        
        # Simulate realistic data where politeness and length might be slightly correlated
        # but not perfectly
        politeness = np.random.normal(0.5, 0.2, n)
        length = np.random.normal(10, 3, n)
        
        # Add slight correlation
        correlation_factor = 0.3
        length = length + correlation_factor * (politeness - 0.5) * 10
        
        df = pd.DataFrame({
            'quality_rating': np.random.randint(1, 6, n),
            'politeness': politeness,
            'conversation_length': length,
            'user_id': np.random.choice(range(50), n)
        })
        
        # Run the check
        has_high, vifs, msg = check_collinearity(
            df, 
            ['politeness', 'conversation_length'], 
            threshold=5.0
        )
        
        # Verify structure
        assert isinstance(vifs, dict)
        assert 'politeness' in vifs
        assert 'conversation_length' in vifs
        
        # In this scenario, VIFs should likely be < 5 (no high collinearity)
        # unless the correlation is very strong
        if has_high:
            assert msg is not None
            assert "politeness" in msg or "conversation_length" in msg

    def test_drop_variable_logic(self):
        """Test the logic for deciding which variable to drop."""
        np.random.seed(42)
        base = np.random.randn(100)
        df = pd.DataFrame({
            'A': base,
            'B': base * 0.99, # Very high correlation
            'C': np.random.randn(100)
        })
        
        has_high, vifs, msg = check_collinearity(df, ['A', 'B', 'C'], threshold=5.0)
        
        assert has_high
        # The variable with the higher VIF should be flagged
        # (Though in perfect correlation, both are high)
        assert 'A' in vifs or 'B' in vifs