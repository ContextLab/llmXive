"""
Unit tests for T043: FID stability correlation calculation.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'code'))

from metrics.fid_stability_corr import (
    load_hybrid_output,
    load_estimator_predictions,
    compute_fid_stability,
    calculate_correlation,
    run_fid_stability_correlation,
    CORRELATION_THRESHOLD
)

@pytest.fixture
def sample_hybrid_output():
    """Create a sample hybrid output DataFrame."""
    return pd.DataFrame({
        'frame_id': list(range(100)),
        'fid_score': np.random.uniform(5.0, 15.0, 100),
        'skip_flag': np.random.choice([True, False], 100),
        'latency': np.random.uniform(0.1, 0.5, 100)
    })

@pytest.fixture
def sample_predictions():
    """Create a sample predictions DataFrame."""
    return pd.DataFrame({
        'frame_id': list(range(100)),
        'predicted_delta_magnitude': np.random.uniform(0.0, 1.0, 100)
    })

@pytest.fixture
def temp_parquet_file(tmp_path, sample_hybrid_output):
    """Create a temporary parquet file with sample data."""
    file_path = tmp_path / 'test_hybrid_output.parquet'
    sample_hybrid_output.to_parquet(file_path)
    return file_path

@pytest.fixture
def temp_predictions_file(tmp_path, sample_predictions):
    """Create a temporary predictions parquet file."""
    file_path = tmp_path / 'test_predictions.parquet'
    sample_predictions.to_parquet(file_path)
    return file_path

def test_compute_fid_stability_with_skip_flags(sample_hybrid_output):
    """Test FID stability computation with skip flags."""
    result = compute_fid_stability(sample_hybrid_output)
    
    assert 'fid_stability' in result.columns
    assert len(result) == len(sample_hybrid_output)
    
    # Check that skipped frames have non-zero stability (relative to baseline)
    skipped = result[result['skip_flag'] == True]
    if len(skipped) > 0:
        # Stability should be non-negative
        assert all(result.loc[skipped.index, 'fid_stability'] >= 0)

def test_compute_fid_stability_without_fid_column():
    """Test FID stability computation when fid_score is missing."""
    df = pd.DataFrame({
        'frame_id': list(range(10)),
        'skip_flag': [True] * 10
    })
    
    result = compute_fid_stability(df)
    
    assert 'fid_stability' in result.columns
    # Should create placeholder zeros
    assert all(result['fid_stability'] == 0.0)

def test_calculate_correlation_basic(sample_predictions, sample_hybrid_output):
    """Test basic correlation calculation."""
    # Compute FID stability first
    hybrid_with_stability = compute_fid_stability(sample_hybrid_output)
    
    corr, p_val, n = calculate_correlation(sample_predictions, hybrid_with_stability)
    
    assert corr is not None
    assert p_val is not None
    assert n > 0
    assert -1.0 <= corr <= 1.0

def test_calculate_correlation_insufficient_data():
    """Test correlation calculation with insufficient data."""
    predictions = pd.DataFrame({
        'frame_id': [0],
        'predicted_delta_magnitude': [0.5]
    })
    
    hybrid = pd.DataFrame({
        'frame_id': [0],
        'fid_stability': [0.3]
    })
    
    corr, p_val, n = calculate_correlation(predictions, hybrid)
    
    # Need at least 2 points for correlation
    assert corr is None
    assert p_val is None
    assert n == 0

def test_calculate_correlation_with_nan_values():
    """Test correlation calculation with NaN values."""
    predictions = pd.DataFrame({
        'frame_id': [0, 1, 2, 3],
        'predicted_delta_magnitude': [0.5, np.nan, 0.7, 0.8]
    })
    
    hybrid = pd.DataFrame({
        'frame_id': [0, 1, 2, 3],
        'fid_stability': [0.3, 0.4, np.nan, 0.5]
    })
    
    corr, p_val, n = calculate_correlation(predictions, hybrid)
    
    # Should handle NaN by dropping them
    assert corr is not None
    assert n == 2  # Only 2 valid pairs

@patch('metrics.fid_stability_corr.load_hybrid_output')
@patch('metrics.fid_stability_corr.load_estimator_predictions')
@patch('metrics.fid_stability_corr.compute_fid_stability')
@patch('metrics.fid_stability_corr.calculate_correlation')
@patch('metrics.fid_stability_corr.log_results')
@patch('metrics.fid_stability_corr.update_state_with_validation')
def test_run_fid_stability_correlation_success(
    mock_update_state,
    mock_log_results,
    mock_calc_corr,
    mock_compute_stability,
    mock_load_preds,
    mock_load_hybrid
):
    """Test successful correlation calculation."""
    # Setup mocks
    mock_load_hybrid.return_value = pd.DataFrame({
        'frame_id': [0, 1, 2],
        'fid_score': [10.0, 11.0, 12.0],
        'skip_flag': [True, False, True]
    })
    
    mock_load_preds.return_value = pd.DataFrame({
        'frame_id': [0, 1, 2],
        'predicted_delta_magnitude': [0.5, 0.6, 0.7]
    })
    
    mock_compute_stability.side_effect = lambda df: df.assign(fid_stability=[0.1, 0.0, 0.2])
    mock_calc_corr.return_value = (0.85, 0.001, 3)  # High correlation
    
    result = run_fid_stability_correlation()
    
    assert result['status'] == 'passed'
    assert result['correlation'] == 0.85
    mock_update_state.assert_called_once()

@patch('metrics.fid_stability_corr.load_hybrid_output')
@patch('metrics.fid_stability_corr.update_state_with_validation')
def test_run_fid_stability_correlation_no_hybrid_output(
    mock_update_state,
    mock_load_hybrid
):
    """Test handling when hybrid output is missing."""
    mock_load_hybrid.return_value = None
    
    result = run_fid_stability_correlation()
    
    assert result['status'] == 'failed'
    assert result['reason'] == 'Could not load hybrid output'
    mock_update_state.assert_called_once()

@patch('metrics.fid_stability_corr.load_hybrid_output')
@patch('metrics.fid_stability_corr.load_estimator_predictions')
@patch('metrics.fid_stability_corr.update_state_with_validation')
def test_run_fid_stability_correlation_no_predictions(
    mock_update_state,
    mock_load_preds,
    mock_load_hybrid
):
    """Test handling when predictions are missing."""
    mock_load_hybrid.return_value = pd.DataFrame({'frame_id': [0]})
    mock_load_preds.return_value = None
    
    result = run_fid_stability_correlation()
    
    assert result['status'] == 'failed'
    assert result['reason'] == 'Could not load estimator predictions'
    mock_update_state.assert_called_once()

@patch('metrics.fid_stability_corr.load_hybrid_output')
@patch('metrics.fid_stability_corr.load_estimator_predictions')
@patch('metrics.fid_stability_corr.compute_fid_stability')
@patch('metrics.fid_stability_corr.calculate_correlation')
@patch('metrics.fid_stability_corr.log_results')
@patch('metrics.fid_stability_corr.update_state_with_validation')
def test_run_fid_stability_correlation_low_correlation(
    mock_update_state,
    mock_log_results,
    mock_calc_corr,
    mock_compute_stability,
    mock_load_preds,
    mock_load_hybrid
):
    """Test when correlation is below threshold."""
    mock_load_hybrid.return_value = pd.DataFrame({
        'frame_id': [0, 1, 2],
        'fid_score': [10.0, 11.0, 12.0],
        'skip_flag': [True, False, True]
    })
    
    mock_load_preds.return_value = pd.DataFrame({
        'frame_id': [0, 1, 2],
        'predicted_delta_magnitude': [0.5, 0.6, 0.7]
    })
    
    mock_compute_stability.side_effect = lambda df: df.assign(fid_stability=[0.1, 0.0, 0.2])
    mock_calc_corr.return_value = (0.5, 0.1, 3)  # Low correlation
    
    result = run_fid_stability_correlation()
    
    assert result['status'] == 'failed'
    assert result['correlation'] == 0.5
    # Should still update state with invalidated status
    mock_update_state.assert_called_once()