"""
Unit tests for Variance Inflation Factor (VIF) calculation and collinearity handling.

This module tests the VIF implementation used in User Story 3 (Correlation Analysis)
to detect multicollinearity among predictor variables before performing regression
or partial correlation analyses.

Tests cover:
- VIF calculation for simple and complex datasets
- Collinearity flagging when VIF > 5
- Preparation of PCA components for high collinearity scenarios
- Edge cases (constant variables, perfect collinearity)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.validation import validate_dataframe_not_empty


def calculate_vif(df: pd.DataFrame, exclude_col: str = None) -> pd.Series:
    """
    Calculate Variance Inflation Factor for each predictor variable.
    
    This is a standalone implementation for testing purposes, matching the logic
    that will be used in code/03_correlation_analysis.py.
    
    Args:
        df: DataFrame with numeric predictor variables
        exclude_col: Column to exclude from VIF calculation (e.g., target variable)
        
    Returns:
        Series with VIF values indexed by column name
        
    Raises:
        ValueError: If input contains non-numeric columns or NaN values
    """
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if exclude_col and exclude_col in numeric_df.columns:
        numeric_df = numeric_df.drop(columns=[exclude_col])
        
    if numeric_df.empty:
        raise ValueError("No numeric columns available for VIF calculation")
        
    if numeric_df.isnull().any().any():
        raise ValueError("Input data contains NaN values. Please handle missing data first.")
        
    vif_data = {}
    
    # Add constant column for intercept
    X = numeric_df.copy()
    X['const'] = 1.0
    
    for col in numeric_df.columns:
        # Regress current variable against all other variables
        y = X[col]
        X_other = X.drop(columns=[col])
        
        # Simple OLS: beta = (X'X)^-1 X'y
        try:
            # Calculate R-squared for this regression
            # Using numpy for linear algebra
            X_other_array = X_other.values
            y_array = y.values
            
            # Solve normal equations
            # beta = (X'X)^-1 X'y
            XtX = X_other_array.T @ X_other_array
            Xty = X_other_array.T @ y_array
            
            # Check for singularity
            if np.linalg.cond(XtX) > 1e10:
                # Near perfect collinearity
                vif_data[col] = np.inf
                continue
                
            beta = np.linalg.solve(XtX, Xty)
            y_pred = X_other_array @ beta
            
            # Calculate R-squared
            ss_res = np.sum((y_array - y_pred) ** 2)
            ss_tot = np.sum((y_array - np.mean(y_array)) ** 2)
            
            if ss_tot == 0:
                vif_data[col] = np.inf
            else:
                r_squared = 1 - (ss_res / ss_tot)
                if r_squared >= 1.0:
                    vif_data[col] = np.inf
                else:
                    vif_data[col] = 1 / (1 - r_squared)
                    
        except np.linalg.LinAlgError:
            vif_data[col] = np.inf
            
    return pd.Series(vif_data)


def check_collinearity(vif_series: pd.Series, threshold: float = 5.0) -> dict:
    """
    Check for collinearity issues based on VIF values.
    
    Args:
        vif_series: Series of VIF values from calculate_vif
        threshold: VIF threshold above which collinearity is flagged (default 5.0)
        
    Returns:
        Dictionary with collinearity status and affected variables
    """
    high_vif_vars = vif_series[vif_series > threshold].index.tolist()
    
    return {
        "has_collinearity": len(high_vif_vars) > 0,
        "threshold": threshold,
        "affected_variables": high_vif_vars,
        "max_vif": float(vif_series.max()) if not vif_series.empty else 0.0,
        "vif_values": vif_series.to_dict()
    }


class TestVIFCalculation:
    """Test suite for VIF calculation and collinearity handling."""
    
    def test_vif_calculates_for_independent_variables(self):
        """Test VIF calculation with independent variables (should be close to 1)."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'var1': np.random.randn(n),
            'var2': np.random.randn(n),
            'var3': np.random.randn(n)
        })
        
        vif = calculate_vif(df)
        
        # VIF for independent variables should be close to 1
        assert all(vif < 2.0), f"Expected VIF < 2 for independent variables, got: {vif}"
        assert all(vif >= 1.0), "VIF should never be less than 1"
        
    def test_vif_increases_with_correlation(self):
        """Test that VIF increases as correlation between variables increases."""
        n = 100
        np.random.seed(42)
        base = np.random.randn(n)
        
        # Low correlation case
        df_low = pd.DataFrame({
            'var1': base,
            'var2': base * 0.3 + np.random.randn(n) * 0.9
        })
        vif_low = calculate_vif(df_low)
        
        # High correlation case
        df_high = pd.DataFrame({
            'var1': base,
            'var2': base * 0.95 + np.random.randn(n) * 0.1
        })
        vif_high = calculate_vif(df_high)
        
        # VIF should be higher for highly correlated variables
        assert vif_high['var1'] > vif_low['var1'], "VIF should increase with correlation"
        assert vif_high['var2'] > vif_low['var2'], "VIF should increase with correlation"
        
    def test_vif_perfect_collinearity(self):
        """Test VIF calculation with perfect collinearity (should be infinite)."""
        n = 50
        base = np.random.randn(n)
        df = pd.DataFrame({
            'var1': base,
            'var2': base * 2.0  # Perfect linear relationship
        })
        
        vif = calculate_vif(df)
        
        # VIF should be infinite or very large for perfect collinearity
        assert vif['var1'] == np.inf or vif['var1'] > 1000, \
            f"Expected infinite VIF for perfect collinearity, got {vif['var1']}"
            
    def test_vif_constant_variable(self):
        """Test VIF calculation with a constant variable."""
        n = 50
        df = pd.DataFrame({
            'var1': np.random.randn(n),
            'var2': np.ones(n)  # Constant variable
        })
        
        # This should raise an error or return infinite VIF
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            calculate_vif(df)
            
    def test_vif_with_nan_raises_error(self):
        """Test that VIF calculation raises error for NaN values."""
        df = pd.DataFrame({
            'var1': [1.0, 2.0, np.nan, 4.0],
            'var2': [5.0, 6.0, 7.0, 8.0]
        })
        
        with pytest.raises(ValueError, match="NaN"):
            calculate_vif(df)
            
    def test_vif_exclude_column(self):
        """Test VIF calculation with a column to exclude."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'var1': np.random.randn(n),
            'var2': np.random.randn(n),
            'target': np.random.randn(n)
        })
        
        vif = calculate_vif(df, exclude_col='target')
        
        assert 'target' not in vif.index, "Excluded column should not be in VIF results"
        assert len(vif) == 2, "Should have VIF for 2 variables"
        
    def test_collinearity_check_returns_correct_structure(self):
        """Test that collinearity check returns expected dictionary structure."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'var1': np.random.randn(n),
            'var2': np.random.randn(n)
        })
        
        vif = calculate_vif(df)
        result = check_collinearity(vif)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'has_collinearity' in result, "Missing 'has_collinearity' key"
        assert 'threshold' in result, "Missing 'threshold' key"
        assert 'affected_variables' in result, "Missing 'affected_variables' key"
        assert 'max_vif' in result, "Missing 'max_vif' key"
        assert 'vif_values' in result, "Missing 'vif_values' key"
        
    def test_collinearity_flagged_above_threshold(self):
        """Test that collinearity is flagged when VIF exceeds threshold."""
        n = 100
        base = np.random.randn(n)
        df = pd.DataFrame({
            'var1': base,
            'var2': base * 0.98 + np.random.randn(n) * 0.05  # High correlation
        })
        
        vif = calculate_vif(df)
        result = check_collinearity(vif, threshold=5.0)
        
        assert result['has_collinearity'] is True, \
            "Should flag collinearity when VIF > 5"
        assert len(result['affected_variables']) > 0, \
            "Should list affected variables"
            
    def test_collinearity_not_flagged_below_threshold(self):
        """Test that collinearity is not flagged when VIF is below threshold."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'var1': np.random.randn(n),
            'var2': np.random.randn(n)
        })
        
        vif = calculate_vif(df)
        result = check_collinearity(vif, threshold=5.0)
        
        assert result['has_collinearity'] is False, \
            "Should not flag collinearity when VIF < 5"
        assert len(result['affected_variables']) == 0, \
            "Should have no affected variables"
            
    def test_pca_preparation_for_high_collinearity(self):
        """Test that PCA components can be prepared when collinearity is high."""
        import numpy.linalg as la
        
        n = 100
        base = np.random.randn(n)
        df = pd.DataFrame({
            'var1': base,
            'var2': base * 0.95 + np.random.randn(n) * 0.1,
            'var3': base * 0.9 + np.random.randn(n) * 0.2
        })
        
        vif = calculate_vif(df)
        result = check_collinearity(vif, threshold=5.0)
        
        if result['has_collinearity']:
            # Verify we can perform PCA on the affected variables
            affected = result['affected_variables']
            if len(affected) >= 2:
                X = df[affected].values
                # Check that we can compute PCA (via SVD)
                U, S, Vt = la.svd(X, full_matrices=False)
                assert S.shape[0] > 0, "PCA should produce singular values"
                
    def test_vif_with_realistic_eeg_metrics(self):
        """Test VIF with realistic EEG metric correlations (alpha power, PLV, WM)."""
        np.random.seed(42)
        n = 52  # Typical sample size for this study
        
        # Simulate realistic correlations: alpha power and PLV often correlate
        alpha_frontal = np.random.randn(n) * 0.5 + 0.3
        alpha_parietal = alpha_frontal * 0.6 + np.random.randn(n) * 0.4
        plv = alpha_frontal * 0.5 + alpha_parietal * 0.3 + np.random.randn(n) * 0.3
        wm_capacity = alpha_frontal * 0.4 + plv * 0.2 + np.random.randn(n) * 0.5
        
        df = pd.DataFrame({
            'alpha_frontal': alpha_frontal,
            'alpha_parietal': alpha_parietal,
            'plv': plv,
            'wm_capacity': wm_capacity
        })
        
        vif = calculate_vif(df, exclude_col='wm_capacity')
        result = check_collinearity(vif, threshold=5.0)
        
        # Verify structure is correct
        assert 'vif_values' in result
        assert len(result['vif_values']) == 3  # 3 predictors
        
        # Even with moderate correlation, VIF might not exceed 5
        # but the calculation should be valid
        assert all(v > 1.0 for v in vif.values), "All VIF values should be >= 1"
        
    def test_vif_empty_dataframe(self):
        """Test VIF calculation with empty dataframe."""
        df = pd.DataFrame()
        
        with pytest.raises(ValueError):
            calculate_vif(df)
            
    def test_vif_single_column(self):
        """Test VIF calculation with single predictor column."""
        df = pd.DataFrame({
            'var1': np.random.randn(50)
        })
        
        # With only one predictor, VIF calculation might fail or return 1
        # depending on implementation
        try:
            vif = calculate_vif(df)
            # If it succeeds, VIF should be 1 (no other variables to correlate with)
            assert vif['var1'] == 1.0 or vif['var1'] == np.inf
        except ValueError:
            # This is also acceptable behavior
            pass


class TestCollinearityHandling:
    """Test suite for collinearity handling strategies."""
    
    def test_prepare_pca_components(self):
        """Test preparation of PCA components for collinear variables."""
        from sklearn.decomposition import PCA
        
        n = 100
        base = np.random.randn(n)
        df = pd.DataFrame({
            'var1': base,
            'var2': base * 0.95 + np.random.randn(n) * 0.1,
            'var3': base * 0.9 + np.random.randn(n) * 0.2
        })
        
        # Perform PCA
        pca = PCA(n_components=2)
        components = pca.fit_transform(df.values)
        
        assert components.shape[0] == n, "Should have same number of samples"
        assert components.shape[1] <= df.shape[1], "Should have reduced components"
        assert np.sum(pca.explained_variance_ratio_) > 0.5, \
            "PCA should explain significant variance"
            
    def test_joint_variance_reporting(self):
        """Test that joint variance can be reported for collinear variables."""
        n = 100
        base = np.random.randn(n)
        df = pd.DataFrame({
            'var1': base,
            'var2': base * 0.95 + np.random.randn(n) * 0.1
        })
        
        vif = calculate_vif(df)
        result = check_collinearity(vif)
        
        if result['has_collinearity']:
            # Report joint variance (descriptive only)
            from sklearn.decomposition import PCA
            pca = PCA(n_components=1)
            pca.fit(df.values)
            
            joint_variance = pca.explained_variance_ratio_[0]
            assert 0 < joint_variance <= 1.0, "Joint variance should be between 0 and 1"
            
    def test_vif_threshold_documentation(self):
        """Test that VIF threshold of 5 is documented and used consistently."""
        # The threshold of 5 is a common rule of thumb in statistics
        # This test ensures we use it consistently
        default_result = check_collinearity(pd.Series({'a': 6.0}))
        assert default_result['threshold'] == 5.0, "Default threshold should be 5.0"
        
        custom_result = check_collinearity(pd.Series({'a': 6.0}), threshold=10.0)
        assert custom_result['threshold'] == 10.0, "Custom threshold should be respected"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
