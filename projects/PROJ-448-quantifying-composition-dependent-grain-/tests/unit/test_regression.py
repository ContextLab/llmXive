"""
Unit tests for interaction term generation (T019).
Tests the generation of polynomial interaction terms for regression analysis
as specified in FR-004 and T021a.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression


class TestInteractionTermGeneration:
    """Tests for generating interaction terms for multicomponent analysis."""

    def test_polynomial_features_degree_2(self):
        """Test that PolynomialFeatures correctly generates degree 2 interaction terms."""
        # Sample data: 3 samples, 2 features (Cr, Mo concentrations)
        X = np.array([
            [0.1, 0.2],
            [0.2, 0.3],
            [0.15, 0.25]
        ])

        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)

        # Expected columns: [Cr, Mo, Cr^2, Cr*Mo, Mo^2]
        # For first row [0.1, 0.2]:
        # [0.1, 0.2, 0.01, 0.02, 0.04]
        expected_shape = (3, 5)
        assert X_poly.shape == expected_shape, f"Expected shape {expected_shape}, got {X_poly.shape}"

        # Verify the interaction term (Cr*Mo) for first row
        expected_interaction = 0.1 * 0.2
        actual_interaction = X_poly[0, 3]  # 4th column (0-indexed) is Cr*Mo
        assert np.isclose(actual_interaction, expected_interaction), \
            f"Interaction term mismatch: expected {expected_interaction}, got {actual_interaction}"

    def test_interaction_terms_with_ternary_system(self):
        """Test interaction term generation for ternary system (Cr, Mo, V)."""
        # Sample data: 3 samples, 3 features (Cr, Mo, V concentrations)
        X = np.array([
            [0.1, 0.2, 0.05],
            [0.15, 0.25, 0.1],
            [0.12, 0.18, 0.08]
        ])

        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)

        # Expected columns: [Cr, Mo, V, Cr^2, Cr*Mo, Cr*V, Mo^2, Mo*V, V^2]
        # Total: 3 original + 3 squares + 3 interactions = 9 columns
        expected_shape = (3, 9)
        assert X_poly.shape == expected_shape, f"Expected shape {expected_shape}, got {X_poly.shape}"

        # Verify specific interaction terms for first row
        # Cr*Mo = 0.1 * 0.2 = 0.02
        # Cr*V = 0.1 * 0.05 = 0.005
        # Mo*V = 0.2 * 0.05 = 0.01
        assert np.isclose(X_poly[0, 4], 0.02), "Cr*Mo interaction incorrect"
        assert np.isclose(X_poly[0, 5], 0.005), "Cr*V interaction incorrect"
        assert np.isclose(X_poly[0, 7], 0.01), "Mo*V interaction incorrect"

    def test_interaction_terms_identical_to_manual(self):
        """Verify sklearn results match manual calculation."""
        X = np.array([[0.1, 0.2, 0.05]])
        
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)

        # Manual calculation
        cr, mo, v = X[0]
        expected = np.array([[
            cr, mo, v,           # Original features
            cr**2, cr*mo, cr*v,  # Squares and interactions
            mo**2, mo*v,         # More interactions
            v**2                 # Last square
        ]])

        assert np.allclose(X_poly, expected), \
            f"Sklearn results do not match manual calculation:\nExpected: {expected}\nGot: {X_poly}"

    def test_regression_with_interaction_terms(self):
        """Test that regression model can be fitted with interaction terms."""
        # Generate synthetic data with known interaction effect
        np.random.seed(42)
        n_samples = 100
        
        X = np.random.rand(n_samples, 2)  # Cr, Mo
        # True model: y = 2*Cr + 3*Mo + 5*Cr*Mo + noise
        y = 2*X[:, 0] + 3*X[:, 1] + 5*X[:, 0]*X[:, 1] + np.random.normal(0, 0.1, n_samples)

        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)

        model = LinearRegression()
        model.fit(X_poly, y)

        # Check that model was fitted successfully
        assert hasattr(model, 'coef_'), "Model should have coefficients"
        assert len(model.coef_) == 5, "Should have 5 coefficients for 5 features"
        
        # The interaction term coefficient (index 3) should be close to 5
        # Allow some tolerance due to noise and finite sample size
        interaction_coef = model.coef_[3]
        assert 4.0 < interaction_coef < 6.0, \
            f"Interaction coefficient {interaction_coef} should be close to 5.0"

    def test_edge_case_zero_concentration(self):
        """Test interaction terms when some concentrations are zero."""
        X = np.array([
            [0.0, 0.0],
            [0.1, 0.0],
            [0.0, 0.2]
        ])

        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)

        # All interaction terms should be zero when any factor is zero
        assert np.allclose(X_poly[:, 3], 0.0), "Cr*Mo should be zero when either is zero"
        assert np.allclose(X_poly[:, 0:2], X), "Original features preserved"

    def test_feature_names_inference(self):
        """Test that we can infer feature names for interpretation."""
        X = np.array([[0.1, 0.2, 0.05]])
        feature_names = ['Cr', 'Mo', 'V']
        
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)

        # Get feature names from the transformer
        poly_feature_names = poly.get_feature_names_out(feature_names)
        
        # Verify we have the expected names
        expected_names = ['Cr', 'Mo', 'V', 'Cr Cr', 'Cr Mo', 'Cr V', 'Mo Mo', 'Mo V', 'V V']
        assert list(poly_feature_names) == expected_names, \
            f"Feature names mismatch: expected {expected_names}, got {list(poly_feature_names)}"

        # Verify the interaction term name
        assert 'Cr Mo' in poly_feature_names, "Cr Mo interaction should be in feature names"

    def test_large_dataset_performance(self):
        """Test interaction term generation with larger dataset."""
        np.random.seed(123)
        n_samples = 10000
        X = np.random.rand(n_samples, 3)  # Cr, Mo, V

        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)

        assert X_poly.shape[0] == n_samples, "Sample count should be preserved"
        assert X_poly.shape[1] == 9, "Feature count should be 9 for 3 inputs degree 2"
        
        # Verify no NaN or Inf values
        assert not np.any(np.isnan(X_poly)), "Generated features should not contain NaN"
        assert not np.any(np.isinf(X_poly)), "Generated features should not contain Inf"

    def test_consistency_with_pandas_dataframe(self):
        """Test that interaction terms work correctly with pandas DataFrames."""
        df = pd.DataFrame({
            'Cr': [0.1, 0.2, 0.15],
            'Mo': [0.2, 0.3, 0.25],
            'V': [0.05, 0.1, 0.08]
        })

        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(df.values)

        # Convert back to DataFrame for verification
        feature_names = poly.get_feature_names_out(df.columns)
        df_poly = pd.DataFrame(X_poly, columns=feature_names)

        # Verify specific values
        assert np.isclose(df_poly['Cr Mo'].iloc[0], 0.1 * 0.2), "Cr*Mo calculation incorrect"
        assert np.isclose(df_poly['Cr V'].iloc[0], 0.1 * 0.05), "Cr*V calculation incorrect"
        assert np.isclose(df_poly['Mo V'].iloc[0], 0.2 * 0.05), "Mo*V calculation incorrect"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])