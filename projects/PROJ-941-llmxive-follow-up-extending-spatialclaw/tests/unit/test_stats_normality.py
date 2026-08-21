"""
Unit tests for normality check and test selection logic in code/stats/tests.py
"""
import pytest
import numpy as np
from scipy.stats import norm
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from stats.tests import check_normality, run_wilcoxon_test, run_mcnemar_test, run_statistical_tests

def test_check_normality_normal_distribution():
    """Test that check_normality correctly identifies a normal distribution."""
    # Generate normal data
    np.random.seed(42)
    data = np.random.normal(loc=0, scale=1, size=100)
    
    res = check_normality(list(data), list(data))
    
    assert res['is_normal'] is True  # p-value should be > 0.05 for normal data
    assert res['statistic'] is not None
    assert res['pvalue'] is not None

def test_check_normality_non_normal_distribution():
    """Test that check_normality correctly identifies a non-normal distribution."""
    # Generate exponential data (skewed)
    np.random.seed(42)
    data = np.random.exponential(scale=1.0, size=100)
    
    res = check_normality(list(data), list(data))
    
    # Exponential is definitely not normal, so p-value should be low
    assert res['is_normal'] is False
    assert res['statistic'] is not None
    assert res['pvalue'] is not None

def test_check_normality_insufficient_data():
    """Test behavior with insufficient data points."""
    res = check_normality([1.0], [1.0])
    assert res['is_normal'] is False
    assert 'error' in res or res['statistic'] is None

def test_run_wilcoxon_test():
    """Test Wilcoxon test execution."""
    np.random.seed(42)
    a = np.random.normal(0, 1, 50)
    b = np.random.normal(0.5, 1, 50)
    
    res = run_wilcoxon_test(list(a), list(b))
    
    assert res['statistic'] is not None
    assert res['pvalue'] is not None

def test_run_mcnemar_test():
    """Test McNemar test execution."""
    # Create discordant pairs
    s2 = [1, 1, 1, 0, 0]
    s3 = [1, 0, 1, 1, 0]
    # a=2, b=1, c=1, d=1
    
    res = run_mcnemar_test(s2, s3)
    assert res['statistic'] is not None
    assert res['pvalue'] is not None

def test_run_mcnemar_no_discordant_pairs():
    """Test McNemar when there are no discordant pairs."""
    s2 = [1, 1, 0, 0]
    s3 = [1, 1, 0, 0]
    # b=0, c=0
    
    res = run_mcnemar_test(s2, s3)
    assert res['pvalue'] == 1.0
    assert 'note' in res

def test_run_statistical_tests_integration():
    """Test the full run_statistical_tests pipeline."""
    # Mock data
    data = [
        {'task_type': 'occlusion', '2d_success_rate': 1, '3d_success': 1, '2d_mean_latency': 10.0, '3d_latency': 10.0},
        {'task_type': 'occlusion', '2d_success_rate': 1, '3d_success': 0, '2d_mean_latency': 12.0, '3d_latency': 11.0},
        {'task_type': 'occlusion', '2d_success_rate': 0, '3d_success': 1, '2d_mean_latency': 15.0, '3d_latency': 14.0},
        {'task_type': 'depth', '2d_success_rate': 1, '3d_success': 1, '2d_mean_latency': 20.0, '3d_latency': 20.0},
        {'task_type': 'depth', '2d_success_rate': 0, '3d_success': 0, '2d_mean_latency': 22.0, '3d_latency': 21.0},
    ]
    
    results = run_statistical_tests(data)
    
    assert 'occlusion' in results
    assert 'depth' in results
    assert 'latency_test' in results['occlusion']
    assert 'normality_check' in results['occlusion']['latency_test']
    assert 'method' in results['occlusion']['latency_test']
    assert 'result' in results['occlusion']['latency_test']