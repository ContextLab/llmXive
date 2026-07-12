import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analyze import calculate_vif

def test_vif_calculation():
    """Test VIF calculation with known data"""
    # Create a simple dataset with some correlation
    np.random.seed(42)
    n = 100
    
    # Create correlated variables
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.8 + np.random.normal(0, 0.2, n)  # Correlated with x1
    
    df = pd.DataFrame({
        'library_size': x1,
        'total_redundancy': x2
    })
    
    # Calculate VIF
    vif_results = calculate_vif(df, ['library_size', 'total_redundancy'])
    
    # Both VIFs should be > 1 (indicating some correlation)
    assert 'library_size' in vif_results
    assert 'total_redundancy' in vif_results
    assert vif_results['library_size'] > 1.0
    assert vif_results['total_redundancy'] > 1.0
    
    # With moderate correlation (0.8), VIF should be around 1/(1-0.8^2) = 2.78
    # Allow some tolerance due to noise
    assert 1.5 < vif_results['library_size'] < 5.0
    assert 1.5 < vif_results['total_redundancy'] < 5.0

def test_vif_threshold_check():
    """Test that VIF < 5.0 passes the threshold check"""
    # Create data with low correlation
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)  # Uncorrelated
    
    df = pd.DataFrame({
        'library_size': x1,
        'total_redundancy': x2
    })
    
    vif_results = calculate_vif(df, ['library_size', 'total_redundancy'])
    
    # With uncorrelated variables, VIF should be close to 1
    assert vif_results['library_size'] < 5.0
    assert vif_results['total_redundancy'] < 5.0

def test_vif_missing_columns():
    """Test VIF calculation with missing columns"""
    df = pd.DataFrame({
        'library_size': [1, 2, 3],
        'other_col': [4, 5, 6]
    })
    
    with pytest.raises(ValueError):
        calculate_vif(df, ['library_size', 'total_redundancy'])

def test_vif_with_nan():
    """Test VIF calculation with NaN values"""
    df = pd.DataFrame({
        'library_size': [1, 2, np.nan, 4],
        'total_redundancy': [1, 2, 3, np.nan]
    })
    
    # Should handle NaN by dropping rows
    vif_results = calculate_vif(df, ['library_size', 'total_redundancy'])
    
    # Should still produce results if enough valid data remains
    assert len(vif_results) == 2
    assert all(isinstance(v, float) for v in vif_results.values())

if __name__ == "__main__":
    pytest.main([__file__, "-v"])