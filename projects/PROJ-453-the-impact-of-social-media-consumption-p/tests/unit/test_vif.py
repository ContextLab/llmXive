"""
Unit tests for VIF calculation.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.config import RANDOM_SEED

def test_vif_calculation_correctness():
    """Test VIF calculation with known collinearity."""
    np.random.seed(RANDOM_SEED)
    n = 100
    x1 = np.random.randn(n)
    noise = np.random.randn(n) * 0.1
    x2 = x1 * 2 + noise  # High collinearity
    
    df = pd.DataFrame({'x1': x1, 'x2': x2})
    
    # Calculate VIF manually
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif_x2 = variance_inflation_factor(df.values, 1)
    
    assert vif_x2 > 5, f"Expected VIF > 5 for collinear variable, got {vif_x2}"
