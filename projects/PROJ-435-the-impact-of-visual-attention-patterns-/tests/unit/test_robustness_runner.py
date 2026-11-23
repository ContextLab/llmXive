import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import from the project's utility module
from code.utils.robustness_runner import apply_fixation_filter, prepare_data_for_regression, run_mixed_effects_regression, run_robustness_regression

@pytest.fixture
def sample_gaze_data():
    return pd.DataFrame({
        'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
        'headline_id': ['H1', 'H2', 'H3', 'H1', 'H2', 'H3'],
        'x': [100, 102, 101, 150, 152, 151],
        'y': [200, 201, 200, 250, 251, 250],
        'timestamp': [1000, 1033, 1066, 2000, 2033, 2066],
        'roi_type': ['headline_body', 'headline_body', 'headline_body', 'headline_body', 'headline_body', 'headline_body']
    })

@pytest.fixture
def sample_merged_data():
    return pd.DataFrame({
        'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
        'headline_id': ['H1', 'H2', 'H3', 'H1', 'H2', 'H3'],
        'fixation_duration': [100, 150, 120, 130, 140, 110],
        'valence_score': [0.8, -0.5, 0.2, 0.8, -0.5, 0.2],
        'cognitive_reflection_score': [2, 1, 3, 2, 1, 3],
        'belief_rating': [5, 4, 3, 5, 4, 3],
        'headline_length': [10, 12, 8, 10, 12, 8],
        'total_fixation_duration': [300, 400, 350, 320, 380, 340]
    })

def test_apply_fixation_filter_basic(sample_gaze_data):
    # Filter with a 100ms threshold
    filtered = apply_fixation_filter(sample_gaze_data, threshold=100)
    assert 'fixation_duration' in filtered.columns
    assert len(filtered) <= len(sample_gaze_data)

def test_run_robustness_regression_basic(sample_merged_data):
    # Mock the regression functions
    with patch('code.utils.robustness_runner.prepare_data_for_regression') as mock_prepare:
        with patch('code.utils.robustness_runner.run_mixed_effects_regression') as mock_run:
            with patch('code.utils.robustness_runner.generate_results_dataframe') as mock_generate:
                mock_prepare.return_value = sample_merged_data
                mock_result = MagicMock()
                mock_result.params = {'fixation_duration': 0.5}
                mock_result.pvalues = {'fixation_duration': 0.01}
                mock_run.return_value = mock_result
                mock_generate.return_value = pd.DataFrame({'parameter': ['fixation_duration'], 'estimate': [0.5], 'pvalue': [0.01]})
                
                result = run_robustness_regression(sample_merged_data, threshold=100)
                assert result is not None
                assert 'parameter' in result.columns

def test_run_robustness_regression_with_different_thresholds(sample_merged_data):
    # Test that different thresholds produce different results (or at least run without error)
    with patch('code.utils.robustness_runner.apply_fixation_filter') as mock_filter:
        mock_filter.return_value = sample_merged_data
        with patch('code.utils.robustness_runner.run_mixed_effects_regression') as mock_run:
            with patch('code.utils.robustness_runner.generate_results_dataframe') as mock_generate:
                mock_result = MagicMock()
                mock_result.params = {'fixation_duration': 0.5}
                mock_result.pvalues = {'fixation_duration': 0.01}
                mock_run.return_value = mock_result
                mock_generate.return_value = pd.DataFrame({'parameter': ['fixation_duration'], 'estimate': [0.5], 'pvalue': [0.01]})
                
                # Run with different thresholds
                result_50 = run_robustness_regression(sample_merged_data, threshold=50)
                result_100 = run_robustness_regression(sample_merged_data, threshold=100)
                result_150 = run_robustness_regression(sample_merged_data, threshold=150)
                
                assert result_50 is not None
                assert result_100 is not None
                assert result_150 is not None
