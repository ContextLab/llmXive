"""
Unit tests for percolation threshold detection logic.

This module verifies the 80% connectivity cutoff logic implemented
in regression_analysis.detect_percolation_threshold.
"""
import pytest
from regression_analysis import detect_percolation_threshold


def test_percolation_threshold_logic():
    """
    Verify 80% connectivity cutoff logic.
    
    Logic:
    1. Group rows by avg_degree.
    2. Calculate connectivity ratio (mean of percolation_flag) for each degree.
    3. Find the smallest avg_degree where connectivity ratio >= threshold_pct.
    """
    # Create mock data:
    # avg_degree 2.0: 0/1 connected (0%)
    # avg_degree 3.0: 1/2 connected (50%)
    # avg_degree 4.0: 4/5 connected (80%) -> Should be threshold
    # avg_degree 5.0: 5/5 connected (100%)
    
    mock_results = [
        {"avg_degree": 2.0, "percolation_flag": 0},
        {"avg_degree": 3.0, "percolation_flag": 1},
        {"avg_degree": 3.0, "percolation_flag": 0},
        {"avg_degree": 4.0, "percolation_flag": 1},
        {"avg_degree": 4.0, "percolation_flag": 1},
        {"avg_degree": 4.0, "percolation_flag": 1},
        {"avg_degree": 4.0, "percolation_flag": 1},
        {"avg_degree": 4.0, "percolation_flag": 0}, # 4/5 = 80%
        {"avg_degree": 5.0, "percolation_flag": 1},
        {"avg_degree": 5.0, "percolation_flag": 1},
        {"avg_degree": 5.0, "percolation_flag": 1},
        {"avg_degree": 5.0, "percolation_flag": 1},
        {"avg_degree": 5.0, "percolation_flag": 1},
    ]

    threshold = detect_percolation_threshold(mock_results, threshold_pct=0.8)
    
    assert threshold is not None, "Threshold should be detected."
    assert threshold == 4.0, f"Expected threshold 4.0, got {threshold}"


def test_percolation_threshold_not_found():
    """
    Verify behavior when no degree meets 80% threshold.
    """
    mock_results = [
        {"avg_degree": 2.0, "percolation_flag": 0},
        {"avg_degree": 3.0, "percolation_flag": 0},
        {"avg_degree": 4.0, "percolation_flag": 0},
    ]

    threshold = detect_percolation_threshold(mock_results, threshold_pct=0.8)
    
    assert threshold is None, "Threshold should be None if not found."


def test_percolation_threshold_empty():
    """
    Verify behavior with empty input.
    """
    threshold = detect_percolation_threshold([])
    assert threshold is None