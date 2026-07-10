"""
Unit tests for VIF calculation and reduction logic in preprocess.py.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.pipelines.preprocess import calculate_vif, process_vif_reduction

def test_calculate_vif_simple():
    """Test VIF calculation on a simple dataset."""
    # Create a dataframe with two perfectly correlated columns
    data = {
        'var1': [1.0, 2.0, 3.0, 4.0, 5.0],
        'var2': [2.0, 4.0, 6.0, 8.0, 10.0], # Perfect correlation
        'var3': [1.0, 1.0, 1.0, 1.0, 1.0]   # Constant (might cause issues)
    }
    df = pd.DataFrame(data)
    
    vif_df = calculate_vif(df)
    
    assert not vif_df.empty
    assert 'variable' in vif_df.columns
    assert 'vif' in vif_df.columns
    
    # var1 and var2 should have high VIF (infinity or very large)
    # var3 (constant) might be excluded or have NaN/Inf depending on implementation
    logger = pytest.importorskip('src.utils.logging').get_logger(__name__)
    logger.info(f"VIF Results:\n{vif_df}")

def test_process_vif_reduction():
    """Test that process_vif_reduction removes high VIF variables."""
    # Create data where var1 and var2 are highly correlated
    np.random.seed(42)
    base = np.random.rand(50)
    data = {
        'var1': base,
        'var2': base * 2 + np.random.normal(0, 0.01, 50), # Highly correlated
        'var3': np.random.rand(50), # Independent
        'sample_id': [f's{i}' for i in range(50)]
    }
    df = pd.DataFrame(data)
    
    cleaned_df, removed_df = process_vif_reduction(df, threshold=5.0)
    
    # One of var1 or var2 should be removed
    remaining_cols = cleaned_df.columns.tolist()
    assert 'sample_id' in remaining_cols
    assert 'var3' in remaining_cols
    
    # Check that we didn't remove too much
    assert len(remaining_cols) >= 2 
    
    # Check log
    assert not removed_df.empty
    assert 'variable' in removed_df.columns
    assert 'vif' in removed_df.columns

def test_vif_threshold_no_removal():
    """Test that no variables are removed if VIF is below threshold."""
    # Create independent variables
    np.random.seed(42)
    data = {
        'var1': np.random.rand(50),
        'var2': np.random.rand(50),
        'var3': np.random.rand(50),
        'sample_id': [f's{i}' for i in range(50)]
    }
    df = pd.DataFrame(data)
    
    cleaned_df, removed_df = process_vif_reduction(df, threshold=5.0)
    
    # No variables should be removed
    assert len(removed_df) == 0
    # All original numeric cols should remain
    assert set(cleaned_df.columns) == set(df.columns)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
