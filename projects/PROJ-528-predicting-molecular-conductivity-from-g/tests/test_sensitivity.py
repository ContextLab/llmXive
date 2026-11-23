import pytest
import pandas as pd
import numpy as np
import os
import sys
import json
import tempfile

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.analysis import filter_outliers, run_sensitivity_analysis
from code.config import SEED

def test_filter_outliers_basic():
    """Test that filter_outliers correctly removes outliers based on z-score."""
    data = {
        'target': [1.0, 2.0, 3.0, 4.0, 5.0, 100.0] # 100 is an outlier
    }
    df = pd.DataFrame(data)
    
    # Threshold 3.0 should keep most, maybe drop 100 if it's > 3 std away
    # Mean ~ 19.16, Std ~ 39. Z for 100: (100-19)/39 ~ 2.0 -> kept
    # Let's construct a clearer case
    data = {
        'target': [1.0, 1.0, 1.0, 1.0, 1.0, 10.0]
    }
    df = pd.DataFrame(data)
    # Mean = 2.33, Std = 3.4. Z for 10 = (10-2.33)/3.4 = 2.25 -> kept at 3.0
    # Let's use a very extreme one
    data = {
        'target': [1.0, 1.0, 1.0, 1.0, 1.0, 1000.0]
    }
    df = pd.DataFrame(data)
    
    filtered = filter_outliers(df, 'target', 3.0)
    # 1000 is definitely an outlier here
    assert len(filtered) < len(df)

def test_run_sensitivity_analysis_structure():
    """Test that run_sensitivity_analysis returns the expected structure."""
    # Create dummy data
    n = 100
    data = {
        'smiles': ['CC' for _ in range(n)],
        'status': ['valid' for _ in range(n)],
        'feature1': np.random.randn(n),
        'feature2': np.random.randn(n),
        'log_conductivity': np.random.randn(n)
    }
    df = pd.DataFrame(data)
    
    result = run_sensitivity_analysis(df, 'log_conductivity', ['feature1', 'feature2'], thresholds=[2.5, 3.0])
    
    assert 'thresholds' in result
    assert 'r2_scores' in result
    assert 'kruskal_statistic' in result
    assert 'p_value' in result
    assert 'model_hashes' in result
    assert len(result['r2_scores']) == 2