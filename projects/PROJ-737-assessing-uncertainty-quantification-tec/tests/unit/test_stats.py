import pytest
import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
from stats.significance import run_paired_wilcoxon, run_sensitivity_analysis

def test_run_paired_wilcoxon_basic():
    """Test basic Wilcoxon test execution on synthetic data"""
    # Create synthetic per-sample errors data
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'sample_id': list(range(n_samples)) * 2,
        'method': ['method_a'] * n_samples + ['method_b'] * n_samples,
        'prediction': np.concatenate([np.random.normal(0, 1, n_samples), np.random.normal(0.5, 1, n_samples)]),
        'lower_bound': [0.0] * (2 * n_samples),
        'upper_bound': [0.0] * (2 * n_samples),
        'ground_truth': np.concatenate([np.random.normal(0, 1, n_samples), np.random.normal(0.5, 1, n_samples)]),
        'dataset': ['dataset_a'] * (2 * n_samples)
    }
    
    df = pd.DataFrame(data)
    
    result = run_paired_wilcoxon(df)
    
    assert isinstance(result, pd.DataFrame)
    assert 'p_value' in result.columns
    assert 'statistic' in result.columns
    assert 'dataset' in result.columns
    assert 'method_pair' in result.columns
    assert len(result) > 0

def test_run_sensitivity_analysis_coverage_range():
    """Test sensitivity analysis with specific coverage range"""
    # Create synthetic conformal results
    np.random.seed(42)
    n_samples = 200
    
    data = {
        'sample_id': list(range(n_samples)),
        'method': ['conformal'] * n_samples,
        'prediction': np.random.normal(0, 1, n_samples),
        'lower_bound': np.random.normal(-1, 0.5, n_samples),
        'upper_bound': np.random.normal(1, 0.5, n_samples),
        'ground_truth': np.random.normal(0, 1, n_samples),
        'dataset': ['dataset_a'] * n_samples
    }
    
    df = pd.DataFrame(data)
    
    # Test with custom range
    result = run_sensitivity_analysis(df, coverage_range=(0.85, 0.95))
    
    assert isinstance(result, pd.DataFrame)
    assert 'coverage_level' in result.columns
    assert 'avg_width' in result.columns
    assert 'observed_coverage_error' in result.columns
    
    # Check that coverage levels are within range
    assert all(result['coverage_level'] >= 0.85)
    assert all(result['coverage_level'] <= 0.95)
    
    # Check step size
    coverage_levels = sorted(result['coverage_level'].unique())
    if len(coverage_levels) > 1:
        steps = np.diff(coverage_levels)
        assert all(np.isclose(steps, 0.01, atol=0.001))

def test_run_sensitivity_analysis_empty_input():
    """Test sensitivity analysis with empty input"""
    df = pd.DataFrame(columns=['sample_id', 'method', 'prediction', 'lower_bound', 'upper_bound', 'ground_truth', 'dataset'])
    
    result = run_sensitivity_analysis(df)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0

def test_run_sensitivity_analysis_multiple_datasets():
    """Test sensitivity analysis with multiple datasets"""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'sample_id': list(range(n_samples)) * 2,
        'method': ['conformal'] * (2 * n_samples),
        'prediction': np.concatenate([np.random.normal(0, 1, n_samples), np.random.normal(0, 1, n_samples)]),
        'lower_bound': [0.0] * (2 * n_samples),
        'upper_bound': [0.0] * (2 * n_samples),
        'ground_truth': np.concatenate([np.random.normal(0, 1, n_samples), np.random.normal(0, 1, n_samples)]),
        'dataset': ['dataset_a'] * n_samples + ['dataset_b'] * n_samples
    }
    
    df = pd.DataFrame(data)
    
    result = run_sensitivity_analysis(df)
    
    assert isinstance(result, pd.DataFrame)
    assert 'dataset' in result.columns
    assert len(result['dataset'].unique()) == 2
