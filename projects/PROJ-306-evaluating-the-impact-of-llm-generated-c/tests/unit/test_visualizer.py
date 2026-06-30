"""
Unit tests for pattern extraction logic in code/visualizer.py.

This test suite validates the regex-based pattern extraction functions
for loops, conditionals, and recursion detection as specified in US3.
"""
import pytest
import sys
import os
from pathlib import Path

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from visualizer import (
    extract_loop_patterns,
    extract_conditional_patterns,
    extract_recursion_patterns,
    extract_all_patterns
)


class TestLoopPatterns:
    """Tests for loop pattern extraction."""

    def test_for_loop_detection(self):
        """Should detect standard for loops."""
        code = """
        for i in range(10):
            print(i)
        """
        patterns = extract_loop_patterns(code)
        assert len(patterns) > 0
        assert any("for" in p for p in patterns)

    def test_while_loop_detection(self):
        """Should detect while loops."""
        code = """
        while condition:
            do_something()
        """
        patterns = extract_loop_patterns(code)
        assert len(patterns) > 0
        assert any("while" in p for p in patterns)

    def test_nested_loops_detection(self):
        """Should detect nested loops."""
        code = """
        for i in range(5):
            for j in range(5):
                print(i, j)
        """
        patterns = extract_loop_patterns(code)
        assert len(patterns) >= 2

    def test_no_loops(self):
        """Should return empty list for code without loops."""
        code = """
        def hello():
            print("Hello")
        """
        patterns = extract_loop_patterns(code)
        assert len(patterns) == 0

    def test_empty_code(self):
        """Should handle empty code."""
        patterns = extract_loop_patterns("")
        assert len(patterns) == 0


class TestConditionalPatterns:
    """Tests for conditional pattern extraction."""

    def test_if_statement_detection(self):
        """Should detect if statements."""
        code = """
        if x > 0:
            print("positive")
        """
        patterns = extract_conditional_patterns(code)
        assert len(patterns) > 0
        assert any("if" in p for p in patterns)

    def test_else_detection(self):
        """Should detect else blocks."""
        code = """
        if x > 0:
            print("positive")
        else:
            print("non-positive")
        """
        patterns = extract_conditional_patterns(code)
        assert len(patterns) >= 2
        assert any("else" in p for p in patterns)

    def test_elif_detection(self):
        """Should detect elif blocks."""
        code = """
        if x > 0:
            print("positive")
        elif x < 0:
            print("negative")
        else:
            print("zero")
        """
        patterns = extract_conditional_patterns(code)
        assert len(patterns) >= 3
        assert any("elif" in p for p in patterns)

    def test_no_conditionals(self):
        """Should return empty list for code without conditionals."""
        code = """
        def add(a, b):
            return a + b
        """
        patterns = extract_conditional_patterns(code)
        assert len(patterns) == 0


class TestRecursionPatterns:
    """Tests for recursion pattern extraction."""

    def test_direct_recursion_detection(self):
        """Should detect direct recursion."""
        code = """
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        """
        patterns = extract_recursion_patterns(code)
        assert len(patterns) > 0
        # Check that the function calls itself
        assert any("factorial" in p for p in patterns)

    def test_mutual_recursion_detection(self):
        """Should detect mutual recursion."""
        code = """
        def is_even(n):
            if n == 0:
                return True
            return is_odd(n - 1)

        def is_odd(n):
            if n == 0:
                return False
            return is_even(n - 1)
        """
        patterns = extract_recursion_patterns(code)
        assert len(patterns) > 0

    def test_no_recursion(self):
        """Should return empty list for non-recursive code."""
        code = """
        def add(a, b):
            return a + b

        result = add(1, 2)
        """
        patterns = extract_recursion_patterns(code)
        assert len(patterns) == 0

    def test_empty_code(self):
        """Should handle empty code."""
        patterns = extract_recursion_patterns("")
        assert len(patterns) == 0


class TestExtractAllPatterns:
    """Tests for combined pattern extraction."""

    def test_complex_function(self):
        """Should extract all pattern types from complex code."""
        code = """
        def process_data(items):
            result = []
            for item in items:
                if item > 0:
                    result.append(item)
                elif item < 0:
                    result.append(-item)
                else:
                    continue
            return result

        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        """
        patterns = extract_all_patterns(code)
        
        # Check that all categories are present
        assert "loops" in patterns
        assert "conditionals" in patterns
        assert "recursion" in patterns
        
        # Check counts
        assert len(patterns["loops"]) > 0
        assert len(patterns["conditionals"]) > 0
        assert len(patterns["recursion"]) > 0

    def test_simple_function(self):
        """Should handle simple functions with no patterns."""
        code = """
        def add(a, b):
            return a + b
        """
        patterns = extract_all_patterns(code)
        
        assert "loops" in patterns
        assert "conditionals" in patterns
        assert "recursion" in patterns
        
        assert len(patterns["loops"]) == 0
        assert len(patterns["conditionals"]) == 0
        assert len(patterns["recursion"]) == 0

    def test_empty_input(self):
        """Should handle empty input gracefully."""
        patterns = extract_all_patterns("")
        
        assert patterns == {
            "loops": [],
            "conditionals": [],
            "recursion": []
        }

    def test_none_input(self):
        """Should handle None input gracefully."""
        patterns = extract_all_patterns(None)
        
        assert patterns == {
            "loops": [],
            "conditionals": [],
            "recursion": []
        }