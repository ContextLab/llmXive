"""
Unit tests for sensitivity analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import json
import tempfile
from pathlib import Path

from analysis.sensitivity import run_sensitivity_analysis

@pytest.fixture
def mock_dataframe():
    """Create a mock dataframe with required columns."""
    n_samples = 200
    # Use log-log linear relationship + noise to simulate Paris Law behavior
    delta_k = np.linspace(5, 25, n_samples)
    # da/dN = C * (Delta_K)^m, with m ~ 3, C ~ 1e-10
    da_dN = 1e-10 * (delta_k ** 3) + np.random.normal(0, 1e-10, n_samples)
    # Ensure positive values
    da_dN = np.abs(da_dN)
    
    data = {
        'Delta_K': delta_k,
        'da_dN': da_dN,
        'C': np.random.uniform(0.1, 0.5, n_samples),
        'Mn': np.random.uniform(0.5, 2.0, n_samples),
        'Heat_Treatment': np.random.choice(['T6', 'O', 'Unknown'], n_samples)
    }
    return pd.DataFrame(data)

def test_run_sensitivity_analysis_basic(mock_dataframe):
    """Test basic execution of sensitivity analysis."""
    feature_cols = ['C', 'Mn']
    result = run_sensitivity_analysis(
        df=mock_dataframe,
        feature_cols=feature_cols,
        delta_k_col='Delta_K',
        target_col='da_dN',
        n_sweeps=3,
        random_state=42
    )
    
    assert 'sweep_results' in result
    assert 'stability_metric' in result
    assert 'is_model_stable' in result
    assert 'regime_ranking_stable' in result
    assert 'summary' in result
    
    # Check sweep results structure
    assert len(result['sweep_results']) == 3
    for sweep in result['sweep_results']:
        assert 'n_estimators' in sweep
        assert 'mean_r2' in sweep
        assert 'std_r2' in sweep
        assert 'regime_stats' in sweep

def test_run_sensitivity_analysis_output_file(mock_dataframe):
    """Test that sensitivity analysis writes a JSON report when output_dir is provided."""
    feature_cols = ['C', 'Mn']
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_sensitivity_analysis(
            df=mock_dataframe,
            feature_cols=feature_cols,
            delta_k_col='Delta_K',
            target_col='da_dN',
            n_sweeps=2,
            random_state=42,
            output_dir=tmpdir
        )
        
        assert 'final_report_path' in result
        assert Path(result['final_report_path']).exists()
        
        with open(result['final_report_path'], 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['stability_metric'] == result['stability_metric']
        assert saved_data['summary']['best_n_estimators'] > 0

def test_stability_metric_calculation(mock_dataframe):
    """Test that stability metric is calculated correctly (CV of R2)."""
    feature_cols = ['C', 'Mn']
    result = run_sensitivity_analysis(
        df=mock_dataframe,
        feature_cols=feature_cols,
        n_sweeps=5,
        random_state=42
    )
    
    r2_values = [r['mean_r2'] for r in result['sweep_results']]
    # Avoid division by zero if mean is 0 (unlikely with real data)
    if np.mean(r2_values) != 0:
        expected_cv = np.std(r2_values) / np.abs(np.mean(r2_values))
        assert np.isclose(result['stability_metric'], expected_cv)
    
    # Stability threshold is 0.1 (10% CV)
    assert result['is_model_stable'] == (result['stability_metric'] < 0.1)

def test_regime_ranking_stability_logic(mock_dataframe):
    """Test that regime ranking stability is checked."""
    feature_cols = ['C', 'Mn']
    result = run_sensitivity_analysis(
        df=mock_dataframe,
        feature_cols=feature_cols,
        n_sweeps=3,
        random_state=42
    )
    
    # The result should contain the boolean flag
    assert 'regime_ranking_stable' in result
    assert isinstance(result['regime_ranking_stable'], bool)

def test_empty_feature_cols(mock_dataframe):
    """Test handling of empty feature columns (should raise or return empty)."""
    # With no features, the model will likely fail or produce NaNs.
    # We expect it to handle it gracefully or raise a clear error.
    with pytest.raises((ValueError, IndexError)):
        run_sensitivity_analysis(
            df=mock_dataframe,
            feature_cols=[],
            n_sweeps=2
        )

def test_small_sample_size(mock_dataframe):
    """Test behavior with a very small dataset (edge case)."""
    small_df = mock_dataframe.head(10)
    feature_cols = ['C']
    
    # Should not crash, but might have low stability
    result = run_sensitivity_analysis(
        df=small_df,
        feature_cols=feature_cols,
        n_sweeps=2,
        random_state=42
    )
    
    assert 'sweep_results' in result
    # With small data, stability might be low, but it should run
    assert len(result['sweep_results']) == 2

def test_invalid_target_col(mock_dataframe):
    """Test handling of invalid target column."""
    feature_cols = ['C', 'Mn']
    with pytest.raises(KeyError):
        run_sensitivity_analysis(
            df=mock_dataframe,
            feature_cols=feature_cols,
            delta_k_col='Delta_K',
            target_col='nonexistent_column',
            n_sweeps=2
        )

def test_invalid_delta_k_col(mock_dataframe):
    """Test handling of invalid Delta_K column."""
    feature_cols = ['C', 'Mn']
    with pytest.raises(KeyError):
        run_sensitivity_analysis(
            df=mock_dataframe,
            feature_cols=feature_cols,
            delta_k_col='nonexistent_column',
            target_col='da_dN',
            n_sweeps=2
        )

def test_single_feature_col(mock_dataframe):
    """Test sensitivity analysis with a single feature column."""
    feature_cols = ['C']
    result = run_sensitivity_analysis(
        df=mock_dataframe,
        feature_cols=feature_cols,
        delta_k_col='Delta_K',
        target_col='da_dN',
        n_sweeps=2,
        random_state=42
    )
    
    assert 'sweep_results' in result
    assert len(result['sweep_results']) == 2
    assert result['summary']['best_n_estimators'] > 0

def test_multiple_feature_cols(mock_dataframe):
    """Test sensitivity analysis with multiple feature columns."""
    feature_cols = ['C', 'Mn', 'Heat_Treatment']
    result = run_sensitivity_analysis(
        df=mock_dataframe,
        feature_cols=feature_cols,
        delta_k_col='Delta_K',
        target_col='da_dN',
        n_sweeps=2,
        random_state=42
    )
    
    assert 'sweep_results' in result
    assert len(result['sweep_results']) == 2
    assert result['summary']['best_n_estimators'] > 0

def test_different_random_states(mock_dataframe):
    """Test that different random states produce different results."""
    feature_cols = ['C', 'Mn']
    result1 = run_sensitivity_analysis(
        df=mock_dataframe,
        feature_cols=feature_cols,
        delta_k_col='Delta_K',
        target_col='da_dN',
        n_sweeps=2,
        random_state=42
    )
    result2 = run_sensitivity_analysis(
        df=mock_dataframe,
        feature_cols=feature_cols,
        delta_k_col='Delta_K',
        target_col='da_dN',
        n_sweeps=2,
        random_state=123
    )
    
    # Results should differ due to different random seeds in CV splits
    # (though they might be similar, they shouldn't be identical)
    assert result1['stability_metric'] != result2['stability_metric'] or \
           result1['summary']['best_n_estimators'] != result2['summary']['best_n_estimators']