"""
Unit Tests for Statistical Analysis Module.

This module contains unit tests for power analysis and correlation logic.
"""
import pytest
import numpy as np
from analysis.power_analysis import calculate_power_for_correlation, check_power_sufficiency
from analysis.correlation import calculate_spearman_correlation

def test_power_calculation():
    """
    Test power analysis logic.
    """
    # With large N, power should be high
    power_large = calculate_power_for_correlation(n=100, effect_size=0.5)
    assert power_large > 0.8, "Power should be high for large N"
    
    # With small N, power should be low
    power_small = calculate_power_for_correlation(n=5, effect_size=0.5)
    assert power_small < 0.5, "Power should be low for small N"

def test_power_sufficiency_check():
    """
    Test power sufficiency check.
    """
    assert check_power_sufficiency(0.8) is True
    assert check_power_sufficiency(0.1) is False

def test_spearman_correlation():
    """
    Test Spearman correlation calculation with bootstrap.
    """
    np.random.seed(42)
    x = np.random.normal(0, 1, 50)
    y = x + np.random.normal(0, 0.5, 50)  # Positive correlation
    
    result = calculate_spearman_correlation(x, y, bootstrap_iterations=100)
    
    assert 'r' in result
    assert 'p_value' in result
    assert 'ci_lower' in result
    assert 'ci_upper' in result
    assert result['r'] > 0, "Correlation should be positive"
