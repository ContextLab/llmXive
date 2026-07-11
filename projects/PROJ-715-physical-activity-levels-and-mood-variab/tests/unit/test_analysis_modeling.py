"""
Unit tests for model convergence and coefficient extraction in analysis.py.

These tests verify that:
1. The linear mixed-effects models converge successfully.
2. The fixed-effect coefficients for 'total_steps' and covariates are extracted correctly.
3. The extracted statistics (estimate, std_err, p_value, conf_int) are valid numbers.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import fit_lmm_model, extract_coefficients


@pytest.fixture
def mock_converged_model():
    """
    Creates a mock statsmodels MixedLMResults object that simulates a successful convergence.
    """
    mock_results = MagicMock()
    mock_results.converged.return_value = True
    
    # Mock the fixed effects coefficients (params)
    # Expected columns: Intercept, total_steps, sleep_duration, C(day_of_week)[T.1], etc., baseline_affect
    mock_params = pd.Series({
        'Intercept': 2.5,
        'total_steps': -0.0001,
        'sleep_duration': 0.05,
        'baseline_affect': 0.12
    })
    mock_results.params = mock_params

    # Mock the covariance matrix for standard errors
    # Diagonal elements correspond to the params
    cov_matrix = pd.DataFrame({
        'Intercept': [0.1, 0.0, 0.0, 0.0],
        'total_steps': [0.0, 0.000001, 0.0, 0.0],
        'sleep_duration': [0.0, 0.0, 0.02, 0.0],
        'baseline_affect': [0.0, 0.0, 0.0, 0.03]
    }, index=['Intercept', 'total_steps', 'sleep_duration', 'baseline_affect'])
    mock_results.cov_params.return_value = cov_matrix

    # Mock p-values (simulated t-test or z-test results)
    mock_pvalues = pd.Series({
        'Intercept': 0.001,
        'total_steps': 0.045,
        'sleep_duration': 0.01,
        'baseline_affect': 0.005
    })
    mock_results.pvalues = mock_pvalues

    # Mock conf_int
    mock_conf_int = pd.DataFrame({
        0: [2.3, -0.0003, 0.01, 0.09],
        1: [2.7, 0.0001, 0.09, 0.15]
    }, index=['Intercept', 'total_steps', 'sleep_duration', 'baseline_affect'])
    mock_results.conf_int.return_value = mock_conf_int

    return mock_results


@pytest.fixture
def mock_data():
    """
    Creates a minimal valid DataFrame for testing model fitting logic.
    """
    data = {
        'participant_id': [1, 1, 2, 2, 3, 3],
        'total_steps': [5000, 6000, 4000, 7000, 5500, 6200],
        'log_mood_std': [0.5, 0.4, 0.6, 0.3, 0.55, 0.45],
        'sleep_duration': [7.0, 7.5, 6.5, 8.0, 7.2, 7.8],
        'baseline_affect': [3.0, 3.2, 2.8, 3.5, 3.1, 3.3],
        'day_of_week': ['Mon', 'Tue', 'Mon', 'Wed', 'Thu', 'Fri']
    }
    return pd.DataFrame(data)


def test_model_convergence_success(mock_converged_model):
    """
    Test that the code correctly identifies a successful model convergence.
    """
    assert mock_converged_model.converged() is True


def test_extract_coefficients_structure(mock_converged_model):
    """
    Test that extract_coefficients returns a dictionary with the expected structure
    and valid data types for the 'total_steps' predictor.
    """
    result = extract_coefficients(mock_converged_model, 'total_steps')
    
    assert isinstance(result, dict)
    assert 'predictor' in result
    assert 'estimate' in result
    assert 'std_err' in result
    assert 'p_value' in result
    assert 'conf_int_lower' in result
    assert 'conf_int_upper' in result
    
    assert result['predictor'] == 'total_steps'
    assert isinstance(result['estimate'], float)
    assert isinstance(result['std_err'], float)
    assert isinstance(result['p_value'], float)
    assert isinstance(result['conf_int_lower'], float)
    assert isinstance(result['conf_int_upper'], float)


def test_extract_coefficients_values(mock_converged_model):
    """
    Test that extracted values match the mock model's internal state.
    """
    result = extract_coefficients(mock_converged_model, 'total_steps')
    
    # Check estimate
    assert result['estimate'] == pytest.approx(-0.0001)
    
    # Check standard error (sqrt of diagonal of cov matrix)
    # From mock: cov_matrix.loc['total_steps', 'total_steps'] = 0.000001
    expected_se = np.sqrt(0.000001)
    assert result['std_err'] == pytest.approx(expected_se)
    
    # Check p-value
    assert result['p_value'] == pytest.approx(0.045)
    
    # Check confidence interval (mock returns 0 and 1 as columns)
    assert result['conf_int_lower'] == pytest.approx(-0.0003)
    assert result['conf_int_upper'] == pytest.approx(0.0001)


def test_extract_coefficients_missing_predictor(mock_converged_model):
    """
    Test behavior when the requested predictor is not in the model.
    """
    with pytest.raises(KeyError, match="Predictor 'non_existent_var' not found in model parameters"):
        extract_coefficients(mock_converged_model, 'non_existent_var')


def test_fit_lmm_model_convergence_check(mock_data, mock_converged_model):
    """
    Integration-style test: Verify that fit_lmm_model correctly checks for convergence
    and raises an error if the model did not converge.
    """
    # Mock the statsmodels MixedLM function to return our successful mock
    with patch('statsmodels.regression.mixed_linear_model.MixedLM') as MockMixedLM:
        mock_fit = MagicMock(return_value=mock_converged_model)
        MockMixedLM.return_value.fit = mock_fit
        
        # This should succeed without raising
        try:
            results = fit_lmm_model(
                data=mock_data,
                outcome='log_mood_std',
                predictor='total_steps',
                covariates=['sleep_duration', 'baseline_affect'],
                group_col='participant_id'
            )
            assert results is not None
            assert results.converged() is True
        except Exception as e:
            pytest.fail(f"fit_lmm_model raised an unexpected exception for a converged model: {e}")


def test_fit_lmm_model_non_convergence(mock_data):
    """
    Integration-style test: Verify that fit_lmm_model raises a RuntimeError
    if the model fails to converge.
    """
    mock_failed_results = MagicMock()
    mock_failed_results.converged.return_value = False
    
    with patch('statsmodels.regression.mixed_linear_model.MixedLM') as MockMixedLM:
        mock_fit = MagicMock(return_value=mock_failed_results)
        MockMixedLM.return_value.fit = mock_fit
        
        with pytest.raises(RuntimeError, match="Model failed to converge"):
            fit_lmm_model(
                data=mock_data,
                outcome='log_mood_std',
                predictor='total_steps',
                covariates=['sleep_duration', 'baseline_affect'],
                group_col='participant_id'
            )