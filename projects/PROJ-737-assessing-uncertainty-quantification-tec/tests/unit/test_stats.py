"""
Unit tests for statistical significance testing module.
"""
import pytest
import pandas as pd
import numpy as np
from scipy.stats import wilcoxon

import sys
from pathlib import Path

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_path))

from stats.significance import run_paired_wilcoxon, run_sensitivity_analysis

@pytest.fixture
def sample_metrics_df():
    """Create a sample DataFrame with per-sample errors for testing."""
    np.random.seed(42)
    n_samples = 200
    
    # Create sample data
    sample_ids = [f"sample_{i}" for i in range(n_samples)]
    methods = ['GPR', 'MC_Dropout', 'Deep_Ensemble']
    datasets = ['OQMD_BandGap', 'OQMD_FormationEnergy']
    
    records = []
    for dataset in datasets:
        for method in methods:
            for i, sample_id in enumerate(sample_ids):
                # Generate correlated errors to simulate realistic scenario
                base_error = np.random.normal(0, 0.5, n_samples)
                if method == 'GPR':
                    error = base_error + np.random.normal(0, 0.1)
                elif method == 'MC_Dropout':
                    error = base_error + np.random.normal(0, 0.15)
                else:  # Deep_Ensemble
                    error = base_error + np.random.normal(0, 0.12)
                
                records.append({
                    'sample_id': sample_id,
                    'method': method,
                    'prediction': 1.0 + error,  # Ground truth = 1.0
                    'ground_truth': 1.0,
                    'dataset': dataset
                })
    
    return pd.DataFrame(records)

@pytest.fixture
def sample_conformal_results():
    """Create sample conformal prediction results."""
    np.random.seed(42)
    n_samples = 100
    
    records = []
    for coverage_level in [0.80, 0.85, 0.90, 0.95, 0.99]:
        for i in range(n_samples):
            width = np.random.uniform(0.5, 1.5)
            lower = 1.0 - width / 2 + np.random.normal(0, 0.05)
            upper = 1.0 + width / 2 + np.random.normal(0, 0.05)
            ground_truth = 1.0 + np.random.normal(0, 0.1)
            
            records.append({
                'sample_id': f"sample_{i}",
                'coverage_level': coverage_level,
                'lower_bound': lower,
                'upper_bound': upper,
                'ground_truth': ground_truth,
                'interval_width': upper - lower
            })
    
    return pd.DataFrame(records)

def test_run_paired_wilcoxon_basic(sample_metrics_df):
    """Test basic functionality of paired Wilcoxon test."""
    results = run_paired_wilcoxon(sample_metrics_df)
    
    # Check that results are returned
    assert isinstance(results, pd.DataFrame)
    assert len(results) > 0
    
    # Check required columns
    required_cols = ['dataset', 'method_pair', 'statistic', 'p_value', 'significant', 'n_samples']
    assert all(col in results.columns for col in required_cols)
    
    # Check that we have tests for each dataset
    assert len(results['dataset'].unique()) == 2
    
    # Check that p_values are in valid range
    assert all((results['p_value'] >= 0) & (results['p_value'] <= 1))
    
    # Check that significant flag is boolean
    assert results['significant'].dtype == bool

def test_run_paired_wilcoxon_missing_columns():
    """Test that appropriate error is raised for missing columns."""
    incomplete_df = pd.DataFrame({
        'sample_id': ['s1', 's2'],
        'method': ['GPR', 'MC_Dropout'],
        'prediction': [1.0, 1.1]
    })
    
    with pytest.raises(ValueError, match="missing required columns"):
        run_paired_wilcoxon(incomplete_df)

def test_run_paired_wilcoxon_small_sample():
    """Test behavior with very small sample size."""
    np.random.seed(42)
    small_df = pd.DataFrame({
        'sample_id': [f"sample_{i}" for i in range(5)],
        'method': ['GPR'] * 5 + ['MC_Dropout'] * 5,
        'prediction': [1.0, 1.1, 1.2, 1.3, 1.4, 1.1, 1.2, 1.3, 1.4, 1.5],
        'ground_truth': [1.0] * 10,
        'dataset': ['test'] * 10
    })
    
    # Should handle gracefully, possibly with warning
    results = run_paired_wilcoxon(small_df)
    
    # May return empty DataFrame if too few samples
    assert isinstance(results, pd.DataFrame)

def test_run_sensitivity_analysis_basic(sample_conformal_results):
    """Test basic functionality of sensitivity analysis."""
    results = run_sensitivity_analysis(sample_conformal_results)
    
    # Check that results are returned
    assert isinstance(results, pd.DataFrame)
    assert len(results) > 0
    
    # Check required columns
    required_cols = ['coverage_level', 'avg_width', 'observed_coverage', 'coverage_error']
    assert all(col in results.columns for col in required_cols)
    
    # Check that coverage levels are in expected range
    assert all((results['coverage_level'] >= 0.80) & (results['coverage_level'] <= 0.99))
    
    # Check that coverage_error is non-negative
    assert all(results['coverage_error'] >= 0)

def test_run_sensitivity_analysis_custom_range(sample_conformal_results):
    """Test sensitivity analysis with custom coverage range."""
    results = run_sensitivity_analysis(
        sample_conformal_results,
        coverage_range=(0.85, 0.95),
        step_size=0.02
    )
    
    # Check that only requested range is included
    assert all((results['coverage_level'] >= 0.85) & (results['coverage_level'] <= 0.95))
    
    # Check step size
    coverage_levels = sorted(results['coverage_level'].unique())
    for i in range(1, len(coverage_levels)):
        assert abs(coverage_levels[i] - coverage_levels[i-1]) <= 0.025  # Allow small floating point error

def test_run_sensitivity_analysis_no_data():
    """Test sensitivity analysis with empty input."""
    empty_df = pd.DataFrame(columns=['coverage_level', 'lower_bound', 'upper_bound', 'ground_truth'])
    results = run_sensitivity_analysis(empty_df)
    
    assert isinstance(results, pd.DataFrame)
    assert len(results) == 0

def test_paired_wilcoxon_vs_scipy():
    """Verify our implementation matches scipy's wilcoxon for a simple case."""
    np.random.seed(42)
    n = 50
    
    # Create paired data with known difference
    x = np.random.normal(0, 1, n)
    y = x + np.random.normal(0.2, 0.5, n)  # Shifted by 0.2
    
    # Expected result from scipy
    expected_stat, expected_p = wilcoxon(x - y)
    
    # Create DataFrame for our function
    df = pd.DataFrame({
        'sample_id': [f"s{i}" for i in range(n)],
        'method': ['A'] * n + ['B'] * n,
        'prediction': list(x) + list(y),
        'ground_truth': [0.0] * (2 * n),  # Both compared to 0
        'dataset': ['test'] * (2 * n)
    })
    
    results = run_paired_wilcoxon(df)
    
    # Find our result for A vs B
    our_result = results[results['method_pair'] == 'A vs B'].iloc[0]
    
    # Check that statistics are approximately equal
    assert abs(our_result['statistic'] - expected_stat) < 1e-10
    assert abs(our_result['p_value'] - expected_p) < 1e-10
