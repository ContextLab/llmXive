import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from statistical_analysis import (
    compute_effect_size_cohen_d,
    compute_power_cohen_d,
    compute_cliffs_delta,
    get_effect_size_magnitude,
    run_mann_whitney_u_test,
    run_power_analysis_for_metric,
    PowerAnalysisResult
)

def test_cohen_d_identical_groups():
    """Test Cohen's d returns 0 for identical groups."""
    group1 = np.array([1.0, 2.0, 3.0])
    group2 = np.array([1.0, 2.0, 3.0])
    d = compute_effect_size_cohen_d(group1, group2)
    assert abs(d) < 1e-6

def test_cohen_d_different_groups():
    """Test Cohen's d returns positive value for distinct groups."""
    group1 = np.array([1.0, 2.0, 3.0])
    group2 = np.array([4.0, 5.0, 6.0])
    d = compute_effect_size_cohen_d(group1, group2)
    assert d < 0 # group1 < group2, so negative
    assert abs(d) > 1.0

def test_power_calculation():
    """Test power calculation increases with effect size."""
    n = 50
    power_small = compute_power_cohen_d(0.2, n)
    power_large = compute_power_cohen_d(0.8, n)
    assert power_small < power_large
    assert power_large > 0.8 # Large effect with n=50 should have high power

def test_cliffs_delta():
    """Test Cliff's Delta calculation."""
    group1 = np.array([1.0, 2.0, 3.0])
    group2 = np.array([4.0, 5.0, 6.0])
    d = compute_cliffs_delta(group1, group2)
    # group1 is entirely less than group2, so d should be -1.0
    assert abs(d - (-1.0)) < 1e-6

def test_effect_size_magnitude():
    """Test magnitude classification."""
    assert get_effect_size_magnitude(0.1) == "negligible"
    assert get_effect_size_magnitude(0.2) == "small"
    assert get_effect_size_magnitude(0.4) == "medium"
    assert get_effect_size_magnitude(0.6) == "large"

def test_mann_whitney_u():
    """Test Mann-Whitney U test."""
    group1 = np.array([1.0, 2.0, 3.0])
    group2 = np.array([4.0, 5.0, 6.0])
    u, p = run_mann_whitney_u_test(group1, group2)
    assert p < 0.05 # Should be significant

def test_power_analysis_threshold_warning():
    """Test that power analysis logs warning when power < 0.8."""
    # Small sample size and small effect size -> low power
    group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    group2 = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
    
    result = run_power_analysis_for_metric(group1, group2, "test_metric", min_power_threshold=0.8)
    
    assert result.passed == False
    assert "WARNING" in result.message
    assert result.power < 0.8

def test_power_analysis_threshold_pass():
    """Test that power analysis passes when power >= 0.8."""
    # Large effect size and sufficient sample size -> high power
    group1 = np.array([1.0] * 50)
    group2 = np.array([5.0] * 50)
    
    result = run_power_analysis_for_metric(group1, group2, "test_metric", min_power_threshold=0.8)
    
    assert result.passed == True
    assert "WARNING" not in result.message
    assert result.power >= 0.8