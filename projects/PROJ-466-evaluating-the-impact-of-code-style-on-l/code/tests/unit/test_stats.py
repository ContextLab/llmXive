"""
Unit tests for statistical analysis (T029, T030).
Tests Kruskal-Wallis H-test and sensitivity analysis.
"""
import pytest
import sys
import numpy as np
from pathlib import Path

# Ensure imports work
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from analysis.stats import kruskal_wallis_test, dunn_posthoc_test
from analysis.sensitivity import run_sweep_kruskal

def test_kruskal_wallis_test():
    """Test Kruskal-Wallis H-test setup and execution (T029)."""
    # Create synthetic data with different distributions
    group1 = np.random.normal(0, 1, 50)
    group2 = np.random.normal(2, 1, 50) # Different mean
    group3 = np.random.normal(0, 1, 50)

    stat, p_value = kruskal_wallis_test([group1, group2, group3])

    assert stat > 0, "H-statistic should be positive"
    assert 0 <= p_value <= 1, "p-value should be between 0 and 1"
    # Since groups are different, p-value should likely be small
    assert p_value < 0.05, "Expected significant difference for distinct groups"

def test_dunn_posthoc_test():
    """Test Dunn's post-hoc test (T029)."""
    # Mock data for post-hoc
    group1 = np.random.normal(0, 1, 50)
    group2 = np.random.normal(2, 1, 50)
    
    # This function usually requires the full dataset or pre-calculated ranks
    # We test the interface exists and returns a result structure
    # Note: The actual implementation in stats.py might need adjustment to accept raw arrays
    # For this test, we assume it returns a dict of comparisons
    result = dunn_posthoc_test([group1, group2])
    
    assert result is not None, "Post-hoc result should not be None"
    assert isinstance(result, dict), "Post-hoc result should be a dict"

def test_sensitivity_sweep():
    """Test sensitivity analysis threshold sweep (T030)."""
    # Create mock metrics data
    mock_data = {
        "style_A": [1.0, 2.0, 3.0, 4.0, 5.0],
        "style_B": [1.5, 2.5, 3.5, 4.5, 5.5],
        "style_C": [2.0, 3.0, 4.0, 5.0, 6.0]
    }
    
    # Test the sweep function
    # We pass a small range of alphas for speed
    alphas = [0.01, 0.05, 0.1]
    results = run_sweep_kruskal(mock_data, alphas)
    
    assert results is not None
    assert len(results) == len(alphas)
    for alpha, count in results:
        assert alpha in alphas
        assert isinstance(count, int) or isinstance(count, np.integer)