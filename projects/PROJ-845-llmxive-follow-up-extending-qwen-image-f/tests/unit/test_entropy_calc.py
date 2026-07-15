import sys
import os
import pytest

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.metrics import compute_entropy

def test_entropy_returns_float():
    """Test that the entropy calculation function returns a float."""
    test_string = "hello world"
    result = compute_entropy(test_string)
    
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    assert result >= 0.0, "Entropy cannot be negative"

def test_entropy_empty_string():
    """Test that empty string returns 0.0 entropy."""
    result = compute_entropy("")
    assert result == 0.0

def test_entropy_single_char():
    """Test that single character string returns 0.0 entropy."""
    result = compute_entropy("a")
    assert result == 0.0

def test_entropy_uniform_distribution():
    """Test entropy with uniform distribution of characters."""
    # "ab" has higher entropy than "aa"
    entropy_ab = compute_entropy("ab")
    entropy_aa = compute_entropy("aa")
    
    assert entropy_ab > entropy_aa, "Uniform distribution should have higher entropy"