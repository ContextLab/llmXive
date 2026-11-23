"""
Tests for the sensitivity analysis module, specifically T065 (LOO-CV).
"""
import json
import pytest
from pathlib import Path
import numpy as np

# Import the function to test
from sensitivity import perform_leave_one_out_cv, SensitivityError

@pytest.fixture
def sample_results():
    """Generate a mock set of statistical results for testing."""
    # Create 10 bins with different frequencies
    results = []
    np.random.seed(42)
    for i in range(10):
        freq = 10.0 + i * 5.0
        # Simulate p-values
        ks_p = np.random.uniform(0.01, 0.2)
        chi2_p = np.random.uniform(0.01, 0.2)
        results.append({
            'frequency': freq,
            'ks_p_value': ks_p,
            'chi2_p_value': chi2_p,
            'material': 'steel',
            'n_samples': 1000
        })
    return results

@pytest.fixture
def outlier_results():
    """Generate results where one bin is a clear outlier driver."""
    results = []
    # 9 normal bins (high p-values, no rejection)
    for i in range(9):
        results.append({
            'frequency': 10.0 + i,
            'ks_p_value': 0.5,
            'chi2_p_value': 0.6,
            'material': 'steel',
            'n_samples': 1000
        })
    # 1 outlier bin (very low p-values, causes rejection)
    results.append({
        'frequency': 99.0,
        'ks_p_value': 0.001,
        'chi2_p_value': 0.001,
        'material': 'steel',
        'n_samples': 1000
    })
    return results

def test_loo_cv_empty_input():
    """Test that LOO-CV handles empty input gracefully."""
    result = perform_leave_one_out_cv([])
    assert 'error' in result
    assert result['error'] == 'No results provided for LOO-CV'

def test_loo_cv_single_bin(sample_results):
    """Test LOO-CV with a single bin type (or effectively single group)."""
    # Modify sample to have only one frequency
    for r in sample_results:
        r['frequency'] = 10.0
    
    result = perform_leave_one_out_cv(sample_results)
    
    assert result['total_bins_analyzed'] == 1
    assert 'bin_10.0' in result['details']
    # Removing the only bin should leave no data
    assert result['details']['bin_10.0']['status'] == 'skipped'

def test_loo_cv_outlier_detection(outlier_results):
    """Test that LOO-CV correctly identifies the outlier driver."""
    result = perform_leave_one_out_cv(outlier_results)
    
    assert result['total_bins_analyzed'] == 10
    assert result['robustness_summary'] == 'unstable_due_to_outliers'
    
    # The outlier bin (99.0) should be flagged
    outlier_details = result['details'].get('bin_99.0')
    assert outlier_details is not None
    assert outlier_details['is_outlier_driver'] is True
    
    # Other bins should not be flagged
    for i in range(10):
        freq = 10.0 + i
        if freq == 99.0:
            continue
        details = result['details'].get(f'bin_{freq}')
        if details:
            assert details['is_outlier_driver'] is False

def test_loo_cv_stable_case(sample_results):
    """Test a case where no single bin drives the result."""
    # Make all p-values very similar so no single removal changes the rate significantly
    base_p = 0.04
    for r in sample_results:
        r['ks_p_value'] = base_p
        r['chi2_p_value'] = base_p
    
    result = perform_leave_one_out_cv(sample_results)
    
    # Should be stable as all bins contribute equally
    assert result['robustness_summary'] == 'stable'
    assert len(result['outlier_drivers']) == 0

def test_loo_cv_output_structure(sample_results):
    """Test that the output structure matches the expected schema."""
    result = perform_leave_one_out_cv(sample_results)
    
    assert 'method' in result
    assert result['method'] == 'leave_one_out_cross_validation'
    assert 'total_bins_analyzed' in result
    assert 'outlier_drivers' in result
    assert 'robustness_summary' in result
    assert 'details' in result
    
    # Check detail structure
    for key, val in result['details'].items():
        assert 'bin_value' in val
        assert 'samples_excluded' in val
        assert 'samples_remaining' in val
        assert 'rejection_rate_with_bin' in val
        assert 'rejection_rate_without_bin' in val
        assert 'deviation' in val
        assert 'is_outlier_driver' in val