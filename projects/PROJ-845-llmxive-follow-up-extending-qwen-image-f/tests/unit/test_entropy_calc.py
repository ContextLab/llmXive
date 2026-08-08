"""
Unit test for entropy calculation in code/analysis/metrics.py.
"""
import pytest
from code.analysis.metrics import compute_entropy

def test_compute_entropy_returns_float():
    """Test that compute_entropy returns a float."""
    # Test with a simple probability distribution
    probabilities = [0.5, 0.5]
    result = compute_entropy(probabilities)
    
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    # For uniform distribution of 2 elements, entropy should be 1.0 (log2(2))
    assert result == 1.0, f"Expected 1.0 for uniform distribution, got {result}"

def test_compute_entropy_with_single_element():
    """Test entropy with a single probability (should be 0)."""
    probabilities = [1.0]
    result = compute_entropy(probabilities)
    
    assert isinstance(result, float)
    assert result == 0.0, f"Expected 0.0 for single element, got {result}"

def test_compute_entropy_with_empty_list():
    """Test that empty list raises an error or returns 0."""
    probabilities = []
    # Depending on implementation, this might raise or return 0
    try:
        result = compute_entropy(probabilities)
        assert isinstance(result, float)
    except (ValueError, ZeroDivisionError):
        # Expected behavior for empty input
        pass