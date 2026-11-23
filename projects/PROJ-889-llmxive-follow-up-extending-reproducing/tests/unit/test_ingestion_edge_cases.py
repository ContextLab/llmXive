import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Add code to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingestion import compute_divergence_gap, compute_derivative_and_zscore

def test_zero_variance_zscore():
    """
    Test that zero-variance G(t) results in z-score of 0.
    """
    data = {
        'step': [1, 2, 3, 4, 5],
        't': [1.0, 2.0, 3.0, 4.0, 5.0],
        'J_biased': [10.0, 10.0, 10.0, 10.0, 10.0],
        'J_unbiased': [5.0, 5.0, 5.0, 5.0, 5.0],
    }
    df = pd.DataFrame(data)
    
    # Compute G(t)
    df = compute_divergence_gap(df)
    # G_t should be 5.0 for all rows
    assert all(df['G_t'] == 5.0)
    
    # Compute derivative and z-score
    # Window size default is 20, but we have 5 samples.
    # std of [5, 5, 5, 5, 5] is 0.
    result = compute_derivative_and_zscore(df, window=5)
    
    # Check that z_G_t is 0 for all rows (since variance is 0)
    assert all(result['z_G_t'] == 0.0), f"Expected z-score 0 for zero variance, got {result['z_G_t'].values}"

def test_missing_timesteps_interpolation():
    """
    Test that missing timesteps (NaN in G_t) are interpolated.
    """
    data = {
        'step': [1, 2, 3, 4, 5],
        't': [1.0, 2.0, 3.0, 4.0, 5.0],
        'J_biased': [10.0, 10.0, 10.0, 10.0, 10.0],
        'J_unbiased': [5.0, 6.0, np.nan, 8.0, 9.0], # Gap at step 3
    }
    df = pd.DataFrame(data)
    
    df = compute_divergence_gap(df)
    # G_t: 5, 4, NaN, 2, 1
    
    result = compute_derivative_and_zscore(df, window=5)
    
    # Step 3 should be interpolated. 
    # Linear interpolation between 4 (step 2) and 2 (step 4) -> 3.0
    expected_g_interp_step3 = 3.0
    actual_g_interp_step3 = result.loc[result['step'] == 3, 'G_t_interp'].values[0]
    
    assert np.isclose(actual_g_interp_step3, expected_g_interp_step3), \
        f"Interpolation failed. Expected {expected_g_interp_step3}, got {actual_g_interp_step3}"

def test_missing_timesteps_skipped_derivative():
    """
    Test that if a row cannot be interpolated (e.g., all neighbors missing), 
    derivative is NaN.
    """
    data = {
        'step': [1, 2, 3, 4, 5],
        't': [1.0, 2.0, 3.0, 4.0, 5.0],
        'J_biased': [10.0, 10.0, 10.0, 10.0, 10.0],
        'J_unbiased': [5.0, np.nan, np.nan, np.nan, 9.0], # Large gap
    }
    df = pd.DataFrame(data)
    
    df = compute_divergence_gap(df)
    # G_t: 5, NaN, NaN, NaN, 1
    
    result = compute_derivative_and_zscore(df, window=5)
    
    # Steps 2, 3, 4 should be NaN for G_t_interp and thus dG_t/z_G_t
    # Step 1 and 5 should have values (if window allows)
    
    # Check step 2
    step2 = result.loc[result['step'] == 2]
    assert pd.isna(step2['G_t_interp'].values[0]), "Step 2 should remain NaN"
    assert pd.isna(step2['dG_t'].values[0]), "Step 2 derivative should be NaN"
    
    # Check step 3
    step3 = result.loc[result['step'] == 3]
    assert pd.isna(step3['G_t_interp'].values[0]), "Step 3 should remain NaN"
    assert pd.isna(step3['dG_t'].values[0]), "Step 3 derivative should be NaN"

def test_single_sample_window():
    """
    Test behavior with a single sample (min_periods=1).
    """
    data = {
        'step': [1],
        't': [1.0],
        'J_biased': [10.0],
        'J_unbiased': [5.0],
    }
    df = pd.DataFrame(data)
    
    df = compute_divergence_gap(df)
    result = compute_derivative_and_zscore(df, window=5)
    
    # With one sample, std is NaN (or 0 depending on implementation, pandas std is NaN for n=1)
    # Our logic sets z-score to 0 if std is NaN or 0.
    assert result['z_G_t'].values[0] == 0.0, "Single sample z-score should be 0"
    assert pd.isna(result['dG_t'].values[0]), "Single sample derivative should be NaN"
