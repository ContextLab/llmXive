"""
Unit test for metric calculation (R², RMSE, p-values).
This test suite validates the mathematical correctness of the regression metrics
used in User Story 2, specifically R², RMSE, and p-value extraction from OLS models.
"""
import pytest
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error
import statsmodels.api as sm
import sys
from pathlib import Path

# Ensure the project 'code' directory is in the path for imports if needed
# (though this specific test relies mostly on standard libraries and sklearn/statsmodels)
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

def test_r2_calculation():
    """Test R² calculation with known values."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.1, 2.9, 4.1, 5.0])
    
    r2 = r2_score(y_true, y_pred)
    
    # Expect a very high R² given the close predictions
    assert 0.95 <= r2 <= 1.0, f"R² should be close to 1.0, got {r2}"
    
    # Verify against manual calculation: 1 - SS_res / SS_tot
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    manual_r2 = 1 - (ss_res / ss_tot)
    assert np.abs(r2 - manual_r2) < 1e-6, "sklearn R² does not match manual calculation"

def test_rmse_calculation():
    """Test RMSE calculation with known values."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.1, 2.9, 4.1, 5.0])
    
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    # Expected RMSE is approx 0.07
    expected_rmse = np.sqrt(np.sum((y_true - y_pred) ** 2) / len(y_true))
    assert np.abs(rmse - expected_rmse) < 1e-6, "RMSE calculation mismatch"
    assert rmse < 0.2, f"RMSE should be small, got {rmse}"

def test_pvalue_extraction():
    """Test p-value extraction from OLS model using statsmodels."""
    # Generate deterministic synthetic data for reproducibility
    np.random.seed(42)
    n_samples = 100
    X = np.random.rand(n_samples, 2)
    # y = 1.0 + 2.0*X1 + 3.0*X2 + noise
    y = 1.0 + 2.0 * X[:, 0] + 3.0 * X[:, 1] + np.random.normal(0, 0.1, n_samples)
    
    X_with_const = sm.add_constant(X)
    model = sm.OLS(y, X_with_const).fit()
    
    pvalues = model.pvalues
    
    # Check dimensions: 1 constant + 2 features = 3 coefficients
    assert len(pvalues) == 3, f"Should have 3 coefficients (const + 2 features), got {len(pvalues)}"
    
    # Check range: p-values must be between 0 and 1
    assert all(pvalues >= 0) and all(pvalues <= 1), "P-values must be between 0 and 1"
    
    # Check significance: The true coefficients are 1, 2, 3 with low noise.
    # P-values for the features should be very small (significant).
    # The intercept (const) should also be significant.
    # We assert that p-values for the features (index 1 and 2) are < 0.05
    assert pvalues[1] < 0.05, f"Feature 1 p-value should be significant (< 0.05), got {pvalues[1]}"
    assert pvalues[2] < 0.05, f"Feature 2 p-value should be significant (< 0.05), got {pvalues[2]}"

def test_pvalue_extraction_edge_case():
    """Test p-value extraction when data is perfectly collinear (should raise or handle)."""
    np.random.seed(42)
    n_samples = 50
    # Create perfect collinearity: X2 = X1
    X = np.column_stack([np.random.rand(n_samples), np.random.rand(n_samples)])
    X[:, 1] = X[:, 0] 
    y = X[:, 0] + np.random.normal(0, 0.1, n_samples)
    
    X_with_const = sm.add_constant(X)
    
    # This should raise a PerfectCollinearityWarning or similar in statsmodels,
    # but the fit object will still exist, potentially with NaN p-values for the redundant feature.
    with pytest.warns(UserWarning):
        model = sm.OLS(y, X_with_const).fit()
    
    pvalues = model.pvalues
    # One of the p-values for the collinear feature might be NaN or very high
    # We just verify the extraction doesn't crash and returns an array of correct length
    assert len(pvalues) == 3

def test_metrics_consistency():
    """Test that R² and RMSE are consistent with each other for a simple case."""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    assert r2 == 1.0, "Perfect prediction should yield R² = 1.0"
    assert rmse == 0.0, "Perfect prediction should yield RMSE = 0.0"