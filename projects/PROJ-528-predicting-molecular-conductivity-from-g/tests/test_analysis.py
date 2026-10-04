import pytest
import numpy as np
import pandas as pd
from code.analysis import calculate_vif
from code.feature_analysis import apply_bh_correction

def test_vif_calculation():
    """
    Assert that calculate_vif(X) returns a dictionary with expected VIF scores
    for a known feature matrix X.
    
    We construct a simple matrix where:
    - Feature 'a' and 'b' are perfectly collinear (b = 2*a).
    - Feature 'c' is independent.
    
    Expected behavior:
    - VIF for 'a' should be very high (infinity or large number) due to collinearity.
    - VIF for 'b' should be very high.
    - VIF for 'c' should be 1.0 (no collinearity).
    """
    # Create a deterministic dataset
    np.random.seed(42)
    n = 100
    a = np.random.rand(n)
    b = 2 * a  # Perfectly collinear with 'a'
    c = np.random.rand(n)  # Independent
    
    df = pd.DataFrame({
        'a': a,
        'b': b,
        'c': c
    })
    
    # Calculate VIF
    vif_scores = calculate_vif(df)
    
    # Assert return type
    assert isinstance(vif_scores, dict), "calculate_vif must return a dictionary"
    assert set(vif_scores.keys()) == {'a', 'b', 'c'}, "Keys must match feature names"
    
    # Assert specific values
    # 'c' is independent, so VIF should be exactly 1.0
    assert vif_scores['c'] == 1.0, f"VIF for independent feature 'c' should be 1.0, got {vif_scores['c']}"
    
    # 'a' and 'b' are collinear. VIF will be very high (often inf or large float).
    # We assert they are significantly larger than 1.0 (e.g., > 1000) to confirm collinearity detection.
    assert vif_scores['a'] > 1000, f"VIF for collinear feature 'a' should be high, got {vif_scores['a']}"
    assert vif_scores['b'] > 1000, f"VIF for collinear feature 'b' should be high, got {vif_scores['b']}"

def test_bh_correction():
    """
    Assert that apply_bh_correction(p_values) returns adjusted p-values matching
    the expected output for a known input array.
    
    Benjamini-Hochberg procedure:
    1. Sort p-values: p_(1) <= p_(2) <= ... <= p_(m)
    2. Calculate adjusted p-values: p_adj_(i) = min( (m/i) * p_(i), 1.0 )
    3. Ensure monotonicity (cumulative min from the end)
    
    Test case:
    Input: [0.05, 0.01, 0.03, 0.10]
    Sorted: [0.01, 0.03, 0.05, 0.10] (indices 1, 2, 3, 4)
    m = 4
    
    Calculations:
    i=1: 0.01 * (4/1) = 0.04
    i=2: 0.03 * (4/2) = 0.06
    i=3: 0.05 * (4/3) = 0.0667
    i=4: 0.10 * (4/4) = 0.10
    
    Monotonicity check (from end):
    idx 4: 0.10
    idx 3: min(0.0667, 0.10) = 0.0667
    idx 2: min(0.06, 0.0667) = 0.06
    idx 1: min(0.04, 0.06) = 0.04
    
    Mapping back to original order:
    0.05 (orig idx 0) -> rank 3 -> 0.0667
    0.01 (orig idx 1) -> rank 1 -> 0.04
    0.03 (orig idx 2) -> rank 2 -> 0.06
    0.10 (orig idx 3) -> rank 4 -> 0.10
    
    Expected: [0.0667, 0.04, 0.06, 0.10] (approx)
    """
    p_values = np.array([0.05, 0.01, 0.03, 0.10])
    
    adjusted = apply_bh_correction(p_values)
    
    # Assert return type and shape
    assert isinstance(adjusted, np.ndarray), "apply_bh_correction must return a numpy array"
    assert adjusted.shape == p_values.shape, "Output shape must match input shape"
    
    # Assert values are within [0, 1]
    assert np.all(adjusted >= 0.0), "Adjusted p-values must be >= 0"
    assert np.all(adjusted <= 1.0), "Adjusted p-values must be <= 1"
    
    # Verify specific values (with tolerance for floating point)
    # Expected: [0.06666667, 0.04, 0.06, 0.1]
    expected = np.array([0.06666667, 0.04, 0.06, 0.1])
    
    np.testing.assert_almost_equal(adjusted, expected, decimal=5, 
                                   err_msg="BH corrected p-values do not match expected values")
    
    # Verify monotonicity property (sorted adjusted p-values should be non-decreasing)
    sorted_indices = np.argsort(p_values)
    sorted_adjusted = adjusted[sorted_indices]
    assert np.all(np.diff(sorted_adjusted) >= -1e-9), "Adjusted p-values must be monotonically non-decreasing when sorted by original p-value"
    
    # Verify that adjusted p-values are always >= original p-values
    assert np.all(adjusted >= p_values - 1e-9), "Adjusted p-values must be >= original p-values"