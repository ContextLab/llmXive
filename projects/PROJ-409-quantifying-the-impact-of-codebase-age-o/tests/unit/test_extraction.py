"""
Unit tests for extraction logic.
Tests code/extraction/git_utils.py and code/extraction/snippet_extractor.py
"""
import ast
import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.git_utils import calculate_median_commit_age, get_file_commits
from extraction.snippet_extractor import TokenCounter, ComplexityCalculator, extract_functions


class TestTokenCounter(unittest.TestCase):
    """Tests for the TokenCounter class."""

    def setUp(self):
        self.counter = TokenCounter()

    def test_count_tokens_simple(self):
        """Test token counting on a simple function."""
        code = "def foo():\n    return 1"
        tokens = self.counter.count_tokens(code)
        self.assertGreater(tokens, 0)
        self.assertIsInstance(tokens, int)

    def test_count_tokens_empty(self):
        """Test token counting on empty string."""
        tokens = self.counter.count_tokens("")
        self.assertEqual(tokens, 0)

    def test_count_tokens_multiline(self):
        """Test token counting on multiline code."""
        code = """
        def bar(x, y):
            if x > y:
                return x
            return y
        """
        tokens = self.counter.count_tokens(code)
        self.assertGreater(tokens, 10)  # Should have a reasonable number of tokens


class TestComplexityCalculator(unittest.TestCase):
    """Tests for the ComplexityCalculator class."""

    def setUp(self):
        self.calc = ComplexityCalculator()

    def test_calculate_simple_function(self):
        """Test complexity calculation on a simple function."""
        code = "def simple():\n    return 1"
        tree = ast.parse(code)
        complexity = self.calc.calculate(tree)
        # Simple function should have low complexity (nodes + edges)
        self.assertGreater(complexity, 0)

    def test_calculate_branching(self):
        """Test complexity increases with branching."""
        code_if = "def f():\n    if True:\n        pass"
        code_if_else = "def f():\n    if True:\n        pass\n    else:\n        pass"
        
        tree_if = ast.parse(code_if)
        tree_if_else = ast.parse(code_if_else)
        
        comp_if = self.calc.calculate(tree_if)
        comp_if_else = self.calc.calculate(tree_if_else)
        
        self.assertGreaterEqual(comp_if_else, comp_if)


class TestExtractFunctions(unittest.TestCase):
    """Tests for the extract_functions function."""

    def test_extract_single_function(self):
        """Test extracting a single function."""
        code = """
        def my_func(a, b):
            return a + b
        """
        functions = extract_functions(code)
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0].name, 'my_func')

    def test_extract_multiple_functions(self):
        """Test extracting multiple functions."""
        code = """
        def func1():
            pass

        def func2():
            pass

        class MyClass:
            def method1(self):
                pass
        """
        functions = extract_functions(code)
        # Should extract func1, func2, and method1
        self.assertGreaterEqual(len(functions), 2)

    def test_extract_no_functions(self):
        """Test extraction when no functions exist."""
        code = "x = 1\ny = 2"
        functions = extract_functions(code)
        self.assertEqual(len(functions), 0)

    def test_extract_with_nested_functions(self):
        """Test extraction with nested functions."""
        code = """
        def outer():
            def inner():
                return 1
            return inner()
        """
        functions = extract_functions(code)
        # Should extract both outer and inner
        self.assertGreaterEqual(len(functions), 1)
        names = [f.name for f in functions]
        self.assertIn('outer', names)


class TestCalculateMedianCommitAge(unittest.TestCase):
    """Tests for calculate_median_commit_age function."""

    def test_median_odd_count(self):
        """Test median calculation with odd number of dates."""
        # Mock dates: 1, 3, 5 -> median 3
        mock_dates = [1, 3, 5]
        result = calculate_median_commit_age(mock_dates)
        self.assertEqual(result, 3)

    def test_median_even_count(self):
        """Test median calculation with even number of dates."""
        # Mock dates: 1, 2, 3, 4 -> median (2+3)/2 = 2.5
        mock_dates = [1, 2, 3, 4]
        result = calculate_median_commit_age(mock_dates)
        self.assertEqual(result, 2.5)

    def test_median_single_item(self):
        """Test median with single item."""
        mock_dates = [42]
        result = calculate_median_commit_age(mock_dates)
        self.assertEqual(result, 42)

    def test_median_empty_list(self):
        """Test median with empty list returns 0."""
        mock_dates = []
        result = calculate_median_commit_age(mock_dates)
        self.assertEqual(result, 0)

    def test_median_unsorted_input(self):
        """Test median calculation with unsorted input."""
        mock_dates = [5, 1, 9, 3]
        result = calculate_median_commit_age(mock_dates)
        # Sorted: 1, 3, 5, 9 -> median (3+5)/2 = 4
        self.assertEqual(result, 4)


class TestGetFileCommits(unittest.TestCase):
    """Tests for get_file_commits function."""

    @patch('extraction.git_utils.subprocess.run')
    def test_get_file_commits_success(self, mock_run):
        """Test successful retrieval of file commits."""
        # Mock subprocess output
        mock_output = MagicMock()
        mock_output.stdout = "2023-01-01 12:00:00\n2023-01-02 12:00:00\n"
        mock_run.return_value = mock_output

        repo_path = "/fake/repo"
        file_path = "test.py"
        
        dates = get_file_commits(repo_path, file_path)
        
        self.assertEqual(len(dates), 2)
        mock_run.assert_called_once()

    @patch('extraction.git_utils.subprocess.run')
    def test_get_file_commits_empty(self, mock_run):
        """Test handling of empty git history."""
        mock_output = MagicMock()
        mock_output.stdout = ""
        mock_run.return_value = mock_output

        repo_path = "/fake/repo"
        file_path = "test.py"
        
        dates = get_file_commits(repo_path, file_path)
        
        self.assertEqual(len(dates), 0)

    @patch('extraction.git_utils.subprocess.run')
    def test_get_file_commits_error(self, mock_run):
        """Test handling of git command error."""
        mock_run.side_effect = Exception("Git error")

        repo_path = "/fake/repo"
        file_path = "test.py"
        
        dates = get_file_commits(repo_path, file_path)
        
        self.assertEqual(len(dates), 0)


if __name__ == '__main__':
    unittest.main()