import pytest
import numpy as np
from regression_analysis import run_ols_regression, detect_percolation_threshold, analyze_scaling_law

def test_regression_outputs():
    """Test that regression produces exponent, CI, and p-value."""
    # Create mock data
    mock_results = [
        {"seed": 1, "N": 100, "p": 0.1, "avg_degree": 2.0, "conductivity": 10.0, "percolation_flag": 1},
        {"seed": 2, "N": 100, "p": 0.1, "avg_degree": 3.0, "conductivity": 15.0, "percolation_flag": 1},
        {"seed": 3, "N": 100, "p": 0.1, "avg_degree": 4.0, "conductivity": 20.0, "percolation_flag": 1},
        {"seed": 4, "N": 100, "p": 0.1, "avg_degree": 5.0, "conductivity": 25.0, "percolation_flag": 1},
    ]

    result = run_ols_regression(mock_results)

    assert "exponent" in result
    assert "ci_low" in result
    assert "ci_high" in result
    assert "p_value" in result
    assert result["exponent"] is not None
    assert result["p_value"] is not None

def test_percolation_threshold_logic():
    """Test 80% connectivity cutoff logic."""
    mock_results = [
        {"seed": 1, "avg_degree": 1.0, "percolation_flag": 0},
        {"seed": 2, "avg_degree": 1.0, "percolation_flag": 0},
        {"seed": 3, "avg_degree": 2.0, "percolation_flag": 1},
        {"seed": 4, "avg_degree": 2.0, "percolation_flag": 0},
        {"seed": 5, "avg_degree": 3.0, "percolation_flag": 1},
        {"seed": 6, "avg_degree": 3.0, "percolation_flag": 1},
        {"seed": 7, "avg_degree": 3.0, "percolation_flag": 1},
        {"seed": 8, "avg_degree": 3.0, "percolation_flag": 1},
        {"seed": 9, "avg_degree": 4.0, "percolation_flag": 1},
    ]

    threshold = detect_percolation_threshold(mock_results)
    
    # At avg_degree=3, 4/4=100% connected -> should be threshold
    assert threshold is not None
    assert threshold == 3.0

def test_scaling_law_significance():
    """Test that scaling law reports significance correctly."""
    mock_results = [
        {"avg_degree": 3.0, "conductivity": 10.0, "percolation_flag": 1},
        {"avg_degree": 4.0, "conductivity": 12.0, "percolation_flag": 1},
        {"avg_degree": 5.0, "conductivity": 14.0, "percolation_flag": 1},
        {"avg_degree": 6.0, "conductivity": 16.0, "percolation_flag": 1},
    ]

    threshold = 2.0
    result = analyze_scaling_law(mock_results, threshold)

    assert "significant" in result
    assert "exponent" in result
    assert "p_value" in result