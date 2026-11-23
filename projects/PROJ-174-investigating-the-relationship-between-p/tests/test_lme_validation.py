import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from analysis.lme_model import validate_sufficient_trials, mitigate_collinearity, handle_unfulfillable_predictors

@pytest.fixture
def mock_df():
    return pd.DataFrame({
        'subject_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S2', 'S2'],
        'search_time': [1.2, 1.5, 1.3, 2.0, 2.1, 2.2, 2.3],
        'pupil_diameter': [3.1, 3.2, 3.1, 4.0, 4.1, 4.2, 4.3]
    })

@pytest.fixture
def mock_df_low_trials():
    return pd.DataFrame({
        'subject_id': ['S1', 'S1', 'S2', 'S2', 'S2'],
        'search_time': [1.2, 1.5, 2.0, 2.1, 2.2],
        'pupil_diameter': [3.1, 3.2, 4.0, 4.1, 4.2]
    })

def test_validate_sufficient_trials_pass(mock_df):
    """Test that validation passes when all subjects have >= 20 trials (mocked threshold)."""
    # In real scenario, we would have 20+ trials. Here we test the logic with a lower threshold
    # by passing a custom min_trials.
    assert validate_sufficient_trials(mock_df, min_trials=2, aggregation_enabled=False) == True

def test_validate_sufficient_trials_fail(mock_df_low_trials):
    """Test that validation fails when a subject has < 20 trials."""
    with pytest.raises(RuntimeError, match="Subject S1 has < 20 trials"):
        validate_sufficient_trials(mock_df_low_trials, min_trials=3, aggregation_enabled=False)

def test_validate_sufficient_trials_aggregation_enabled(mock_df_low_trials):
    """Test that validation passes when aggregation is enabled."""
    assert validate_sufficient_trials(mock_df_low_trials, min_trials=3, aggregation_enabled=True) == True

def test_mitigate_collinearity_no_reduction(mock_df):
    """Test that no predictor is dropped if VIF is low."""
    predictors = ['search_time']
    remaining, dropped = mitigate_collinearity(mock_df, predictors, threshold=5.0)
    assert dropped is None
    assert remaining == predictors

def test_handle_unfulfillable_predictors(mock_df):
    """Test handling of predictors with NA values."""
    # Add a column with all NA
    df_na = mock_df.copy()
    df_na['target_salience'] = np.nan
    
    usable, unfulfillable = handle_unfulfillable_predictors(df_na, ['search_time', 'target_salience'])
    assert 'search_time' in usable
    assert 'target_salience' in unfulfillable
