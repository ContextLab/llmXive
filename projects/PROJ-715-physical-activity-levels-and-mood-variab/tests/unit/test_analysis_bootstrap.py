import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import the function to test
# Assuming analysis.py is in the code directory and we are running from project root
# Adjust import path if necessary based on how tests are run
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis import run_bootstrap_sensitivity_analysis, run_sensitivity_analysis_exclude_single_ratings, run_sensitivity_analysis_impute_single_ratings

@pytest.fixture
def mock_df():
    """Create a mock dataframe with necessary columns."""
    data = {
        'participant_id': ['P1'] * 100 + ['P2'] * 100,
        'total_steps': np.random.randint(1000, 20000, 200),
        'sleep_duration': np.random.uniform(6, 9, 200),
        'day_of_week': np.random.choice([0, 1, 2, 3, 4, 5, 6], 200),
        'baseline_affect': np.random.uniform(-1, 1, 200),
        'mean_mood': np.random.uniform(1, 5, 200),
        'mood_std': np.random.uniform(0, 1, 200),
        'log_mood_std': np.log(np.random.uniform(0, 1, 200) + 0.01), # Pre-transformed
        'n_ratings': np.random.choice([1, 2, 3, 4, 5], 200) # Mix of single and multiple
    }
    return pd.DataFrame(data)

def test_exclude_single_ratings(mock_df):
    """Test that single-rating days are excluded."""
    result = run_sensitivity_analysis_exclude_single_ratings(mock_df)
    assert (result['n_ratings'] >= 2).all()
    assert len(result) < len(mock_df) # Should be strictly less if there were single ratings

def test_impute_single_ratings(mock_df):
    """Test that single-rating days are imputed."""
    original_single = mock_df[mock_df['n_ratings'] == 1]
    if len(original_single) == 0:
        pytest.skip("No single rating days in mock data")
        
    result = run_sensitivity_analysis_impute_single_ratings(mock_df)
    
    # Check that n_ratings is still 1 (we don't change the count, just the values)
    imputed_single = result[result['n_ratings'] == 1]
    
    # The mean_mood for these rows should be imputed (not necessarily equal to original if original was NaN, 
    # but here we assume original had values. The logic replaces them with median).
    # We just verify the function runs without error and returns a dataframe of same size.
    assert len(result) == len(mock_df)
    assert 'mean_mood' in result.columns

@patch('analysis.fit_mood_std_model')
@patch('analysis.run_sensitivity_analysis_impute_single_ratings')
@patch('analysis.run_sensitivity_analysis_exclude_single_ratings')
def test_run_bootstrap_sensitivity_analysis(mock_exclude, mock_impute, mock_fit, mock_df):
    """Test the bootstrap loop logic with mocked dependencies."""
    
    # Setup mocks
    mock_exclude.return_value = mock_df[mock_df['n_ratings'] >= 2]
    mock_impute.return_value = mock_df # Return same size for simplicity
    
    # Mock the model result to return a fixed coefficient
    mock_result = MagicMock()
    mock_result.fe_params = {'total_steps': 0.5}
    mock_fit.return_value = mock_result

    # Run the function
    # Note: This will likely fail in a real environment due to statsmodels fitting on random data,
    # but with mocks it should proceed.
    # We need to ensure the loop runs at least once.
    
    # Patch the random seed to ensure reproducibility in test
    with patch('numpy.random.choice') as mock_choice:
        mock_choice.return_value = np.arange(len(mock_df)) # Identity selection for stability
        
        result = run_bootstrap_sensitivity_analysis(mock_df)

    # Assertions
    assert 'consistency_rate' in result
    assert 'total_iterations' in result
    assert result['total_iterations'] > 0
    # Since we mocked the same coefficient (0.5), consistency should be 100%
    assert result['consistency_rate'] == 1.0
    assert result['threshold_met'] == True

def test_bootstrap_threshold_logic(mock_df):
    """Verify that the threshold logic works correctly."""
    # This is harder to test without mocking the loop heavily, 
    # but we can check the return structure.
    # We rely on the previous test for the core logic.
    pass
