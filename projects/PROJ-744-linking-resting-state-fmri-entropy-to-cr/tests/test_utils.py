"""
Tests for utility functions (logging, VIF, file I/O).
"""
import pytest
import pandas as pd
import numpy as np

def test_vif_calculation():
    """
    Test Variance Inflation Factor calculation.
    """
    # Create a dataset with some collinearity
    np.random.seed(42)
    x1 = np.random.randn(100)
    x2 = x1 * 0.9 + np.random.randn(100) * 0.1  # Highly correlated
    df = pd.DataFrame({"x1": x1, "x2": x2})
    
    try:
        from code.utils import calculate_vif
        vif_values = calculate_vif(df)
        
        # x2 should have VIF > 5 due to correlation
        assert vif_values['x2'] > 5
    except ImportError:
        pytest.skip("code/utils.py not yet implemented")

def test_file_io_helpers():
    """
    Test file writing and reading utilities.
    """
    try:
        from code.utils import write_to_csv, read_csv
        import os
        
        test_data = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        path = "tests/fixtures/test_io.csv"
        
        write_to_csv(test_data, path)
        assert os.path.exists(path)
        
        loaded = read_csv(path)
        assert loaded.equals(test_data)
        
        os.remove(path)
    except ImportError:
        pytest.skip("code/utils.py not yet implemented")
