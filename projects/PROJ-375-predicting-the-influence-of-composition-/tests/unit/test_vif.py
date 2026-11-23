import pytest
import pandas as pd
import numpy as np
import logging
from features.descriptors import extract_descriptors, _calculate_vif

# Configure logging to capture warnings
logging.basicConfig(level=logging.WARNING)

def test_vif_retention_on_high_collinearity():
    """
    Test that size_mismatch is retained even if VIF > threshold.
    This tests the T017 constraint: "DO NOT exclude size_mismatch".
    """
    # Create a dataset where mean_atomic_radius and size_mismatch are highly correlated
    # size_mismatch is mathematically related to mean_atomic_radius, but we can construct
    # a scenario where they are perfectly correlated or nearly so to trigger the warning.
    # In real data, they are often correlated.
    
    # Mock data: 100 rows of synthetic composition-like data
    # We'll construct a dataframe that has the required columns after extraction
    # to test the VIF logic directly, or we can test the function behavior.
    
    # Since extract_descriptors parses formulas, let's create a set of formulas
    # that result in high correlation.
    # Actually, the VIF check happens inside extract_descriptors.
    # We need to ensure the function returns the dataframe WITH the columns.
    
    # Let's create a simple test dataframe with pre-calculated descriptors to isolate the VIF logic
    # if we were testing _calculate_vif, but we need to test extract_descriptors.
    
    # To force high VIF in a small test, we can manipulate the data or rely on the natural correlation.
    # However, the requirement is: IF VIF > 5.0, LOG WARNING and RETAIN.
    
    # Let's create a dataset that naturally has high correlation.
    # Zr-based alloys usually have specific radii.
    # We'll just check that the columns exist in the output.
    
    data = {
        'composition': ['Zr50Cu40Al10', 'Zr60Cu30Al10', 'Zr70Cu20Al10', 'Pd40Ni40P20', 'Pd50Ni30P20', 
                        'Fe80B20', 'Fe75B25', 'Fe70B30', 'Cu50Zr50', 'Cu60Zr40']
    }
    df = pd.DataFrame(data)
    
    # Run extraction
    result = extract_descriptors(df, vif_threshold=5.0)
    
    # Assert that both columns exist (retention)
    assert 'mean_atomic_radius' in result.columns
    assert 'size_mismatch' in result.columns
    
    # Assert that VIF was calculated and logged (we can't easily assert the log without a handler,
    # but we can assert the logic didn't crash or drop columns).
    
    # Check that VIF calculation didn't remove the column
    assert result['size_mismatch'].notna().all()

def test_vif_threshold_config():
    """
    Test that the VIF threshold can be overridden.
    """
    data = {
        'composition': ['Zr50Cu40Al10'] * 10
    }
    df = pd.DataFrame(data)
    
    # With a very low threshold, we might trigger the warning more easily if correlation exists
    result = extract_descriptors(df, vif_threshold=1.1)
    
    assert 'size_mismatch' in result.columns
    assert 'mean_atomic_radius' in result.columns

def test_vif_calculation_helper():
    """
    Test the VIF calculation helper function directly.
    """
    # Create a dataframe with two perfectly correlated columns (VIF should be infinite)
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [2, 4, 6, 8, 10] # Perfectly correlated
    })
    
    vif_results = _calculate_vif(df, ['A', 'B'])
    
    # VIF for B (regressed on A) should be infinite
    assert 'B' in vif_results
    assert np.isinf(vif_results['B'])

def test_vif_uncorrelated():
    """
    Test VIF calculation on uncorrelated data.
    """
    np.random.seed(42)
    df = pd.DataFrame({
        'A': np.random.rand(100),
        'B': np.random.rand(100)
    })
    
    vif_results = _calculate_vif(df, ['A', 'B'])
    
    # VIF should be close to 1.0 for uncorrelated variables
    assert 1.0 <= vif_results['A'] < 2.0
    assert 1.0 <= vif_results['B'] < 2.0