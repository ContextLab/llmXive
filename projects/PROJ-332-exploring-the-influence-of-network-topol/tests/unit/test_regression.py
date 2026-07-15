import pytest
import pandas as pd
import numpy as np
from regression_analysis import run_ols_regression, detect_percolation_threshold, analyze_scaling_law

def test_regression_outputs():
    """Test that regression outputs include exponent, CI, and p-value."""
    # Create synthetic data
    np.random.seed(42)
    x = np.linspace(1, 10, 20)
    y = 2 * x + np.random.normal(0, 0.5, 20)
    
    df = pd.DataFrame({'avg_degree': x, 'conductivity': y})
    
    results = run_ols_regression(df, 'avg_degree', 'conductivity')
    
    # Check that all required fields are present
    assert 'exponent' in results
    assert 'ci_low' in results
    assert 'ci_high' in results
    assert 'p_value' in results
    assert 'r_squared' in results
    
    # Check values are reasonable
    assert results['exponent'] is not None
    assert abs(results['exponent'] - 2.0) < 0.5  # Should be close to 2
    assert results['p_value'] < 0.05  # Should be significant

def test_percolation_threshold_logic():
    """Test percolation threshold detection with 80% connectivity cutoff."""
    # Create mock results
    results = [
        {'avg_degree': 1.0, 'percolation_flag': 0},
        {'avg_degree': 1.0, 'percolation_flag': 0},
        {'avg_degree': 2.0, 'percolation_flag': 1},
        {'avg_degree': 2.0, 'percolation_flag': 1},
        {'avg_degree': 2.0, 'percolation_flag': 0},
        {'avg_degree': 3.0, 'percolation_flag': 1},
        {'avg_degree': 3.0, 'percolation_flag': 1},
        {'avg_degree': 3.0, 'percolation_flag': 1},
        {'avg_degree': 3.0, 'percolation_flag': 1},
    ]
    
    threshold = detect_percolation_threshold(results)
    
    # At degree 3.0, 4/4 = 100% connected -> threshold should be 3.0
    # At degree 2.0, 2/3 = 66.7% connected -> not threshold
    assert threshold == 3.0

def test_scaling_law_analysis():
    """Test scaling law analysis returns significant results."""
    results = [
        {'avg_degree': 2.0, 'conductivity': 10.0, 'percolation_flag': 1},
        {'avg_degree': 3.0, 'conductivity': 15.0, 'percolation_flag': 1},
        {'avg_degree': 4.0, 'conductivity': 20.0, 'percolation_flag': 1},
        {'avg_degree': 5.0, 'conductivity': 25.0, 'percolation_flag': 1},
    ]
    
    analysis = analyze_scaling_law(results, threshold=1.5)
    
    assert 'significant' in analysis
    assert 'exponent' in analysis
    assert 'message' in analysis
    assert analysis['significant'] is True  # Should be significant