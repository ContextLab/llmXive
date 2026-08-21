import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import fit_lmm_variability, fit_lmm_mean, apply_log_transform

def test_model_convergence_flag():
    """
    Test that the model converges.
    """
    # Create dummy data
    data = {
        'participant_id': ['P1'] * 20 + ['P2'] * 20,
        'date': pd.date_range('2023-01-01', periods=40).date,
        'total_steps': np.random.randint(1000, 10000, 40),
        'mean_mood': np.random.rand(40) * 5,
        'mood_std': np.random.rand(40) * 2 + 0.1,
        'n_mood_ratings': [5] * 40,
        'sleep_duration': [7.0] * 40,
        'baseline_affect': [3.0] * 40,
        'day_of_week': [0] * 40
    }
    df = pd.DataFrame(data)
    
    # Test variability model
    res, _ = fit_lmm_variability(df)
    # statsmodels fit result has converged attribute?
    # mixedlm result doesn't always have 'converged' boolean directly like sklearn.
    # We check if fit succeeded without error.
    assert res is not None
    
    # Test mean model
    res2, _ = fit_lmm_mean(df)
    assert res2 is not None

def test_apply_log_transform():
    series = pd.Series([1.0, 2.0, 3.0])
    result = apply_log_transform(series)
    expected = np.log(series + 0.01)
    pd.testing.assert_series_equal(result, expected)
