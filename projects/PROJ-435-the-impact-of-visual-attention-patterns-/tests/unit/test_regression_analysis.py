import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import from the project's utility module
from code.utils.regression_analysis import prepare_data_for_regression, run_mixed_effects_regression, generate_results_dataframe, apply_multiple_comparison_correction

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

def test_prepare_data_for_regression(sample_merged_data):
    prepared = prepare_data_for_regression(sample_merged_data)
    assert 'interaction_term' in prepared.columns
    assert 'fixation_duration_x_valence_x_crt' in prepared.columns

def test_run_mixed_effects_regression_basic(sample_merged_data):
    # Mock the statsmodels mixedlm to avoid actual computation
    with patch('code.utils.regression_analysis.MixedLM') as mock_model:
        mock_result = MagicMock()
        mock_result.params = {
            'fixation_duration': 0.5,
            'valence_score': 0.3,
            'cognitive_reflection_score': -0.2,
            'fixation_duration_x_valence_x_crt': 0.1
        }
        mock_result.pvalues = {
            'fixation_duration': 0.01,
            'valence_score': 0.05,
            'cognitive_reflection_score': 0.1,
            'fixation_duration_x_valence_x_crt': 0.03
        }
        mock_model.fit.return_value = mock_result
        
        result = run_mixed_effects_regression(sample_merged_data)
        assert result is not None

def test_generate_results_dataframe(sample_merged_data):
    # Create a mock result object
    mock_result = MagicMock()
    mock_result.params = pd.Series({
        'fixation_duration': 0.5,
        'valence_score': 0.3,
        'cognitive_reflection_score': -0.2,
        'fixation_duration_x_valence_x_crt': 0.1
    })
    mock_result.pvalues = pd.Series({
        'fixation_duration': 0.01,
        'valence_score': 0.05,
        'cognitive_reflection_score': 0.1,
        'fixation_duration_x_valence_x_crt': 0.03
    })
    
    df = generate_results_dataframe(mock_result)
    assert 'parameter' in df.columns
    assert 'estimate' in df.columns
    assert 'pvalue' in df.columns

def test_apply_multiple_comparison_correction():
    pvalues = pd.Series([0.01, 0.05, 0.1, 0.03])
    corrected = apply_multiple_comparison_correction(pvalues)
    assert len(corrected) == len(pvalues)
    # Holm-Bonferroni correction should result in adjusted p-values
    assert all(corrected >= pvalues)  # Adjusted p-values should be >= raw p-values
    assert all(corrected <= 1.0)  # Adjusted p-values should be <= 1.0
