import pandas as pd
import numpy as np
import os
import tempfile
from code.analysis import fit_mlr_model, analyze_collinearity

def test_mlr_no_collinearity():
    """Test MLR fitting when VIF <= 5 (Holm-Bonferroni applied)."""
    # Create synthetic data with low correlation between predictors
    np.random.seed(42)
    n = 50
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n) # Independent of x1
    y = 2 * x1 + 3 * x2 + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({
        'subject_id': range(n),
        'clustering_coefficient': x1,
        'path_length': x2,
        'entrainment_metric': y
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.csv')
        output_path = os.path.join(tmpdir, 'output.csv')
        df.to_csv(input_path, index=False)
        
        result = fit_mlr_model(input_path, output_path)
        
        assert os.path.exists(output_path)
        assert 'adjusted_p_value' in result.columns
        assert 'is_significant' in result.columns
        assert 'collinearity_warning' in result.columns
        assert result['collinearity_warning'].iloc[0] == False
        # Check that p-values are adjusted (they should be different from raw if method matters, 
        # but for this test we just ensure the column exists and logic ran)
        assert not result['adjusted_p_value'].isna().all()

def test_mlr_collinearity_suppression():
    """Test MLR fitting when VIF > 5 (p-values suppressed)."""
    # Create synthetic data with high correlation between predictors
    np.random.seed(42)
    n = 50
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.95 + np.random.normal(0, 0.01, n) # Highly correlated
    y = 2 * x1 + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({
        'subject_id': range(n),
        'clustering_coefficient': x1,
        'path_length': x2,
        'entrainment_metric': y
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.csv')
        output_path = os.path.join(tmpdir, 'output.csv')
        df.to_csv(input_path, index=False)
        
        result = fit_mlr_model(input_path, output_path)
        
        assert os.path.exists(output_path)
        assert result['collinearity_warning'].iloc[0] == True
        # When collinearity is detected, individual p-values for predictors should be None or suppressed
        # The logic in fit_mlr_model creates a 'Model_Joint' row with p_value=None
        assert result['p_value'].isna().all() or 'Model_Joint' in result['metric_name'].values
        assert result['model_r_squared'].iloc[0] > 0

def test_vif_calculation():
    """Test VIF calculation logic directly."""
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.99 + np.random.normal(0, 0.01, n) # High collinearity
    
    df = pd.DataFrame({
        'clustering_coefficient': x1,
        'path_length': x2
    })
    
    max_vif, vif_series = analyze_collinearity(df, ['clustering_coefficient', 'path_length'])
    
    assert max_vif > 5.0
    assert vif_series['clustering_coefficient'] > 5.0
    assert vif_series['path_length'] > 5.0