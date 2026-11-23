import pytest
import numpy as np
import pandas as pd
import os
from code.transformation import apply_clr

def test_clr_transform_sum_logs_zero():
    """
    Test that the sum of log-transformed columns after CLR is zero (within tolerance).
    
    Input: Taxa matrix with columns ['TaxaA', 'TaxaB', 'TaxaC'] and values 
           [[10, 10, 10], [20, 20, 20]].
    Expect: Sum of log-transformed columns to be 0 (within tolerance 1e-6).
    
    Note: This test passes if apply_clr is correctly implemented.
    """
    # Load fixture data if it exists, otherwise create inline for the test
    fixture_path = "tests/fixtures/sample_clr_taxa.csv"
    if os.path.exists(fixture_path):
        df = pd.read_csv(fixture_path)
    else:
        # Create input data as described in task T018
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

def test_clr_transform_known_values():
    """
    Test CLR transformation with specific known values to ensure correctness.
    Input: [[10, 10, 10], [20, 20, 20]]
    Expected: For row 1 (10,10,10), geometric mean is 10. log(10/10) = 0. Sum = 0.
              For row 2 (20,20,20), geometric mean is 20. log(20/20) = 0. Sum = 0.
    """
    data = {
        'TaxaA': [10, 20],
        'TaxaB': [10, 20],
        'TaxaC': [10, 20]
    }
    df = pd.DataFrame(data)
    
    result = apply_clr(df)
    
    # For uniform rows, CLR should result in zeros
    expected = pd.DataFrame({
        'TaxaA': [0.0, 0.0],
        'TaxaB': [0.0, 0.0],
        'TaxaC': [0.0, 0.0]
    })
    
    pd.testing.assert_frame_equal(result, expected)