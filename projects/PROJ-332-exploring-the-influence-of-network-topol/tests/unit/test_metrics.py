import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from regression_analysis import detect_percolation_threshold

def test_percolation_threshold_logic():
    # Same as in test_regression.py but isolated
    results = [
        {'avg_degree': 1.0, 'percolation_flag': 0},
        {'avg_degree': 1.0, 'percolation_flag': 0},
        {'avg_degree': 2.0, 'percolation_flag': 1},
        {'avg_degree': 2.0, 'percolation_flag': 1},
        {'avg_degree': 3.0, 'percolation_flag': 1},
    ]
    threshold = detect_percolation_threshold(results)
    assert threshold == 2.0
