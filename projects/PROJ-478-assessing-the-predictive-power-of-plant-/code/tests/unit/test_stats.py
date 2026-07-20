"""
Unit tests for statistical analysis functions in src/analysis/stats.py
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

from src.analysis.stats import (
    load_model_results,
    calculate_differences,
    paired_t_test,
    bonferroni_correction,
    calculate_cohen_d,
    interpret_effect_size,
    run_statistical_analysis
)

@pytest.fixture
def sample_results_df():
    """Create a sample DataFrame with model results."""
    data = {
        'species': ['sp1', 'sp2', 'sp3', 'sp4', 'sp5'],
        'auc_climate': [0.75, 0.80, 0.72, 0.85, 0.78],
        'auc_traits': [0.78, 0.82, 0.75, 0.87, 0.80],
        'tss_climate': [0.45, 0.50, 0.42, 0.55, 0.48],
        'tss_traits': [0.48, 0.52, 0.45, 0.58, 0.50]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_results_file(sample_results_df):
    """Create a temporary CSV file with sample results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_results_df.to_csv(f, index=False)
        return f.name

def test_load_model_results_success(temp_results_file):
    """Test successful loading of model results from CSV."""
    df = load_model_results(temp_results_file)
    assert len(df) == 5
    assert 'species' in df.columns
    assert 'auc_climate' in df.columns
    assert 'auc_traits' in df.columns
    assert 'tss_climate' in df.columns
    assert 'tss_traits' in df.columns

def test_load_model_results_missing_columns(temp_results_file):
    """Test error handling for missing columns."""
    # Create a file with missing columns
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        pd.DataFrame({'species': ['sp1'], 'auc_climate': [0.75]}).to_csv(f, index=False)
        temp_file = f.name
    
    with pytest.raises(ValueError, match="Missing required columns"):
        load_model_results(temp_file)

def test_calculate_differences(sample_results_df):
    """Test calculation of differences between trait and climate models."""
    auc_diff = calculate_differences(sample_results_df, 'auc')
    expected_auc_diff = pd.Series([0.03, 0.02, 0.03, 0.02, 0.02], name='auc_diff')
    pd.testing.assert_series_equal(auc_diff, expected_auc_diff)

def test_paired_t_test_basic():
    """Test basic paired t-test functionality."""
    differences = pd.Series([0.03, 0.02, 0.03, 0.02, 0.02])
    result = paired_t_test(differences)
    
    assert 't_statistic' in result
    assert 'p_value' in result
    assert 'df' in result
    assert result['n'] == 5
    assert result['df'] == 4
    assert result['mean_diff'] > 0  # Positive mean difference

def test_paired_t_test_insufficient_data():
    """Test t-test with insufficient data points."""
    differences = pd.Series([0.03])
    result = paired_t_test(differences)
    
    assert result['n'] == 1
    assert result['df'] == 0
    assert np.isnan(result['t_statistic'])
    assert np.isnan(result['p_value'])

def test_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_values = [0.01, 0.03, 0.05]
    result = bonferroni_correction(p_values, alpha=0.05)
    
    assert len(result['corrected_p_values']) == 3
    assert result['n_tests'] == 3
    assert result['alpha_corrected'] == 0.05 / 3
    
    # Check that corrected p-values are <= 1.0
    assert all(p <= 1.0 for p in result['corrected_p_values'])
    
    # Check significance decisions
    # With alpha_corrected = 0.0167, only p=0.01 should be significant
    assert result['significant'][0] == True  # 0.01 < 0.0167
    assert result['significant'][1] == False  # 0.03 > 0.0167
    assert result['significant'][2] == False  # 0.05 > 0.0167

def test_bonferroni_correction_empty():
    """Test Bonferroni correction with empty list."""
    result = bonferroni_correction([], alpha=0.05)
    
    assert len(result['corrected_p_values']) == 0
    assert result['n_tests'] == 0

def test_calculate_cohen_d():
    """Test Cohen's d calculation."""
    differences = pd.Series([0.03, 0.02, 0.03, 0.02, 0.02])
    cohen_d = calculate_cohen_d(differences)
    
    assert isinstance(cohen_d, float)
    assert cohen_d > 0  # Positive effect size
    
    # Verify calculation manually
    mean_diff = differences.mean()
    std_diff = differences.std()
    expected_cohen_d = mean_diff / std_diff
    assert abs(cohen_d - expected_cohen_d) < 1e-10

def test_calculate_cohen_d_insufficient_data():
    """Test Cohen's d with insufficient data."""
    differences = pd.Series([0.03])
    cohen_d = calculate_cohen_d(differences)
    
    assert np.isnan(cohen_d)

def test_calculate_cohen_d_zero_std():
    """Test Cohen's d with zero standard deviation."""
    differences = pd.Series([0.02, 0.02, 0.02, 0.02])
    cohen_d = calculate_cohen_d(differences)
    
    assert np.isnan(cohen_d)

def test_interpret_effect_size():
    """Test effect size interpretation."""
    assert interpret_effect_size(0.1) == "negligible"
    assert interpret_effect_size(0.3) == "small"
    assert interpret_effect_size(0.6) == "medium"
    assert interpret_effect_size(1.0) == "large"
    assert np.isnan(interpret_effect_size(np.nan))

def test_run_statistical_analysis(temp_results_file):
    """Test the full statistical analysis pipeline."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    results = run_statistical_analysis(temp_results_file, output_path, alpha=0.05)
    
    # Check structure
    assert 'auc_analysis' in results
    assert 'tss_analysis' in results
    assert 'bonferroni_correction' in results
    assert 'summary' in results
    
    # Check AUC analysis
    assert results['auc_analysis']['n_samples'] == 5
    assert results['auc_analysis']['mean_difference'] > 0
    assert 't_statistic' in results['auc_analysis']
    assert 'p_value' in results['auc_analysis']
    assert 'corrected_p_value' in results['auc_analysis']
    assert 'cohen_d' in results['auc_analysis']
    assert 'effect_size_interpretation' in results['auc_analysis']
    
    # Check TSS analysis
    assert results['tss_analysis']['n_samples'] == 5
    assert results['tss_analysis']['mean_difference'] > 0
    
    # Check Bonferroni correction
    assert results['bonferroni_correction']['n_tests'] == 2
    assert len(results['bonferroni_correction']['corrected_p_values']) == 2
    
    # Check summary
    assert results['summary']['total_species'] == 5
    assert results['summary']['species_with_valid_metrics'] == 5
    
    # Verify file was created
    assert Path(output_path).exists()
    
    # Verify JSON is valid
    with open(output_path, 'r') as f:
        saved_results = json.load(f)
    assert saved_results == results

def test_run_statistical_analysis_with_nan():
    """Test statistical analysis with some NaN values."""
    data = {
        'species': ['sp1', 'sp2', 'sp3', 'sp4', 'sp5'],
        'auc_climate': [0.75, 0.80, np.nan, 0.85, 0.78],
        'auc_traits': [0.78, 0.82, 0.75, 0.87, 0.80],
        'tss_climate': [0.45, 0.50, 0.42, 0.55, 0.48],
        'tss_traits': [0.48, 0.52, 0.45, 0.58, 0.50]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_input = f.name
        df.to_csv(f, index=False)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    results = run_statistical_analysis(temp_input, output_path, alpha=0.05)
    
    # Should handle NaN gracefully
    assert results['auc_analysis']['n_samples'] < 5  # Some samples dropped
    assert results['tss_analysis']['n_samples'] == 5
    assert not np.isnan(results['auc_analysis']['t_statistic'])

def test_paired_t_test_negative_difference():
    """Test t-test with negative mean difference."""
    differences = pd.Series([-0.03, -0.02, -0.03, -0.02, -0.02])
    result = paired_t_test(differences)
    
    assert result['mean_diff'] < 0
    assert result['t_statistic'] < 0

def test_bonferroni_correction_all_significant():
    """Test Bonferroni correction when all are significant."""
    p_values = [0.001, 0.002, 0.003]
    result = bonferroni_correction(p_values, alpha=0.05)
    
    # alpha_corrected = 0.05/3 = 0.0167
    # All corrected p-values should be < 0.0167
    assert all(result['significant'])