import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add project root to path if necessary
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.analysis import build_multivariate_model, check_significance, calculate_vif

def test_check_significance():
    """Test the logic for checking statistical significance in correlation results."""
    data = {
        'descriptor': ['bond_variance', 'angle_variance', 'dihedral_variance'],
        'correlation': [0.5, 0.1, 0.8],
        'p_value': [0.03, 0.2, 0.01]
    }
    df = pd.DataFrame(data)
    
    sig_vars = check_significance(df, alpha=0.05)
    assert 'bond_variance' in sig_vars
    assert 'angle_variance' not in sig_vars
    assert 'dihedral_variance' in sig_vars

def test_calculate_vif():
    """Test VIF calculation."""
    # Create a simple dataframe with some correlation
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = x1 * 0.9 + np.random.randn(n) * 0.1 # Highly correlated
    x3 = np.random.randn(n)
    
    df = pd.DataFrame({'x1': x1, 'x2': x2, 'x3': x3})
    
    vif_results = calculate_vif(df, ['x1', 'x2', 'x3'])
    
    assert 'x1' in vif_results
    assert 'x2' in vif_results
    # x1 and x2 should have high VIF
    assert vif_results['x1'] > 5.0
    assert vif_results['x2'] > 5.0
    # x3 should be low
    assert vif_results['x3'] < 5.0

def test_build_multivariate_model_basic():
    """Test basic model building with mandatory features."""
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        'dihedral_variance': np.random.randn(n),
        'logP': np.random.randn(n),
        'MW': np.random.randn(n) * 100 + 300,
        'PSA': np.random.randn(n) * 10 + 50,
        'logPapp': np.random.randn(n)
    })
    
    results = build_multivariate_model(df, primary_pred='dihedral_variance', confounders=['logP', 'MW', 'PSA'])
    
    assert 'coefficients' in results
    assert 'metrics' in results
    assert 'dihedral_variance' in results['included_predictors']
    assert 'logP' in results['included_predictors']
    assert 'MW' in results['included_predictors']
    assert 'PSA' in results['included_predictors']
    assert results['metrics']['rsquared'] >= 0.0
    assert results['metrics']['rsquared'] <= 1.0

def test_build_multivariate_model_vif_pruning():
    """Test that VIF pruning removes collinear features."""
    np.random.seed(42)
    n = 200
    x1 = np.random.randn(n)
    x2 = x1 * 0.95 # Highly correlated
    
    df = pd.DataFrame({
        'dihedral_variance': x1,
        'logP': x2,
        'MW': np.random.randn(n),
        'PSA': np.random.randn(n),
        'bond_variance': x1 * 0.95, # Highly correlated with dihedral
        'logPapp': np.random.randn(n)
    })
    
    # Create dummy correlation results indicating bond_variance is significant
    corr_data = {
        'descriptor': ['bond_variance'],
        'p_value': [0.01]
    }
    corr_df = pd.DataFrame(corr_data)
    
    results = build_multivariate_model(
        df, 
        primary_pred='dihedral_variance', 
        confounders=['logP', 'MW', 'PSA'],
        correlation_results=corr_df
    )
    
    # bond_variance should be excluded if VIF > 5
    assert 'bond_variance' not in results['included_predictors'] or results['vif']['bond_variance'] < 5.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])