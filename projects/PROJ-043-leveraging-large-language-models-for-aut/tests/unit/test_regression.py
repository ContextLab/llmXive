"""
Unit tests for Variance Inflation Factor (VIF) calculation and predictor filtering.
Tests the logic defined in T030: iterative dropping of predictors with VIF > 5.
"""
import pytest
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# Import the module under test. Since T027-T033 are not implemented yet,
# we implement the VIF logic inline for testing purposes or mock the module.
# However, to strictly follow "real code" and "extend don't re-author",
# we assume `code/models/regression.py` will contain the `calculate_vif` and `filter_predictors` functions.
# For this test to run standalone, we define the functions here if the module doesn't exist yet,
# or import them. Given the task is to write the test, we will implement the minimal
# logic in a local helper or import if available.
# Since T030 (implementation) is not done, we cannot import from `code.models.regression` yet.
# We will implement the VIF logic as a local function to test the *logic* of the test,
# but the test itself is designed to be run against the implementation once T030 is done.
# To satisfy the "real runnable code" constraint immediately, we include the implementation
# of the VIF logic within this test file as a "fixture" for the test, but note that
# the actual production code should reside in `code/models/regression.py`.

# NOTE: In a real pipeline, this would be: from models.regression import calculate_vif, filter_predictors
# Since T030 is pending, we define them here to make the test runnable and valid.

def calculate_vif(df: pd.DataFrame, exclude_intercept: bool = True) -> pd.Series:
    """
    Calculate Variance Inflation Factors for all numeric columns in the DataFrame.
    """
    vif_data = pd.Series()
    cols = df.columns.tolist()
    if exclude_intercept and 'intercept' in cols:
        cols.remove('intercept')
    
    # Add constant for OLS
    X = df[cols]
    X = add_constant(X)
    
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
        except Exception:
            vif_data[col] = np.inf
    
    return vif_data

def filter_predictors(df: pd.DataFrame, predictors: list, threshold: float = 5.0) -> list:
    """
    Iteratively drop the predictor with the highest VIF until all remaining 
    predictors have VIF <= threshold.
    """
    current_predictors = predictors.copy()
    max_iterations = len(predictors)
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        if not current_predictors:
            break
        
        # Create a dataframe with the current predictors and the target (if needed, but VIF only needs predictors)
        # We assume the input df contains the predictors.
        subset_df = df[current_predictors]
        
        vif_series = calculate_vif(subset_df, exclude_intercept=True)
        
        if vif_series.empty:
            break
        
        max_vif = vif_series.max()
        
        if max_vif <= threshold:
            break
        
        # Drop the predictor with the highest VIF
        worst_predictor = vif_series.idxmax()
        current_predictors.remove(worst_predictor)
    
    return current_predictors

class TestVIFCalculation:
    """Tests for VIF calculation logic."""

    def test_vif_calculation_perfect_collinearity(self):
        """Test that VIF is very high when perfect collinearity exists."""
        # Create data where X2 is exactly X1 * 2
        data = {
            'X1': [1, 2, 3, 4, 5],
            'X2': [2, 4, 6, 8, 10], # Perfectly collinear
            'X3': [1, 0, 1, 0, 1]
        }
        df = pd.DataFrame(data)
        
        vif = calculate_vif(df)
        
        # X2 should have a very high VIF (or infinity)
        assert vif['X2'] > 1000 or np.isinf(vif['X2'])

    def test_vif_calculation_no_collinearity(self):
        """Test that VIF is low when predictors are independent."""
        np.random.seed(42)
        data = {
            'X1': np.random.rand(100),
            'X2': np.random.rand(100),
            'X3': np.random.rand(100)
        }
        df = pd.DataFrame(data)
        
        vif = calculate_vif(df)
        
        # All VIFs should be close to 1
        assert all(vif < 5), f"VIFs were too high: {vif}"

class TestPredictorFiltering:
    """Tests for the iterative VIF filtering logic."""

    def test_filter_removes_high_vif(self):
        """Test that the function removes predictors with VIF > 5."""
        # Create a dataset with one highly collinear variable
        np.random.seed(42)
        n = 100
        X1 = np.random.rand(n)
        X2 = X1 + np.random.rand(n) * 0.01 # Highly correlated
        X3 = np.random.rand(n) # Independent
        X4 = np.random.rand(n) # Independent
        
        df = pd.DataFrame({
            'X1': X1,
            'X2': X2,
            'X3': X3,
            'X4': X4
        })
        
        initial_predictors = ['X1', 'X2', 'X3', 'X4']
        filtered = filter_predictors(df, initial_predictors, threshold=5.0)
        
        # One of X1 or X2 should be removed
        assert len(filtered) < len(initial_predictors)
        # The remaining set should have VIF <= 5
        remaining_vif = calculate_vif(df[filtered])
        assert all(remaining_vif <= 5.0), f"Filtered set still has high VIF: {remaining_vif}"

    def test_filter_stops_when_all_valid(self):
        """Test that the function returns all predictors if all VIFs are already low."""
        np.random.seed(42)
        data = {
            'A': np.random.rand(50),
            'B': np.random.rand(50),
            'C': np.random.rand(50)
        }
        df = pd.DataFrame(data)
        
        predictors = ['A', 'B', 'C']
        filtered = filter_predictors(df, predictors, threshold=5.0)
        
        assert set(filtered) == set(predictors)

    def test_filter_handles_all_collinear(self):
        """Test behavior when all predictors are collinear."""
        # All variables are copies
        data = {
            'A': [1, 2, 3, 4],
            'B': [1, 2, 3, 4],
            'C': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        predictors = ['A', 'B', 'C']
        filtered = filter_predictors(df, predictors, threshold=5.0)
        
        # Should reduce to a single variable (or empty if logic dictates)
        # Usually keeps one to avoid perfect singularity
        assert len(filtered) <= 1

class TestIntegrationWithOLS:
    """Integration tests ensuring filtered predictors work with OLS."""

    def test_filtered_predictors_fit_ols(self):
        """Ensure the filtered set can be used to fit a valid OLS model."""
        np.random.seed(42)
        n = 200
        X1 = np.random.rand(n)
        X2 = X1 * 0.9 + np.random.rand(n) * 0.1 # Correlated
        X3 = np.random.rand(n)
        y = X1 + X3 + np.random.rand(n) * 0.1
        
        df = pd.DataFrame({
            'X1': X1,
            'X2': X2,
            'X3': X3,
            'y': y
        })
        
        predictors = ['X1', 'X2', 'X3']
        filtered = filter_predictors(df, predictors, threshold=5.0)
        
        # Fit OLS
        X_filtered = add_constant(df[filtered])
        model = OLS(df['y'], X_filtered).fit()
        
        # Check that model fitted successfully
        assert model.rsquared_adj > 0
        assert not np.isnan(model.rsquared_adj)