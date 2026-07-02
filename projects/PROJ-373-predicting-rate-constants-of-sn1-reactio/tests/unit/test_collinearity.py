"""
Unit tests for Variance Inflation Factor (VIF) calculation in code/analysis/collinearity.py.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.collinearity import calculate_vif, calculate_vif_for_dataframe, flag_high_collinearity

class TestVIFCalculation:
    """Tests for the VIF calculation functions."""

    def test_vif_perfectly_uncorrelated(self):
        """Test VIF is 1.0 for perfectly uncorrelated features (identity matrix)."""
        # Create data with identity correlation structure
        n_samples = 100
        data = np.random.randn(n_samples, 3)
        # Ensure orthogonality by using a subset of random data that is effectively uncorrelated
        # For a strict test, we construct a matrix where columns are orthogonal
        # Using a simple orthogonal set
        X = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 1],
            [1, -1, 0],
            [0, 1, -1]
        ] * 20) # Repeat to get enough samples
        
        # Add noise to make it realistic but keep low correlation
        X = X + np.random.normal(0, 0.01, X.shape)
        
        vif_values = calculate_vif(X)
        
        # VIF should be close to 1.0 for uncorrelated features
        assert all(1.0 <= v <= 1.5 for v in vif_values), f"VIF values should be near 1.0, got {vif_values}"

    def test_vif_perfectly_correlated(self):
        """Test VIF is very high (or infinite) for perfectly correlated features."""
        # Create data with perfect correlation
        n_samples = 50
        x1 = np.random.randn(n_samples)
        x2 = x1 * 2 + 1  # Perfect linear relationship
        X = np.column_stack([x1, x2])
        
        # Add a third independent variable to avoid singular matrix issues in some implementations
        x3 = np.random.randn(n_samples)
        X = np.column_stack([X, x3])
        
        vif_values = calculate_vif(X)
        
        # At least one VIF should be very high (indicating multicollinearity)
        # Note: Exact value depends on implementation details, but should be > 100
        assert any(v > 100 for v in vif_values), f"VIF should be high for correlated features, got {vif_values}"

    def test_vif_moderate_correlation(self):
        """Test VIF values are elevated but not extreme for moderately correlated features."""
        n_samples = 100
        x1 = np.random.randn(n_samples)
        x2 = 0.7 * x1 + 0.3 * np.random.randn(n_samples)  # Moderate correlation
        X = np.column_stack([x1, x2])
        
        vif_values = calculate_vif(X)
        
        # VIF should be > 1 but not extremely high
        assert all(v > 1.0 for v in vif_values), "VIF should be greater than 1 for correlated features"
        assert all(v < 100 for v in vif_values), "VIF should not be extreme for moderate correlation"

    def test_vif_single_feature(self):
        """Test VIF for a single feature is 1.0."""
        X = np.random.randn(50, 1)
        vif_values = calculate_vif(X)
        assert len(vif_values) == 1
        assert np.isclose(vif_values[0], 1.0), "VIF for single feature should be 1.0"

    def test_vif_dataframe_input(self):
        """Test VIF calculation works with pandas DataFrame."""
        df = pd.DataFrame({
            'feature_a': np.random.randn(100),
            'feature_b': np.random.randn(100),
            'feature_c': np.random.randn(100)
        })
        
        vif_series = calculate_vif_for_dataframe(df)
        
        assert isinstance(vif_series, pd.Series)
        assert len(vif_series) == 3
        assert list(vif_series.index) == ['feature_a', 'feature_b', 'feature_c']
        assert all(v >= 1.0 for v in vif_series.values), "VIF should be >= 1.0"

    def test_flag_high_collinearity(self):
        """Test the flagging function for high collinearity."""
        # Create a dataframe with known collinearity
        n_samples = 100
        x1 = np.random.randn(n_samples)
        x2 = 0.9 * x1 + 0.1 * np.random.randn(n_samples)  # High correlation
        x3 = np.random.randn(n_samples)  # Independent
        
        df = pd.DataFrame({
            'low_vif': x3,
            'high_vif_1': x1,
            'high_vif_2': x2
        })
        
        vif_series = calculate_vif_for_dataframe(df)
        flagged_pairs = flag_high_collinearity(df, threshold=5.0)
        
        # Check that high collinearity is detected
        assert len(flagged_pairs) > 0, "Should detect high collinearity pairs"
        
        # Verify the flagged pairs involve the correlated features
        correlated_features = {'high_vif_1', 'high_vif_2'}
        found_flag = False
        for pair in flagged_pairs:
            if pair[0] in correlated_features or pair[1] in correlated_features:
                found_flag = True
                break
        
        assert found_flag, "Should flag pairs involving highly correlated features"

    def test_vif_with_constant_feature(self):
        """Test behavior with a constant feature (should handle gracefully)."""
        X = np.array([
            [1, 2, 3],
            [1, 4, 5],
            [1, 6, 7],
            [1, 8, 9]
        ])
        
        # Constant feature might cause division by zero or singular matrix
        # Our implementation should handle this by returning a high VIF or NaN
        try:
            vif_values = calculate_vif(X)
            # If it doesn't crash, at least check the structure
            assert len(vif_values) == 3
        except Exception as e:
            # If it raises an exception, it should be clear and expected
            assert "singular" in str(e).lower() or "constant" in str(e).lower() or "infinite" in str(e).lower(), \
                f"Unexpected error type: {e}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])