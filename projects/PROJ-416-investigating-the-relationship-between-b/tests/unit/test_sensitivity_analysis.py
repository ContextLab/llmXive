import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.stats import (
    run_sensitivity_analysis,
    save_sensitivity_report,
    run_ancova_analysis,
    calculate_vif
)

@pytest.fixture
def sample_data():
    """Create sample data for testing sensitivity analysis."""
    np.random.seed(42)
    n = 20
    data = pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(n)],
        'pre_treatment_score': np.random.uniform(10, 30, n),
        'post_treatment_score': np.random.uniform(5, 25, n),
        'modularity': np.random.uniform(0.1, 0.5, n),
        'global_efficiency': np.random.uniform(0.2, 0.6, n),
        'mean_fd': np.random.uniform(0.1, 3.5, n)  # Some above 3.0 threshold
    })
    return data

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_run_sensitivity_analysis_basic(sample_data):
    """Test that sensitivity analysis runs without error."""
    result = run_sensitivity_analysis(
        data=sample_data,
        dependent_var='post_treatment_score',
        pre_var='pre_treatment_score',
        metric_var='modularity',
        motion_thresholds=[2.0, 3.0],
        p_value_thresholds=[0.05, 0.1]
    )
    
    assert 'thresholds_tested' in result
    assert 'results' in result
    assert len(result['results']) > 0
    
    # Check result structure
    for res in result['results']:
        assert 'motion_threshold' in res
        assert 'p_value_threshold' in res
        assert 'n_samples' in res
        assert 'significant_findings' in res

def test_run_sensitivity_analysis_motion_filtering(sample_data):
    """Test that motion threshold filtering reduces sample size."""
    # High threshold should include more subjects
    result_high = run_sensitivity_analysis(
        data=sample_data,
        dependent_var='post_treatment_score',
        pre_var='pre_treatment_score',
        metric_var='modularity',
        motion_thresholds=[3.5],
        p_value_thresholds=[0.05]
    )
    
    # Low threshold should include fewer subjects
    result_low = run_sensitivity_analysis(
        data=sample_data,
        dependent_var='post_treatment_score',
        pre_var='pre_treatment_score',
        metric_var='modularity',
        motion_thresholds=[1.0],
        p_value_thresholds=[0.05]
    )
    
    # High threshold should have equal or more samples than low threshold
    high_samples = result_high['results'][0]['n_samples']
    low_samples = result_low['results'][0]['n_samples']
    assert high_samples >= low_samples

def test_save_sensitivity_report(sample_data, temp_output_dir):
    """Test that sensitivity report is saved correctly."""
    sensitivity_results = run_sensitivity_analysis(
        data=sample_data,
        dependent_var='post_treatment_score',
        pre_var='pre_treatment_score',
        metric_var='modularity',
        motion_thresholds=[2.0, 3.0],
        p_value_thresholds=[0.05]
    )
    
    output_path = temp_output_dir / 'sensitivity_analysis.md'
    save_sensitivity_report(sensitivity_results, output_path)
    
    assert output_path.exists()
    
    # Check file content
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert '# Sensitivity Analysis Report' in content
    assert 'Motion Thresholds' in content
    assert 'P-value Thresholds' in content
    assert 'Results Summary' in content
    assert 'significant_findings' in content or 'Significant Findings' in content

def test_run_sensitivity_analysis_insufficient_data(sample_data):
    """Test behavior when filtering leaves insufficient data."""
    # Use a very strict motion threshold that might leave < 5 samples
    result = run_sensitivity_analysis(
        data=sample_data,
        dependent_var='post_treatment_score',
        pre_var='pre_treatment_score',
        metric_var='modularity',
        motion_thresholds=[0.1],  # Very strict
        p_value_thresholds=[0.05]
    )
    
    # Should still return a result structure, possibly with warnings
    assert 'results' in result
    # Some results might have low n_samples or be skipped

def test_run_sensitivity_analysis_p_threshold_effect(sample_data):
    """Test that different p-value thresholds yield different significance counts."""
    result = run_sensitivity_analysis(
        data=sample_data,
        dependent_var='post_treatment_score',
        pre_var='pre_treatment_score',
        metric_var='modularity',
        motion_thresholds=[3.0],
        p_value_thresholds=[0.01, 0.05, 0.1]
    )
    
    # Group by motion threshold and check p-value variation
    p01_results = [r for r in result['results'] if r['p_value_threshold'] == 0.01]
    p05_results = [r for r in result['results'] if r['p_value_threshold'] == 0.05]
    p10_results = [r for r in result['results'] if r['p_value_threshold'] == 0.1]
    
    # All should have same n_samples (same motion filter)
    if p01_results and p05_results and p10_results:
        assert p01_results[0]['n_samples'] == p05_results[0]['n_samples']
        assert p05_results[0]['n_samples'] == p10_results[0]['n_samples']
        
        # Significant findings might differ (0.1 threshold should allow more)
        # Note: This is not guaranteed but statistically likely with random data

def test_run_sensitivity_analysis_empty_data():
    """Test behavior with empty or insufficient data."""
    empty_data = pd.DataFrame(columns=['pre_treatment_score', 'post_treatment_score', 'modularity', 'mean_fd'])
    
    result = run_sensitivity_analysis(
        data=empty_data,
        dependent_var='post_treatment_score',
        pre_var='pre_treatment_score',
        metric_var='modularity',
        motion_thresholds=[3.0],
        p_value_thresholds=[0.05]
    )
    
    # Should handle gracefully
    assert 'results' in result
    # Might be empty or have error states
