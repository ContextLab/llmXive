import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling import run_permutation_test, fit_mixed_model

@pytest.fixture
def sample_user_track_data():
    """
    Create a synthetic dataset for testing the permutation test.
    """
    np.random.seed(42)
    n_users = 50
    n_tracks = 20
    
    # Create user-track pairs
    user_ids = np.repeat(range(n_users), n_tracks)
    track_ids = np.tile(range(n_tracks), n_users)
    
    # Simulate exposure scores (constant per track)
    track_scores = np.random.uniform(0, 1, n_tracks)
    exposure_scores = track_scores[track_ids]
    
    # Simulate popularity (constant per track)
    popularity = np.random.uniform(0.1, 0.9, n_tracks)
    popularity_scores = popularity[track_ids]
    
    # Simulate outcome: mean_vividness = 0.5 + 0.3 * exposure + noise
    # This creates a true positive effect
    noise = np.random.normal(0, 0.1, len(user_ids))
    vividness = 0.5 + 0.3 * exposure_scores + noise
    
    df = pd.DataFrame({
        'user_id': user_ids,
        'track_id': track_ids,
        'residualized_exposure_score': exposure_scores,
        'overall_popularity_score': popularity_scores,
        'mean_vividness': vividness
    })
    
    return df

def test_permutation_test_structure(sample_user_track_data):
    """
    Test that the permutation test runs and returns the expected structure.
    """
    result = run_permutation_test(
        sample_user_track_data,
        outcome='mean_vividness',
        predictor='residualized_exposure_score',
        popularity='overall_popularity_score',
        n_permutations=50, # Small number for speed
        seed=123
    )
    
    assert 'observed_statistic' in result
    assert 'null_distribution' in result
    assert 'p_value' in result
    assert 'n_permutations' in result
    
    # Check that null distribution has the expected length
    assert len(result['null_distribution']) == 50
    
    # Check p-value is between 0 and 1
    assert 0.0 <= result['p_value'] <= 1.0

def test_permutation_p_value_significance(sample_user_track_data):
    """
    Test that with a strong effect and enough permutations, we get a low p-value.
    Note: With only 50 permutations, this might be flaky, but with the strong 
    effect (0.3) and 1000 permutations (default), it should be significant.
    We run 200 here for a balance of speed and reliability.
    """
    result = run_permutation_test(
        sample_user_track_data,
        outcome='mean_vividness',
        predictor='residualized_exposure_score',
        popularity='overall_popularity_score',
        n_permutations=200,
        seed=42
    )
    
    # Since we generated data with a positive effect, the p-value should be < 0.05
    # with high probability. We assert < 0.1 to be safe with small N, 
    # but ideally it should be much lower.
    assert result['p_value'] < 0.1, f"P-value {result['p_value']} is not significant enough"

def test_permutation_null_effect():
    """
    Test that if there is no effect, the p-value is not significant.
    """
    np.random.seed(42)
    n_users = 50
    n_tracks = 20
    
    user_ids = np.repeat(range(n_users), n_tracks)
    track_ids = np.tile(range(n_tracks), n_users)
    
    # Random exposure (no true effect)
    exposure_scores = np.random.uniform(0, 1, len(user_ids))
    popularity_scores = np.random.uniform(0.1, 0.9, len(user_ids))
    
    # Outcome independent of exposure
    vividness = np.random.normal(0.5, 0.1, len(user_ids))
    
    df = pd.DataFrame({
        'user_id': user_ids,
        'track_id': track_ids,
        'residualized_exposure_score': exposure_scores,
        'overall_popularity_score': popularity_scores,
        'mean_vividness': vividness
    })
    
    result = run_permutation_test(
        df,
        outcome='mean_vividness',
        predictor='residualized_exposure_score',
        popularity='overall_popularity_score',
        n_permutations=200,
        seed=42
    )
    
    # With no true effect, p-value should be > 0.05 most of the time
    # We just check it's a valid probability
    assert 0.0 <= result['p_value'] <= 1.0
    # It's hard to assert > 0.05 deterministically, but it shouldn't be extremely low
    assert result['p_value'] > 0.01, "P-value is suspiciously low for null data"

def test_permutation_missing_columns():
    """
    Test that the function raises an error if required columns are missing.
    """
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    
    with pytest.raises(ValueError):
        run_permutation_test(df)