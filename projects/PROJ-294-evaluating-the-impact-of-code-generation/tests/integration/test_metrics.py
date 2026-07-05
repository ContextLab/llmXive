"""
Integration test for T019: Verify metric extraction on a known Python snippet.
This test validates that `code/analyze_metrics.py` correctly calculates
Cyclomatic Complexity and Halstead Volume using `radon` on real code snippets.
"""
import os
import sys
import json
import tempfile
import pytest

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analyze_metrics import calculate_code_metrics


def test_cyclomatic_complexity_simple():
    """Test CC on a simple function with no branches."""
    code = """
def add(a, b):
    return a + b
"""
    metrics = calculate_code_metrics(code)
    # Simple function should have CC = 1 (base)
    assert metrics["cyclomatic_complexity"] == 1


def test_cyclomatic_complexity_branches():
    """Test CC on a function with if/else branches."""
    code = """
def check_number(n):
    if n > 0:
        return "positive"
    elif n < 0:
        return "negative"
    else:
        return "zero"
"""
    metrics = calculate_code_metrics(code)
    # 1 base + 3 decision points (if, elif, else) = 4
    assert metrics["cyclomatic_complexity"] == 4


def test_halstead_volume():
    """Test Halstead Volume calculation."""
    code = """
def multiply(a, b):
    return a * b
"""
    metrics = calculate_code_metrics(code)
    # Should be a positive number for valid code
    assert metrics["halstead_volume"] > 0


def test_empty_code():
    """Test handling of empty code."""
    metrics = calculate_code_metrics("")
    assert metrics["cyclomatic_complexity"] == 0
    assert metrics["halstead_volume"] == 0.0


def test_none_code():
    """Test handling of None code."""
    metrics = calculate_code_metrics(None)
    assert metrics["cyclomatic_complexity"] == 0
    assert metrics["halstead_volume"] == 0.0


def test_invalid_syntax():
    """Test handling of invalid Python syntax."""
    code = """
def broken(
    return 1
"""
    # Should not crash, return defaults
    metrics = calculate_code_metrics(code)
    assert metrics["cyclomatic_complexity"] >= 0
    assert metrics["halstead_volume"] >= 0.0


def test_real_world_snippet():
    """Test on a slightly more complex real-world-like snippet."""
    code = """
def process_data(items, threshold):
    results = []
    for item in items:
        if item is not None:
            if item > threshold:
                results.append(item * 2)
            else:
                results.append(item)
        else:
            continue
    return results
"""
    metrics = calculate_code_metrics(code)
    # Verify we get valid numbers
    assert metrics["cyclomatic_complexity"] > 1
    assert metrics["halstead_volume"] > 0
    # Verify structure
    assert "cyclomatic_complexity" in metrics
    assert "halstead_volume" in metrics
    assert "halstead_operators" in metrics
    assert "halstead_operands" in metrics