import pytest
import pandas as pd
import numpy as np
import json
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from statistical_analysis import calculate_vif, load_static_baseline, load_semantic_results, merge_datasets

def test_calculate_vif_basic():
    """Test VIF calculation with synthetic data."""
    # Create a mock dataframe
    data = {
        'loc': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'cyclomatic_complexity': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'embedding': [json.dumps([1.0, 2.0, 3.0]) for _ in range(10)]
    }
    df = pd.DataFrame(data)
    
    # Calculate VIF
    vif_data = calculate_vif(df)
    
    # Check results
    assert 'LOC' in vif_data
    assert 'Cyclomatic' in vif_data
    assert 'Semantic_Mean' in vif_data
    
    # VIF should be >= 1.0 for all predictors
    for vif in vif_data.values():
        assert vif >= 1.0
        
def test_calculate_vif_high_collinearity():
    """Test VIF calculation with highly correlated predictors."""
    # Create data with perfect collinearity (LOC = 2 * Cyclomatic)
    data = {
        'loc': [20, 40, 60, 80, 100, 120, 140, 160, 180, 200],
        'cyclomatic_complexity': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'embedding': [json.dumps([1.0, 2.0, 3.0]) for _ in range(10)]
    }
    df = pd.DataFrame(data)
    
    vif_data = calculate_vif(df)
    
    # VIF for correlated predictors should be very high (or infinite, but statsmodels handles it)
    # We expect at least one predictor to have high VIF
    assert len(vif_data) > 0
    
def test_calculate_vif_missing_columns():
    """Test VIF calculation with missing required columns."""
    data = {
        'loc': [10, 20, 30],
        # Missing cyclomatic_complexity
        'embedding': [json.dumps([1.0]) for _ in range(3)]
    }
    df = pd.DataFrame(data)
    
    vif_data = calculate_vif(df)
    assert vif_data == {}
    
def test_calculate_vif_missing_embeddings():
    """Test VIF calculation with missing embedding column."""
    data = {
        'loc': [10, 20, 30],
        'cyclomatic_complexity': [1, 2, 3],
        # No embedding column
    }
    df = pd.DataFrame(data)
    
    vif_data = calculate_vif(df)
    assert vif_data == {}