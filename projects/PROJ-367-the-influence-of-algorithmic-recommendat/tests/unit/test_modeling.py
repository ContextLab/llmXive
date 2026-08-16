"""
Unit tests for code/modeling.py.

Tests baseline vector derivation and weight stability checks.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Ensure code directory is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from modeling import derive_baseline_interest_vector, check_weight_stability


def test_derive_baseline_interest_vector():
    """Test baseline vector derivation from history."""
    # Mock history: user watched Math, Math, Science
    history = ["Math", "Math", "Science"]
    # We expect a vector representing the distribution of these categories
    # The function should return a normalized vector
    vector = derive_baseline_interest_vector(history)
    
    # Check that vector is a numpy array
    assert isinstance(vector, np.ndarray)
    # Check that it sums to 1.0 (normalized)
    assert np.isclose(vector.sum(), 1.0, atol=1e-5)
    # Check that non-zero elements correspond to seen categories
    # (Assuming the function maps categories to indices, here we just check sum)


def test_check_weight_stability_no_extreme():
    """Test weight stability check when no weights are extreme."""
    weights = np.array([1.0, 1.1, 0.9, 1.05, 0.95])
    median_weight = np.median(weights)
    threshold = 10 * median_weight
    
    is_stable, flagged_indices = check_weight_stability(weights)
    
    assert is_stable is True
    assert len(flagged_indices) == 0


def test_check_weight_stability_extreme():
    """Test weight stability check when some weights are extreme."""
    weights = np.array([1.0, 1.0, 1.0, 100.0, 1.0])
    median_weight = np.median(weights) # 1.0
    threshold = 10 * median_weight # 10.0
    
    is_stable, flagged_indices = check_weight_stability(weights)
    
    assert is_stable is False
    assert 3 in flagged_indices # Index of 100.0
