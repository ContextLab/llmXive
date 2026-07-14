"""
Unit tests for mutation logic in code/data/curate.py.

Tests variable renaming, comment removal, control flow reordering,
and API signature changes to ensure synthetic issues are valid.
"""
import ast
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.curate import (
    mutate_variable_names,
    remove_comments,
    reorder_control_flow,
    change_api_signature,
    is_code_valid
)


class TestMutationLogic:
    """Test suite for code mutation functions."""

    def test_mutate_variable_names_valid(self):
        """Test that variable name mutation produces valid Python."""
        original_code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
  total += num
    return total
"""
        mutated_code = mutate_variable_names(original_code)
        
        # Verify the code is still valid Python
        assert is_code_valid(mutated_code), "Mutated code should be syntactically valid"
        
        # Verify some mutation occurred (variable names changed)
        assert mutated_code != original_code, "Code should be mutated"
        
        # Verify structure is preserved (function definition exists)
        tree = ast.parse(mutated_code)
        assert isinstance(tree.body[0], ast.FunctionDef), "Function definition should be preserved"

    def test_remove_comments_valid(self):
        """Test that comment removal produces valid Python."""
        original_code = """
# This is a comment
def hello():
    # Another comment
    print("Hello")
    """
        
        mutated_code = remove_comments(original_code)
        
        # Verify the code is still valid Python
        assert is_code_valid(mutated_code), "Code without comments should be valid"
        
        # Verify no comments remain
        assert "#" not in mutated_code, "Comments should be removed"
        
        # Verify code structure is preserved
        assert "def hello():" in mutated_code, "Function definition should be preserved"
        assert 'print("Hello")' in mutated_code, "Print statement should be preserved"

    def test_reorder_control_flow_valid(self):
        """Test that control flow reordering produces valid Python."""
        original_code = """
def process_items(items):
    result = []
    for item in items:
  if item > 0:
      result.append(item)
    return result
"""
        mutated_code = reorder_control_flow(original_code)
        
        # Verify the code is still valid Python
        assert is_code_valid(mutated_code), "Reordered code should be syntactically valid"
        
        # Verify structure is preserved
        tree = ast.parse(mutated_code)
        func_node = tree.body[0]
        assert isinstance(func_node, ast.FunctionDef), "Function definition should be preserved"
        
        # Verify the function body contains the expected elements
        has_loop = any(isinstance(node, ast.For) for node in ast.walk(func_node))
        has_if = any(isinstance(node, ast.If) for node in ast.walk(func_node))
        assert has_loop, "For loop should be preserved"
        assert has_if, "If statement should be preserved"

    def test_change_api_signature_valid(self):
        """Test that API signature changes produce valid Python."""
        original_code = """
def calculate_area(width, height):
    return width * height
"""
        mutated_code = change_api_signature(original_code)
        
        # Verify the code is still valid Python
        assert is_code_valid(mutated_code), "Modified signature should be valid"
        
        # Verify function definition exists
        tree = ast.parse(mutated_code)
        assert isinstance(tree.body[0], ast.FunctionDef), "Function definition should be preserved"

    def test_is_code_valid_true(self):
        """Test that valid code returns True."""
        valid_code = """
def example():
    return 42
"""
        assert is_code_valid(valid_code) is True

    def test_is_code_valid_false(self):
        """Test that invalid code returns False."""
        invalid_code = """
def example(:
    return 42
"""
        assert is_code_valid(invalid_code) is False

    def test_is_code_valid_syntax_error(self):
        """Test code with syntax errors."""
        invalid_code = """
if True
    print("Missing colon")
"""
        assert is_code_valid(invalid_code) is False

    def test_mutate_preserves_semantics_structure(self):
        """Test that mutations preserve the basic structure of code."""
        original_code = """
def complex_function(a, b, c):
    # Calculate intermediate values
    x = a + b
    y = b * c
    z = x + y
    
    if z > 10:
  result = z * 2
    else:
  result = z / 2
    
    return result
"""
        mutated_code = mutate_variable_names(original_code)
        
        # Parse both to compare structure
        original_tree = ast.parse(original_code)
        mutated_tree = ast.parse(mutated_code)
        
        # Both should have one function definition
        assert len(original_tree.body) == len(mutated_tree.body) == 1
        assert isinstance(mutated_tree.body[0], ast.FunctionDef)
        
        # Function should have same number of arguments
        orig_func = original_tree.body[0]
        mut_func = mutated_tree.body[0]
        assert len(orig_func.args.args) == len(mut_func.args.args)

    def test_remove_comments_preserves_code(self):
        """Test that removing comments doesn't remove code."""
        original_code = """
# Comment 1
def test():
    # Comment 2
    x = 1
    y = 2
    z = x + y
    return z
"""
        mutated_code = remove_comments(original_code)
        
        # All code statements should still be present
        assert "def test():" in mutated_code
        assert "x = 1" in mutated_code
        assert "y = 2" in mutated_code
        assert "z = x + y" in mutated_code
        assert "return z" in mutated_code

    def test_multiple_mutations_chain(self):
        """Test that multiple mutations can be chained."""
        original_code = """
# Original code
def process(data):
    # Process data
    result = []
    for item in data:
  if item is not None:
      result.append(item)
    return result
"""
        # Apply multiple mutations
        step1 = remove_comments(original_code)
        step2 = mutate_variable_names(step1)
        step3 = reorder_control_flow(step2)
        
        # All steps should produce valid code
        assert is_code_valid(step1)
        assert is_code_valid(step2)
        assert is_code_valid(step3)
        
        # Final result should be different from original
        assert step3 != original_code


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])