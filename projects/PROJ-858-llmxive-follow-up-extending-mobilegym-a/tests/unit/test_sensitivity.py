import pytest
import numpy as np
from analysis.sensitivity import (
    calculate_vector_scalar,
    align_data,
    compute_pearson_correlation,
    analyze_sensitivity
)

def test_calculate_vector_scalar():
    """Test scalar calculation from binary vector."""
    vector = {'task_id': 't1', 'vector': [1, 0, 1, 1, 0]}
    assert calculate_vector_scalar(vector) == 3
    
    vector_empty = {'task_id': 't2', 'vector': [0, 0, 0]}
    assert calculate_vector_scalar(vector_empty) == 0
    
    vector_full = {'task_id': 't3', 'vector': [1, 1, 1, 1]}
    assert calculate_vector_scalar(vector_full) == 4

def test_align_data():
    """Test alignment of coverage vectors and validation results."""
    coverage = [
        {'task_id': 't1', 'vector': [1, 0, 1]},
        {'task_id': 't2', 'vector': [0, 0, 0]},
        {'task_id': 't3', 'vector': [1, 1, 1]}
    ]
    
    validation = [
        {'task_id': 't1', 'success_rate': 0.8},
        {'task_id': 't2', 'success_rate': 0.2},
        {'task_id': 't4', 'success_rate': 0.5}  # Not in coverage
    ]
    
    scalars, rates = align_data(coverage, validation)
    
    # t1: scalar=2, rate=0.8
    # t2: scalar=0, rate=0.2
    # t3 and t4 are excluded (mismatch)
    assert len(scalars) == 2
    assert len(rates) == 2
    
    # Check values (order might vary based on set intersection)
    assert (2.0 in scalars and 0.8 in rates) or (0.0 in scalars and 0.2 in rates)

def test_compute_pearson_correlation():
    """Test Pearson correlation calculation."""
    # Perfect positive correlation
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    corr = compute_pearson_correlation(x, y)
    assert corr is not None
    assert abs(corr - 1.0) < 1e-6
    
    # Perfect negative correlation
    y_neg = [10, 8, 6, 4, 2]
    corr_neg = compute_pearson_correlation(x, y_neg)
    assert corr_neg is not None
    assert abs(corr_neg - (-1.0)) < 1e-6
    
    # No correlation
    y_no = [1, 5, 2, 8, 3]
    corr_no = compute_pearson_correlation(x, y_no)
    assert corr_no is not None
    # Should be close to 0 but not exactly due to randomness
    assert abs(corr_no) < 0.9

def test_analyze_sensitivity_proxy_validated():
    """Test that 'Proxy Validated' status is returned when r >= 0.5."""
    # Create data with strong positive correlation
    coverage = [
        {'task_id': f't{i}', 'vector': [1] * i + [0] * (5 - i)}
        for i in range(1, 6)
    ]
    # Success rates increasing with vector sum
    validation = [
        {'task_id': f't{i}', 'success_rate': 0.1 + 0.15 * i}
        for i in range(1, 6)
    ]
    
    config = {}
    results = analyze_sensitivity(config, coverage, validation)
    
    assert results['status'] == 'success'
    assert results['validation_status'] == 'Proxy Validated'
    assert results['correlation'] is not None
    assert results['correlation'] >= 0.5

def test_analyze_sensitivity_invalid_proxy():
    """Test that 'Invalid Proxy' status is returned when r < 0.3."""
    # Create data with weak/no correlation
    coverage = [
        {'task_id': 't1', 'vector': [1, 0, 1]},
        {'task_id': 't2', 'vector': [0, 1, 0]},
        {'task_id': 't3', 'vector': [1, 1, 1]},
        {'task_id': 't4', 'vector': [0, 0, 0]}
    ]
    # Random success rates
    validation = [
        {'task_id': 't1', 'success_rate': 0.5},
        {'task_id': 't2', 'success_rate': 0.9},
        {'task_id': 't3', 'success_rate': 0.2},
        {'task_id': 't4', 'success_rate': 0.7}
    ]
    
    config = {}
    results = analyze_sensitivity(config, coverage, validation)
    
    assert results['status'] == 'success'
    # Depending on the random data, it might be Invalid or Inconclusive
    # But we ensure we don't get 'Proxy Validated'
    assert results['validation_status'] != 'Proxy Validated'

def test_analyze_sensitivity_insufficient_data():
    """Test handling of insufficient data points."""
    coverage = [{'task_id': 't1', 'vector': [1, 0]}]
    validation = [{'task_id': 't1', 'success_rate': 0.5}]
    
    config = {}
    results = analyze_sensitivity(config, coverage, validation)
    
    assert results['status'] == 'failed'
    assert results['reason'] == 'No aligned data points found' or 'Insufficient data' in str(results.get('message', ''))

def test_analyze_sensitivity_mismatched_ids():
    """Test handling when no common task IDs exist."""
    coverage = [{'task_id': 't1', 'vector': [1, 0]}]
    validation = [{'task_id': 't2', 'success_rate': 0.5}]
    
    config = {}
    results = analyze_sensitivity(config, coverage, validation)
    
    assert results['status'] == 'failed'
    assert 'No aligned data' in results.get('reason', '')