import pytest
import pandas as pd
import numpy as np
from code.analysis.modeling import calculate_vif, residualize_column, apply_residualization_strategy

def test_calculate_vif_low():
    """Test VIF calculation on data with low multicollinearity."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'x1': np.random.normal(0, 1, n),
        'x2': np.random.normal(0, 1, n),
        'x3': np.random.normal(0, 1, n)
    })
    
    vif_results = calculate_vif(df)
    
    # VIF should be close to 1.0 for uncorrelated variables
    for vif in vif_results.values():
        assert 0.9 < vif < 1.5, f"VIF {vif} is unexpectedly high for uncorrelated data"

def test_calculate_vif_high():
    """Test VIF calculation on data with high multicollinearity."""
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.95 + np.random.normal(0, 0.1, n) # Highly correlated with x1
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2
    })
    
    vif_results = calculate_vif(df)
    
    # VIF should be significantly > 1.0
    assert vif_results['x1'] > 5.0, "VIF for x1 should be high"
    assert vif_results['x2'] > 5.0, "VIF for x2 should be high"

def test_residualize_column():
    """Test residualization of a column against a predictor."""
    np.random.seed(42)
    n = 50
    x = np.random.normal(0, 1, n)
    y = 2 * x + np.random.normal(0, 0.5, n) # y depends on x
    
    df = pd.DataFrame({'x': x, 'y': y})
    
    df_resid, r_sq = residualize_column(df, 'y', 'x')
    
    # Check that residualized column exists
    assert 'y_resid' in df_resid.columns
    
    # Check that residuals are uncorrelated with x (approximately)
    corr = df_resid['y_resid'].corr(df_resid['x'])
    assert abs(corr) < 0.1, "Residuals should be uncorrelated with predictor"
    
    # Check R-squared is high because y depends on x
    assert r_sq > 0.5, "R-squared should be high for dependent variables"

def test_apply_residualization_strategy():
    """Test the full residualization strategy workflow."""
    np.random.seed(42)
    n = 100
    ace = np.random.normal(0, 1, n)
    age = ace * 0.9 + np.random.normal(0, 0.1, n) # Highly correlated
    sex = np.random.randint(0, 2, n)
    
    df = pd.DataFrame({
        'ACE_score': ace,
        'age': age,
        'sex': sex
    })
    
    # Simulate VIF results indicating high VIF for age
    vif_results = {'age': 10.0, 'sex': 1.2}
    
    df_new = apply_residualization_strategy(df, 'ACE_score', vif_results)
    
    # Check that residualized column was added
    assert 'ACE_score_resid' in df_new.columns
    
    # Check that original ACE_score is still there
    assert 'ACE_score' in df_new.columns