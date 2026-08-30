"""
Unit tests for screening module.
"""
import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from uq.screening import (
    load_predictions,
    calculate_expected_loss,
    rank_by_expected_loss,
    run_baseline_screening,
    generate_screening_candidates,
    generate_baseline_screening
)

@pytest.fixture
def sample_predictions():
    """Create sample UQ predictions DataFrame."""
    data = {
        'sample_id': [1, 2, 3, 4, 5],
        'method': ['deep_ensemble'] * 5,
        'prediction': [-1.0, -1.5, -2.0, -1.2, -1.8],
        'variance': [0.1, 0.2, 0.15, 0.25, 0.12],
        'aleatoric': [0.05, 0.1, 0.075, 0.125, 0.06],
        'epistemic': [0.05, 0.1, 0.075, 0.125, 0.06],
        'total': [0.1, 0.2, 0.15, 0.25, 0.12]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_input_file(sample_predictions):
    """Create a temporary input file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_predictions.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_predictions(temp_input_file):
    """Test loading predictions from CSV."""
    df = load_predictions(temp_input_file)
    assert len(df) == 5
    assert 'sample_id' in df.columns
    assert 'prediction' in df.columns
    assert 'variance' in df.columns

def test_load_predictions_missing_file():
    """Test loading from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_predictions('non_existent_file.csv')

def test_load_predictions_missing_columns(temp_input_file):
    """Test loading file with missing required columns."""
    # Create file with missing column
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({'sample_id': [1, 2], 'prediction': [1.0, 2.0]})
        df.to_csv(f, index=False)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_predictions(temp_path)
    finally:
        os.unlink(temp_path)

def test_calculate_expected_loss():
    """Test expected loss calculation."""
    predictions = pd.Series([1.0, 2.0, 3.0])
    variances = pd.Series([0.1, 0.2, 0.3])
    
    loss = calculate_expected_loss(predictions, variances, risk_aversion=1.0)
    expected = pd.Series([1.1, 2.2, 3.3])
    
    pd.testing.assert_series_equal(loss, expected)
    
    # Test with different risk aversion
    loss_risk2 = calculate_expected_loss(predictions, variances, risk_aversion=2.0)
    expected_risk2 = pd.Series([1.2, 2.4, 3.6])
    
    pd.testing.assert_series_equal(loss_risk2, expected_risk2)

def test_rank_by_expected_loss(sample_predictions):
    """Test ranking by expected loss."""
    ranked = rank_by_expected_loss(sample_predictions, 'deep_ensemble', risk_aversion=1.0)
    
    assert len(ranked) == 5
    assert 'expected_loss' in ranked.columns
    assert 'rank' in ranked.columns
    
    # Check sorting (should be ascending by expected loss)
    assert ranked['expected_loss'].is_monotonic_increasing
    
    # Check that rank 1 has lowest expected loss
    assert ranked.iloc[0]['rank'] == 1

def test_run_baseline_screening(sample_predictions):
    """Test baseline screening (no variance penalty)."""
    baseline = run_baseline_screening(sample_predictions, 'deep_ensemble')
    
    assert len(baseline) == 5
    assert 'rank' in baseline.columns
    
    # Check sorting (should be ascending by prediction)
    assert baseline['prediction'].is_monotonic_increasing

def test_generate_screening_candidates(sample_predictions):
    """Test generating candidates for multiple methods."""
    # Create data with multiple methods
    data = {
        'sample_id': [1, 2, 3, 4, 5, 6, 7, 8],
        'method': ['deep_ensemble'] * 4 + ['mc_dropout'] * 4,
        'prediction': [-1.0, -1.5, -2.0, -1.2, -1.1, -1.6, -2.1, -1.3],
        'variance': [0.1, 0.2, 0.15, 0.25, 0.11, 0.21, 0.16, 0.26]
    }
    predictions_df = pd.DataFrame(data)
    
    candidates = generate_screening_candidates(
        predictions_df,
        ['deep_ensemble', 'mc_dropout'],
        risk_aversion=1.0
    )
    
    assert len(candidates) == 8
    assert 'expected_loss' in candidates.columns
    assert 'rank' in candidates.columns
    
    # Check that both methods are present
    assert set(candidates['method'].unique()) == {'deep_ensemble', 'mc_dropout'}

def test_generate_screening_candidates_with_fallback(sample_predictions):
    """Test that missing methods are skipped without error."""
    candidates = generate_screening_candidates(
        sample_predictions,
        ['deep_ensemble', 'non_existent_method'],
        risk_aversion=1.0
    )
    
    assert len(candidates) == 5
    assert set(candidates['method'].unique()) == {'deep_ensemble'}

def test_generate_baseline_screening(sample_predictions):
    """Test generating baseline candidates."""
    baseline = generate_baseline_screening(
        sample_predictions,
        ['deep_ensemble']
    )
    
    assert len(baseline) == 5
    assert 'rank' in baseline.columns
    assert baseline['uncertainty_type'].iloc[0] == 'point_prediction'

def test_top_k_limit(sample_predictions):
    """Test that top_k limit is applied correctly."""
    candidates = generate_screening_candidates(
        sample_predictions,
        ['deep_ensemble'],
        top_k=3
    )
    
    assert len(candidates) == 3
    assert candidates['rank'].max() == 3

def test_empty_method_list(sample_predictions):
    """Test handling of empty method list."""
    with pytest.raises(RuntimeError):
        generate_screening_candidates(
            sample_predictions,
            [],
            risk_aversion=1.0
        )
