"""
Unit tests for code/transform/stripper/comment_stripper.py
verifying that 'strip comments' removes # lines and docstrings
but preserves the original logic.
"""
import ast
import pytest
import sys
import os

# Add the code directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from transform.stripper.comment_stripper import (
    CommentRemover,
    strip_comments_and_docstrings
)

# Sample code snippets for testing
SAMPLE_CODE_WITH_COMMENTS = """
# This is a module level comment
def calculate_sum(a, b):
    # This function adds two numbers
    result = a + b  # Inline comment
    return result

# Class definition comment
class Calculator:
    '''This is a class docstring'''
    
    def __init__(self):
        # Initialize the calculator
        self.value = 0
        '''Inline docstring in method'''
    
    def add(self, x):
        # Add x to value
        self.value += x
        return self.value
"""

SAMPLE_CODE_WITH_MULTILINE_STRINGS = """
def process_data(data):
    \"\"\"
    This is a multi-line docstring
    that should be removed.
    \"\"\"
    # Comment before logic
    result = []
    for item in data:
        if item > 0:
            # Only positive numbers
            result.append(item * 2)
    return result
"""

SAMPLE_CODE_WITH_TRIPLE_QUOTED_STRINGS = '''
def get_description():
    """This is a docstring that should be removed."""
    # Comment
    description = "This is a string with \\"quotes\\" inside"
    # Another comment
    multi_line = """
    This is a multi-line string that is NOT a docstring
    and should be preserved.
    """
    return description + multi_line
'''

SAMPLE_CODE_NO_COMMENTS = """
def simple_function(x):
    return x * 2
"""

class TestCommentStripping:
    """Test suite for comment stripping functionality."""

    def test_remove_single_line_comments(self):
        """Verify that # comments are removed but logic is preserved."""
        stripped = strip_comments_and_docstrings(SAMPLE_CODE_WITH_COMMENTS)
        
        # Parse the stripped code to ensure it's valid Python
        try:
            tree = ast.parse(stripped)
        except SyntaxError as e:
            pytest.fail(f"Stripped code has syntax error: {e}")
        
        # Check that comment characters are not present in the output
        assert "#" not in stripped, "Single-line comments were not removed"
        
        # Verify key logic is preserved
        assert "def calculate_sum(a, b):" in stripped
        assert "result = a + b" in stripped
        assert "return result" in stripped
        assert "class Calculator:" in stripped
        assert "self.value = 0" in stripped
        assert "self.value += x" in stripped
        assert "return self.value" in stripped

    def test_remove_docstrings(self):
        """Verify that docstrings are removed but function definitions remain."""
        stripped = strip_comments_and_docstrings(SAMPLE_CODE_WITH_COMMENTS)
        
        # Check that docstring markers are removed
        assert '"""' not in stripped or stripped.count('"""') == 0, "Docstrings were not removed"
        assert "'''" not in stripped or stripped.count("'''") == 0, "Single-quote docstrings were not removed"
        
        # Verify function signatures remain
        assert "def calculate_sum(a, b):" in stripped
        assert "def __init__(self):" in stripped
        assert "def add(self, x):" in stripped

    def test_preserve_multiline_strings_that_are_not_docstrings(self):
        """Verify that triple-quoted strings that are assignments are preserved."""
        stripped = strip_comments_and_docstrings(SAMPLE_CODE_WITH_TRIPLE_QUOTED_STRINGS)
        
        try:
            tree = ast.parse(stripped)
        except SyntaxError as e:
            pytest.fail(f"Stripped code has syntax error: {e}")
        
        # The multi-line string assignment should be preserved
        assert "multi_line" in stripped
        # The actual string content might be formatted differently but the assignment should exist
        assert "multi_line = " in stripped

    def test_preserve_logic_with_inline_comments(self):
        """Verify that code with inline comments has logic preserved."""
        stripped = strip_comments_and_docstrings(SAMPLE_CODE_WITH_COMMENTS)
        
        # Ensure the logic flow is intact
        lines = stripped.split('\n')
        logic_found = {
            'def_calculate_sum': False,
            'result_assignment': False,
            'return_result': False,
            'class_calculator': False,
            'init_method': False,
            'add_method': False
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('def calculate_sum'):
                logic_found['def_calculate_sum'] = True
            elif 'result = a + b' in line:
                logic_found['result_assignment'] = True
            elif line == 'return result':
                logic_found['return_result'] = True
            elif line.startswith('class Calculator'):
                logic_found['class_calculator'] = True
            elif line.startswith('def __init__'):
                logic_found['init_method'] = True
            elif line.startswith('def add'):
                logic_found['add_method'] = True
        
        assert all(logic_found.values()), f"Missing logic in stripped code: {logic_found}"

    def test_empty_code_handling(self):
        """Verify handling of empty or comment-only code."""
        empty_code = "# Just a comment\n"
        stripped = strip_comments_and_docstrings(empty_code)
        assert stripped.strip() == "", "Empty code should result in empty string"
        
        multiline_comments = """
        # Comment 1
        # Comment 2
        '''
        Docstring
        '''
        """
        stripped = strip_comments_and_docstrings(multiline_comments)
        assert stripped.strip() == "", "Comment-only code should result in empty string"

    def test_complex_nesting_preserved(self):
        """Verify that complex nested structures are preserved correctly."""
        complex_code = """
        def outer():
            # Outer comment
            if True:
                # Inner comment
                for i in range(10):
                    # Loop comment
                    def inner():
                        '''Inner docstring'''
                        # Another comment
                        return i
                return inner()
        """
        stripped = strip_comments_and_docstrings(complex_code)
        
        try:
            tree = ast.parse(stripped)
        except SyntaxError as e:
            pytest.fail(f"Stripped complex code has syntax error: {e}")
        
        # Verify structure is preserved
        assert "def outer():" in stripped
        assert "if True:" in stripped
        assert "for i in range(10):" in stripped
        assert "def inner():" in stripped
        assert "return i" in stripped
        assert "return inner()" in stripped

    def test_stripper_class_direct_usage(self):
        """Test the CommentRemover class directly."""
        remover = CommentRemover()
        result = remover.strip(SAMPLE_CODE_WITH_COMMENTS)
        
        try:
            ast.parse(result)
        except SyntaxError as e:
            pytest.fail(f"CommentRemover produced invalid syntax: {e}")
        
        assert "#" not in result
        assert '"""' not in result
        assert "'''" not in result

    def test_preserve_string_literals_with_hash(self):
        """Verify that # inside string literals is preserved."""
        code_with_hash_in_string = """
        def get_url():
            # This is a comment
            url = "http://example.com/path#fragment"
            return url
        """
        stripped = strip_comments_and_docstrings(code_with_hash_in_string)
        
        try:
            ast.parse(stripped)
        except SyntaxError as e:
            pytest.fail(f"Stripped code has syntax error: {e}")
        
        # The hash inside the string should be preserved
        assert "http://example.com/path#fragment" in stripped
        # The comment should be removed
        assert "This is a comment" not in stripped

    def test_preserve_escaped_characters(self):
        """Verify that escaped characters in strings are preserved."""
        code_with_escapes = """
        def process_text():
            # Comment to remove
            text = "Line1\\nLine2\\tTab"
            return text
        """
        stripped = strip_comments_and_docstrings(code_with_escapes)
        
        try:
            ast.parse(stripped)
        except SyntaxError as e:
            pytest.fail(f"Stripped code has syntax error: {e}")
        
        assert "Line1\\nLine2\\tTab" in stripped

    def test_consistency_with_ast_parsing(self):
        """Verify that the stripped code produces the same AST structure (ignoring comments)."""
        original_ast = ast.parse(SAMPLE_CODE_WITH_COMMENTS)
        stripped = strip_comments_and_docstrings(SAMPLE_CODE_WITH_COMMENTS)
        stripped_ast = ast.parse(stripped)
        
        # Compare the number of top-level nodes
        assert len(original_ast.body) == len(stripped_ast.body), \
            "Top-level node count mismatch"
        
        # Compare function names
        original_funcs = [node.name for node in original_ast.body if isinstance(node, ast.FunctionDef)]
        stripped_funcs = [node.name for node in stripped_ast.body if isinstance(node, ast.FunctionDef)]
        assert original_funcs == stripped_funcs, "Function names mismatch"
        
        # Compare class names
        original_classes = [node.name for node in original_ast.body if isinstance(node, ast.ClassDef)]
        stripped_classes = [node.name for node in stripped_ast.body if isinstance(node, ast.ClassDef)]
        assert original_classes == stripped_classes, "Class names mismatch"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])