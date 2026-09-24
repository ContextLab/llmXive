import pytest
import pandas as pd
import numpy as np
from code_03_model import calculate_vif

def test_vif_calculation_correctness():
    """Test VIF calculation correctness."""
    # Create data with known collinearity
    np.random.seed(42)
    df = pd.DataFrame({
        'x1': np.random.randn(100),
        'x2': np.random.randn(100),
        'x3': np.random.randn(100)
    })
    
    vif_scores = calculate_vif(df, ['x1', 'x2', 'x3'])
    
    # VIF should be >= 1
    for var, vif in vif_scores.items():
        assert vif >= 1.0, f"VIF for {var} should be >= 1"
