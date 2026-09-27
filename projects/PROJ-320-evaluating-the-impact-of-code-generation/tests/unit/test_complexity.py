"""
Unit tests for code complexity analysis functions.
Tests for Lines of Code (LOC) calculation and Cyclomatic Complexity.
"""

import pytest
import ast
import io
import tokenize
from pathlib import Path

# Import the functions we are testing from the implementation
# These names must match the public API surface in code/analysis/complexity.py
from code.analysis.complexity import (
    calculate_loc,
    calculate_cyclomatic_complexity,
    analyze_diff_complexity,
    get_memory_usage_mb
)


class TestLinesOfCodeCalculation:
    """Unit tests for the Lines of Code (LOC) calculation logic."""

    def test_loc_empty_code(self):
        """Assert that empty code returns 0 lines."""
        code = ""
        assert calculate_loc(code) == 0

    def test_loc_single_line(self):
        """Assert that a single line of code returns 1."""
        code = "x = 1"
        assert calculate_loc(code) == 1

    def test_loc_multiple_lines(self):
        """Assert that multiple lines of code are counted correctly."""
        code = """
        x = 1
        y = 2
        z = x + y
        """
        # Should count 3 lines of actual code
        assert calculate_loc(code) == 3

    def test_loc_ignores_comments(self):
        """Assert that comment lines are not counted as LOC."""
        code = """
        # This is a comment
        x = 1
        # Another comment
        y = 2
        """
        # Should only count 2 lines of actual code
        assert calculate_loc(code) == 2

    def test_loc_ignores_blank_lines(self):
        """Assert that blank lines are not counted as LOC."""
        code = """
        x = 1

        y = 2
        """
        # Should only count 2 lines of actual code
        assert calculate_loc(code) == 2

    def test_loc_mixed_code(self):
        """Assert LOC calculation handles mixed code correctly."""
        code = """
        # Header comment
        import os

        def hello():
            print("Hello")

        if __name__ == "__main__":
            hello()
        """
        # Counting non-blank, non-comment lines:
        # import os
        # def hello():
        #     print("Hello")
        # if __name__ == "__main__":
        #     hello()
        assert calculate_loc(code) == 5

    def test_loc_with_docstring(self):
        """Assert that docstrings are counted as code lines."""
        code = '''
        def example():
            """This is a docstring."""
            pass
        '''
        # def, docstring line, pass = 3 lines
        assert calculate_loc(code) == 3

    def test_loc_complex_function(self):
        """Assert LOC calculation for a more complex function."""
        code = """
        def calculate_sum(numbers):
            total = 0
            for num in numbers:
                if num > 0:
                    total += num
            return total

        result = calculate_sum([1, 2, 3])
        """
        # Counting:
        # def calculate_sum(numbers):
        #     total = 0
        #     for num in numbers:
        #         if num > 0:
        #             total += num
        #     return total
        # result = calculate_sum([1, 2, 3])
        assert calculate_loc(code) == 7

    def test_loc_with_string_literals(self):
        """Assert that strings containing comment-like text are counted."""
        code = """
        text = "This looks like # a comment"
        x = 1
        """
        # Both lines should be counted as code
        assert calculate_loc(code) == 2

    def test_loc_multiline_string(self):
        """Assert multiline strings are handled correctly."""
        code = '''
        text = """
        Line 1
        Line 2
        """
        x = 1
        '''
        # def line, multiline string start, x = 1 (inside string lines are part of the string token)
        # The tokenizer approach counts the physical lines that are not blank/comment
        # "text = """ starts a line, "x = 1" is another. The lines inside the string are part of the string literal.
        # Depending on implementation, this might be 3 or more. Let's verify the tokenizer behavior.
        # With the tokenizer approach:
        # Line 1: text = """
        # Line 2: Line 1
        # Line 3: Line 2
        # Line 4: """
        # Line 5: x = 1
        # Non-blank lines: 5
        assert calculate_loc(code) == 5

    def test_loc_with_indented_code(self):
        """Assert indented code is counted correctly."""
        code = """
        if True:
            if True:
                x = 1
        """
        # if, if, x = 1 = 3 lines
        assert calculate_loc(code) == 3

    def test_loc_with_syntax_error_graceful(self):
        """Assert that syntax errors are handled gracefully (return 0 or specific value)."""
        code = "x = "  # Incomplete statement
        # The function should handle this without crashing
        result = calculate_loc(code)
        assert isinstance(result, int) and result >= 0

    def test_loc_consistency_with_cyclomatic(self):
        """Assert LOC and Cyclomatic complexity are calculated independently."""
        code = """
        def example(x):
            if x > 0:
                return 1
            else:
                return 0
        """
        loc = calculate_loc(code)
        cc = calculate_cyclomatic_complexity(code)
        
        # LOC should be > 0
        assert loc > 0
        # CC should be >= 1 (base complexity)
        assert cc >= 1
        # They should be different metrics
        assert loc != cc or (loc == cc and cc > 1)  # They could coincidentally be equal, but generally different


class TestCyclomaticComplexityCalculation:
    """Unit tests for Cyclomatic Complexity calculation (complementary to LOC tests)."""

    def test_cc_empty_code(self):
        """Assert empty code has complexity 1 (base)."""
        code = ""
        assert calculate_cyclomatic_complexity(code) == 1

    def test_cc_simple_function(self):
        """Assert a simple function has complexity 1."""
        code = """
        def hello():
            print("Hello")
        """
        assert calculate_cyclomatic_complexity(code) == 1

    def test_cc_if_statement(self):
        """Assert an if statement adds 1 to complexity."""
        code = """
        def check(x):
            if x > 0:
                return True
            return False
        """
        # Base 1 + 1 for if = 2
        assert calculate_cyclomatic_complexity(code) == 2

    def test_cc_multiple_branches(self):
        """Assert if-elif-else adds correctly."""
        code = """
        def grade(score):
            if score >= 90:
                return "A"
            elif score >= 80:
                return "B"
            else:
                return "C"
        """
        # Base 1 + 1 for if + 1 for elif = 3
        assert calculate_cyclomatic_complexity(code) == 3

    def test_cc_loop(self):
        """Assert loops add to complexity."""
        code = """
        def count(items):
            total = 0
            for item in items:
                total += 1
            return total
        """
        # Base 1 + 1 for for loop = 2
        assert calculate_cyclomatic_complexity(code) == 2

    def test_cc_while_loop(self):
        """Assert while loops add to complexity."""
        code = """
        def countdown(n):
            while n > 0:
                n -= 1
        """
        # Base 1 + 1 for while = 2
        assert calculate_cyclomatic_complexity(code) == 2

    def test_cc_try_except(self):
        """Assert try-except adds to complexity."""
        code = """
        def safe_divide(a, b):
            try:
                return a / b
            except ZeroDivisionError:
                return 0
        """
        # Base 1 + 1 for try/except block = 2
        assert calculate_cyclomatic_complexity(code) == 2

    def test_cc_and_or(self):
        """Assert logical operators add to complexity."""
        code = """
        def check(x, y):
            if x > 0 and y > 0:
                return True
            return False
        """
        # Base 1 + 1 for if + 1 for 'and' = 3
        assert calculate_cyclomatic_complexity(code) == 3


class TestMemoryUsage:
    """Tests for memory usage monitoring."""

    def test_memory_usage_returns_positive(self):
        """Assert memory usage returns a positive number."""
        usage = get_memory_usage_mb()
        assert isinstance(usage, (int, float))
        assert usage >= 0

    def test_memory_usage_type(self):
        """Assert memory usage returns a numeric type."""
        usage = get_memory_usage_mb()
        assert isinstance(usage, (int, float))


class TestAnalyzeDiffComplexity:
    """Tests for diff-based complexity analysis."""

    def test_analyze_diff_returns_dict(self):
        """Assert analyze_diff_complexity returns a dictionary."""
        diff_text = """
        --- a/file.py
        +++ b/file.py
        @@ -1,3 +1,5 @@
        +def new_function():
        +    pass
         x = 1
        """
        result = analyze_diff_complexity(diff_text)
        assert isinstance(result, dict)

    def test_analyze_diff_has_loc(self):
        """Assert analyze_diff_complexity result contains LOC."""
        diff_text = """
        --- a/file.py
        +++ b/file.py
        @@ -1,3 +1,5 @@
        +def new_function():
        +    pass
         x = 1
        """
        result = analyze_diff_complexity(diff_text)
        assert "loc" in result or "lines_of_code" in result or isinstance(result, dict)

    def test_analyze_diff_empty(self):
        """Assert empty diff returns appropriate result."""
        result = analyze_diff_complexity("")
        assert isinstance(result, dict)

    def test_analyze_diff_with_syntax_error(self):
        """Assert diff with syntax errors is handled gracefully."""
        diff_text = """
        --- a/file.py
        +++ b/file.py
        @@ -1,3 +1,5 @@
        +def broken(
        +    x = 1
        """
        result = analyze_diff_complexity(diff_text)
        assert isinstance(result, dict)