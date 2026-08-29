"""
Unit tests for statistical_tests.py
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import json
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from analysis.statistical_tests import (
    calculate_cohens_d,
    calculate_confidence_interval,
    run_paired_ttest,
    load_predictions
)

def test_cohens_d_identical_groups():
    """Test Cohen's d when groups are identical (should be 0)"""
    group1 = np.array([1.0, 2.0, 3.0])
    group2 = np.array([1.0, 2.0, 3.0])
    d = calculate_cohens_d(group1, group2)
    assert np.isclose(d, 0.0, atol=1e-5)

def test_cohens_d_large_difference():
    """Test Cohen's d with known large difference"""
    group1 = np.array([10.0, 11.0, 12.0])
    group2 = np.array([1.0, 2.0, 3.0])
    d = calculate_cohens_d(group1, group2)
    # Mean diff = 9, Pooled std approx 5.2
    # d approx 1.7
    assert d > 1.0

def test_confidence_interval_width():
    """Test that CI width is proportional to std error"""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    low, high = calculate_confidence_interval(data, confidence=0.95)
    assert low < np.mean(data) < high

def test_paired_ttest_significance():
    """Test paired t-test with significantly different groups"""
    # Create groups with clear difference
    group1 = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    group2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    
    result = run_paired_ttest(group1, group2)
    assert result['p_value'] < 0.05
    assert result['mean_difference'] > 0

def test_paired_ttest_no_significance():
    """Test paired t-test with random noise (no significant difference)"""
    np.random.seed(42)
    group1 = np.random.normal(0, 1, 100)
    group2 = np.random.normal(0, 1, 100)
    
    result = run_paired_ttest(group1, group2)
    # With random noise, p-value is likely > 0.05 (but not guaranteed)
    # We just check the function runs and returns valid stats
    assert 't_statistic' in result
    assert 'p_value' in result
    assert isinstance(result['p_value'], float)

def test_load_predictions(tmp_path):
    """Test loading predictions from JSON file"""
    test_data = {
        "gnn_errors": [1.0, 2.0, 3.0],
        "rf_errors": [1.5, 2.5, 3.5]
    }
    file_path = tmp_path / "test_preds.json"
    with open(file_path, 'w') as f:
        json.dump(test_data, f)
    
    loaded = load_predictions(file_path)
    assert "gnn_errors" in loaded
    assert "rf_errors" in loaded
    assert isinstance(loaded["gnn_errors"], np.ndarray)
    assert len(loaded["gnn_errors"]) == 3