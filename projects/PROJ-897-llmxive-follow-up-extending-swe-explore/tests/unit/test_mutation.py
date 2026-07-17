"""
Unit tests for mutation logic (T010).
Tests variable rename, comment removal, and structural obfuscation.
"""
import pytest
from data.curate import mutate_variable_names, remove_comments, reorder_control_flow, change_api_signature, is_code_valid

def test_mutate_variable_names():
    """Test that variable names are changed."""
    code = "x = 1\ny = x + 1"
    mutated = mutate_variable_names(code, seed=42)
    
    # Check that original names are gone (simplified check)
    assert "x = 1" not in mutated
    assert "y = " not in mutated
    # Check that code is still valid
    assert is_code_valid(mutated)

def test_mutate_variable_names_validity():
    """Test that mutated code is always valid."""
    code = """
    def foo(a, b):
        c = a + b
        return c
    """
    mutated = mutate_variable_names(code, seed=123)
    assert is_code_valid(mutated)

def test_remove_comments():
    """Test that comments are removed."""
    code = """
    # This is a comment
    x = 1 # inline comment
    y = 2
    """
    mutated = remove_comments(code)
    assert "#" not in mutated
    assert "x = 1" in mutated
    assert "y = 2" in mutated

def test_reorder_control_flow():
    """Test that control flow is reordered."""
    code = """
    if x > 0:
        print("positive")
    else:
        print("non-positive")
    """
    mutated = reorder_control_flow(code)
    # The logic should be inverted or structure changed
    # We just check it's valid and not identical
    assert mutated != code
    assert is_code_valid(mutated)

def test_change_api_signature():
    """Test that API signatures are changed."""
    code = """
    def my_func(a, b, c):
        return a + b + c
    """
    mutated = change_api_signature(code)
    # Argument names should be generic
    assert "arg_0" in mutated
    assert "arg_1" in mutated
    assert "arg_2" in mutated
    assert "is_code_valid(mutated)"
    assert is_code_valid(mutated)
