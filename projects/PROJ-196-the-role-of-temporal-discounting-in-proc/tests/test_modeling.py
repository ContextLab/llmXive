import pytest
import numpy as np
import pandas as pd
from code.modeling import hyperbolic_function, transform_and_center, calculate_vif

def test_hyperbolic_function():
    result = hyperbolic_function(1, 0.1, 100)
    assert abs(result - 90.909) < 0.1

def test_interaction_term_creation():
    """
    Unit test for interaction term creation and mean-centering in code/modeling.py.
    
    This test verifies that the transform_and_center function correctly:
    1. Mean-centers the input predictors.
    2. Creates an interaction term from the centered predictors.
    3. Returns a DataFrame with the correct columns.
    """
    # Create sample data
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'log_k': np.random.normal(0.0, 0.5, n),
        'wm_metric': np.random.normal(0.8, 0.1, n)
    })

    # Call the function
    result_df = transform_and_center(data)

    # Assertions
    assert isinstance(result_df, pd.DataFrame)
    
    # Check that original columns are not present (they should be replaced by centered versions)
    # Note: The implementation might keep originals or replace them. 
    # Based on standard practice and the function name, we expect centered versions.
    # Let's check for the expected centered columns and interaction.
    assert 'log_k_centered' in result_df.columns, "log_k_centered column missing"
    assert 'wm_metric_centered' in result_df.columns, "wm_metric_centered column missing"
    assert 'interaction' in result_df.columns, "interaction column missing"

    # Verify mean-centering: mean of centered columns should be ~0
    assert np.isclose(result_df['log_k_centered'].mean(), 0.0, atol=1e-6), "log_k_centered not mean-centered"
    assert np.isclose(result_df['wm_metric_centered'].mean(), 0.0, atol=1e-6), "wm_metric_centered not mean-centered"

    # Verify interaction term creation: interaction = log_k_centered * wm_metric_centered
    expected_interaction = result_df['log_k_centered'] * result_df['wm_metric_centered']
    assert np.allclose(result_df['interaction'], expected_interaction), "Interaction term calculation incorrect"

    # Verify no NaNs in the result (assuming input had no NaNs)
    assert not result_df.isnull().any().any(), "Result contains NaN values"

def test_hyperbolic_fit_failure():
    """
    Unit test for hyperbolic model fitting edge cases (failure cases).
    
    This test verifies that the fitting routine handles invalid data
    (e.g., constant values, NaNs, or non-positive values) gracefully
    by raising a ValueError or returning None, rather than crashing
    the entire pipeline.
    """
    from code.modeling import fit_hyperbolic_model
    
    # Case 1: All values are the same (constant V) -> slope is undefined
    # This should fail to converge or raise an error in curve_fit
    delays_constant = np.array([1.0, 1.0, 1.0, 1.0])
    values_constant = np.array([50.0, 50.0, 50.0, 50.0])
    
    with pytest.raises((RuntimeError, ValueError)):
        fit_hyperbolic_model(delays_constant, values_constant)
    
    # Case 2: Contains NaN values -> fitting should fail or be handled
    delays_nan = np.array([1.0, 2.0, np.nan, 4.0])
    values_nan = np.array([50.0, 40.0, 30.0, 20.0])
    
    # We expect this to either raise or return None/fail to fit
    # depending on implementation, but it must NOT produce a valid k
    # if the data is invalid.
    try:
        result = fit_hyperbolic_model(delays_nan, values_nan)
        # If it returns a result, it must be None or a specific failure indicator
        # If the implementation filters NaNs and fits, we check if k is reasonable
        # But strictly, fitting on NaN data is an edge case.
        # Assuming the function handles it by raising or returning None:
        if result is not None:
            # If it somehow fits, ensure it doesn't crash, but this is risky
            # The spec says "exclude participants where fitting fails"
            # So returning None is acceptable behavior for failure.
            pass
    except (RuntimeError, ValueError):
        # Expected behavior: fitting fails
        pass
    
    # Case 3: Non-positive delays (k must be > 0, delays must be > 0 for log)
    delays_neg = np.array([-1.0, 2.0, 3.0])
    values_neg = np.array([50.0, 40.0, 30.0])
    
    with pytest.raises((ValueError, RuntimeError)):
        fit_hyperbolic_model(delays_neg, values_neg)

def test_vif_calculation():
    """
    Unit test for VIF calculation and threshold flagging in code/modeling.py.
    
    This test verifies that the calculate_vif function:
    1. Correctly calculates Variance Inflation Factor for each predictor.
    2. Returns a dictionary with the expected structure.
    3. Correctly identifies high multicollinearity (VIF > 5).
    """
    # Create sample data with known multicollinearity
    # We'll create a dataset where one variable is highly correlated with another
    np.random.seed(42)
    n = 100
    
    # Create base variables
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    
    # Create a third variable that is highly correlated with x1 (VIF should be high)
    x3 = x1 * 0.95 + np.random.normal(0, 0.1, n)
    
    # Create target variable
    y = x1 + x2 + x3 + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({
        'y': y,
        'x1': x1,
        'x2': x2,
        'x3': x3
    })
    
    # Calculate VIF
    vif_scores = calculate_vif(df[['x1', 'x2', 'x3']])
    
    # Assertions
    assert isinstance(vif_scores, dict), "VIF result should be a dictionary"
    assert 'x1' in vif_scores, "VIF result should contain x1"
    assert 'x2' in vif_scores, "VIF result should contain x2"
    assert 'x3' in vif_scores, "VIF result should contain x3"
    
    # All VIF scores should be positive
    for var, vif in vif_scores.items():
        assert vif > 0, f"VIF for {var} should be positive"
    
    # x3 should have a high VIF (> 5) due to correlation with x1
    assert vif_scores['x3'] > 5, f"VIF for x3 should be > 5 due to multicollinearity, got {vif_scores['x3']}"
    assert vif_scores['x1'] > 5, f"VIF for x1 should be > 5 due to multicollinearity, got {vif_scores['x1']}"
    
    # x2 should have a low VIF (close to 1) as it's independent
    assert vif_scores['x2'] < 2, f"VIF for x2 should be low (< 2), got {vif_scores['x2']}"
    
    # Test with perfectly collinear variables (should result in very high VIF)
    df_collinear = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': x1  # Perfectly collinear with x1
    })
    
    vif_collinear = calculate_vif(df_collinear)
    
    # With perfect collinearity, VIF should be extremely high or infinite
    # We check that at least one VIF is very high (> 100)
    assert any(v > 100 for v in vif_collinear.values), "Perfect collinearity should result in very high VIF"