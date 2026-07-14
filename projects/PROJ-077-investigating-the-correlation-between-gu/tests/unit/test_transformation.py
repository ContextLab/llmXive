import pytest
import numpy as np
import pandas as pd
from code.transformation import apply_clr

def test_clr_transform_sum_logs_zero():
    """
    Test that the sum of log-transformed columns after CLR is zero (within tolerance).
    
    Input: Taxa matrix with columns ['TaxaA', 'TaxaB', 'TaxaC'] and values 
           [[10, 10, 10], [20, 20, 20]].
    Expect: Sum of log-transformed columns to be 0 (within tolerance 1e-6).
    
    Note: This is a failing test stub until apply_clr is implemented.
    """
    # Create input data
    data = {
        'TaxaA': [10, 20],
        'TaxaB': [10, 20],
        'TaxaC': [10, 20]
    }
    df = pd.DataFrame(data)
    
    # Apply CLR transformation
    clr_result = apply_clr(df)
    
    # Calculate sum of log-transformed columns for each row
    # After CLR, the sum of log(x_i / geometric_mean) should be 0 for each row
    log_sum = clr_result.sum(axis=1)
    
    # Assert that the sum is zero within tolerance
    np.testing.assert_allclose(log_sum, 0, atol=1e-6)
    
    # Also verify that the output has the same shape as input
    assert clr_result.shape == df.shape
