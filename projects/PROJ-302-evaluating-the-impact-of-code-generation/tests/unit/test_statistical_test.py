import pytest
import numpy as np
from analysis.statistical_test import run_shapiro_wilk, calculate_cohens_d, select_and_run_test

def test_run_shapiro_wilk_normal():
    """Test Shapiro-Wilk test on normally distributed data."""
    np.random.seed(42)
    data = np.random.normal(0, 1, 100)
    
    stat, p_value = run_shapiro_wilk(data)
    
    assert 0 <= p_value <= 1

def test_run_shapiro_wilk_small_sample():
    """Test Shapiro-Wilk test on small sample."""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    
    stat, p_value = run_shapiro_wilk(data)
    
    assert 0 <= p_value <= 1

def test_calculate_cohens_d():
    """Test Cohen's d calculation."""
    group1 = np.array([1, 2, 3, 4, 5])
    group2 = np.array([2, 3, 4, 5, 6])
    
    d = calculate_cohens_d(group1, group2)
    
    assert isinstance(d, float)

def test_select_and_run_test_normal():
    """Test test selection when data is normal."""
    np.random.seed(42)
    group1 = np.random.normal(10, 1, 50)
    group2 = np.random.normal(11, 1, 50)
    
    result = select_and_run_test(group1, group2)
    
    assert 'p_value' in result
    assert 'test_type' in result

def test_select_and_run_test_non_normal():
    """Test test selection when data is non-normal."""
    # Skewed distribution
    group1 = np.random.exponential(2, 50)
    group2 = np.random.exponential(2.5, 50)
    
    result = select_and_run_test(group1, group2)
    
    assert 'p_value' in result
    assert result['test_type'] in ['t-test', 'mann-whitney']