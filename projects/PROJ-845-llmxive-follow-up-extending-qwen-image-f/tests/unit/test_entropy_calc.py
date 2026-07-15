"""
Unit tests for entropy calculation functions.
"""
import sys
import os

# Add the project root to the path to allow imports from code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.metrics import compute_entropy, compute_trace_entropy, compute_entropy_statistics

def test_compute_entropy_returns_float():
    """Test that compute_entropy returns a float."""
    tokens = ["a", "b", "a", "c", "b", "a"]
    result = compute_entropy(tokens)
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    assert result >= 0.0, "Entropy cannot be negative"
    
def test_compute_entropy_empty_list():
    """Test that compute_entropy returns 0.0 for empty list."""
    result = compute_entropy([])
    assert isinstance(result, float)
    assert result == 0.0
    
def test_compute_trace_entropy_returns_float():
    """Test that compute_trace_entropy returns a float."""
    problem = {"id": "test-123"}
    trace = ["token1", "token2", "token1"]
    result = compute_trace_entropy(problem, trace)
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    
def test_compute_entropy_statistics_returns_dict_with_floats():
    """Test that compute_entropy_statistics returns a dict with float values."""
    high = [1.5, 2.0, 2.5, 3.0]
    low = [0.5, 0.8, 1.0, 1.2]
    
    result = compute_entropy_statistics(high, low)
    
    assert isinstance(result, dict)
    assert "mean_high" in result
    assert "mean_low" in result
    assert "p_value" in result
    
    assert isinstance(result["mean_high"], float)
    assert isinstance(result["mean_low"], float)
    assert isinstance(result["p_value"], float)