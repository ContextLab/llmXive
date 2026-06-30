"""
Additional integration test to ensure MMD works with the full synthetic data pipeline.
"""
import numpy as np
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from synthetic_data import generate_synthetic_ili_series
from test_mmd import mmd_statistic, mmd_permutation_test

def test_mmd_with_synthetic_pipeline():
    """
    Test MMD detection using the full synthetic data generation pipeline.
    Ensures that the synthetic data generator and MMD detector work together.
    """
    np.random.seed(42)
    
    # Generate data with known shift
    n_weeks = 200
    shift_week = 100
    shift_magnitude = 1.5
    
    data = generate_synthetic_ili_series(
        n_weeks=n_weeks,
        seed=42,
        include_missing=False,
        include_constant=False,
        include_outliers=False,
        shift_start=shift_week,
        shift_magnitude=shift_magnitude
    )
    
    # Define windows around the shift point
    window_size = 12
    before_shift = data[shift_week - window_size:shift_week].values.reshape(-1, 1)
    after_shift = data[shift_week:shift_week + window_size].values.reshape(-1, 1)
    
    # Compute MMD
    mmd_val, p_val, _ = mmd_permutation_test(
        before_shift, 
        after_shift, 
        n_permutations=100, 
        seed=42
    )
    
    # Verify detection
    assert p_val < 0.1, f"Should detect shift with p={p_val}"
    assert mmd_val > 0.1, f"MMD should be positive, got {mmd_val}"
    
    print(f"✓ Integration test passed: Detected shift at week {shift_week} with MMD={mmd_val:.4f} (p={p_val:.3f})")

if __name__ == "__main__":
    test_mmd_with_synthetic_pipeline()
    print("All integration tests passed!")