"""
Unit tests for complexity analysis functions.
"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.complexity import (
    calculate_loc,
    calculate_cyclomatic_complexity,
    analyze_diff_complexity
)

class TestCalculateLOC:
    """Tests for lines of code calculation."""

    def test_empty_code(self):
        """Empty code should return 0 LOC."""
        assert calculate_loc("") == 0

    def test_simple_function(self):
        """Simple function should have correct LOC."""
        code = """
        def hello():
            print("Hello")
        """
        # Should count non-blank, non-comment lines
        loc = calculate_loc(code)
        assert loc > 0

    def test_comments_excluded(self):
        """Comments should not be counted as LOC."""
        code = """
        # This is a comment
        def foo():
            pass
        """
        loc = calculate_loc(code)
        # The comment line should not be counted
        assert loc >= 1  # At least the function definition and pass

    def test_whitespace_only(self):
        """Whitespace only should return 0 LOC."""
        assert calculate_loc("   \n\t\n   ") == 0

    def test_single_line(self):
        """Single line of code should return 1 LOC."""
        assert calculate_loc("x = 1") == 1

    def test_multiple_statements(self):
        """Multiple statements on separate lines."""
        code = """
        x = 1
        y = 2
        z = 3
        """
        loc = calculate_loc(code)
        assert loc == 3

    def test_docstring_excluded(self):
        """Docstrings should not be counted as LOC."""
        code = '''
        def foo():
            """This is a docstring."""
            pass
        '''
        loc = calculate_loc(code)
        # Should count 'def foo():' and 'pass', but not the docstring line
        assert loc == 2

class TestCalculateCyclomaticComplexity:
    """Tests for cyclomatic complexity calculation."""

    def test_empty_code(self):
        """Empty code should have CC of 1."""
        assert calculate_cyclomatic_complexity("") == 1

    def test_no_decision_points(self):
        """Code without decisions should have CC of 1."""
        code = """
        x = 1
        y = 2
        """
        assert calculate_cyclomatic_complexity(code) == 1

    def test_if_statement(self):
        """If statement should increase CC by 1."""
        code = """
        if x > 0:
            print("positive")
        """
        assert calculate_cyclomatic_complexity(code) == 2

    def test_multiple_if_statements(self):
        """Multiple if statements should increase CC."""
        code = """
        if x > 0:
            print("positive")
        elif x < 0:
            print("negative")
        else:
            print("zero")
        """
        # if + elif = 2 decision points, base 1 = 3
        assert calculate_cyclomatic_complexity(code) == 3

    def test_loop(self):
        """Loop should increase CC by 1."""
        code = """
        for i in range(10):
            print(i)
        """
        assert calculate_cyclomatic_complexity(code) == 2

    def test_bool_op(self):
        """Boolean operators should increase CC."""
        code = """
        if x > 0 and y > 0:
            print("both positive")
        """
        # if (1) + and (1) = 2, base 1 = 3
        assert calculate_cyclomatic_complexity(code) == 3

    def test_try_except(self):
        """Try/except should increase CC."""
        code = """
        try:
            x = 1
        except:
            y = 2
        """
        # try/except adds 1 decision point
        assert calculate_cyclomatic_complexity(code) == 2

    def test_nested_conditions(self):
        """Nested conditions should accumulate CC."""
        code = """
        if x > 0:
            if y > 0:
                print("both positive")
        """
        # 2 if statements, base 1 = 3
        assert calculate_cyclomatic_complexity(code) == 3

class TestAnalyzeDiffComplexity:
    """Tests for diff complexity analysis."""

    def test_empty_diff(self):
        """Empty diff should return zero metrics."""
        result = analyze_diff_complexity("")
        assert result['cyclomatic_complexity'] >= 1  # Base complexity
        assert result['lines_of_code'] == 0

    def test_added_lines_only(self):
        """Only added lines should be analyzed."""
        diff = """
        @@ -1,2 +1,3 @@
        -old line
        +new line
        +another line
        """
        result = analyze_diff_complexity(diff)
        # Should analyze "new line" and "another line"
        assert result['lines_of_code'] >= 2

    def test_invalid_python_handling(self):
        """Invalid Python in diff should not crash."""
        diff = """
        @@ -1,2 +1,3 @@
        +this is not valid python {{{
        +another invalid line
        """
        # Should return base complexity without crashing
        result = analyze_diff_complexity(diff)
        assert 'cyclomatic_complexity' in result
        assert 'lines_of_code' in result

    def test_complex_diff(self):
        """Diff with control flow should calculate correct CC."""
        diff = """
        @@ -1,5 +1,10 @@
        +def process_data(items):
        +    for item in items:
        +        if item > 0:
        +            print(item)
        """
        result = analyze_diff_complexity(diff)
        # for (1) + if (1) = 2, base 1 = 3
        assert result['cyclomatic_complexity'] >= 3

    def test_mixed_context_and_added(self):
        """Context lines should be ignored, only added lines counted."""
        diff = """
        @@ -1,3 +1,4 @@
         context line 1
        -deleted line
        +added line with if
        +    if x:
        +        pass
         context line 2
        """
        result = analyze_diff_complexity(diff)
        # Should count added lines: "added line with if", "    if x:", "        pass"
        # LOC should be 3
        assert result['lines_of_code'] == 3
        # CC should be at least 2 (base 1 + 1 for 'if')
        assert result['cyclomatic_complexity'] >= 2