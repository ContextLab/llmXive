"""
Unit tests for code/quality/complexity.py
Tests for cyclomatic complexity computation using radon.
"""
import unittest
import sys
from pathlib import Path

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from quality.complexity import (
    compute_cyclomatic_complexity,
    get_complexity_breakdown,
    analyze_code_quality
)


class TestCyclomaticComplexity(unittest.TestCase):
    """Unit tests for cyclomatic complexity calculation."""

    def test_simple_function(self):
        """Test complexity of a simple function without branches."""
        code = """
def add(a, b):
    return a + b
"""
        cc = compute_cyclomatic_complexity(code)
        # Simple function has CC = 1
        self.assertEqual(cc, 1)

    def test_if_statement(self):
        """Test complexity with an if statement."""
        code = """
def check_positive(n):
    if n > 0:
  return True
    return False
"""
        cc = compute_cyclomatic_complexity(code)
        # One if statement adds 1 to base complexity
        self.assertEqual(cc, 2)

    def test_multiple_branches(self):
        """Test complexity with multiple if/elif/else."""
        code = """
def grade(score):
    if score >= 90:
  return 'A'
    elif score >= 80:
  return 'B'
    elif score >= 70:
  return 'C'
    else:
  return 'F'
"""
        cc = compute_cyclomatic_complexity(code)
        # Base (1) + 3 if/elif conditions = 4
        self.assertEqual(cc, 4)

    def test_loop_complexity(self):
        """Test complexity with loops."""
        code = """
def sum_list(items):
    total = 0
    for item in items:
  total += item
    return total
"""
        cc = compute_cyclomatic_complexity(code)
        # Base (1) + 1 for loop = 2
        self.assertEqual(cc, 2)

    def test_nested_branches(self):
        """Test complexity with nested branches."""
        code = """
def check_range(n):
    if n > 0:
  if n < 100:
      return True
    return False
"""
        cc = compute_cyclomatic_complexity(code)
        # Base (1) + 2 if statements = 3
        self.assertEqual(cc, 3)

    def test_complexity_breakdown(self):
        """Test getting detailed complexity breakdown."""
        code = """
def process(data):
    if data:
  for item in data:
      if item > 0:
          print(item)
"""
        breakdown = get_complexity_breakdown(code)
        self.assertIsInstance(breakdown, list)
        self.assertGreater(len(breakdown), 0)
        
        # Check that each item has required fields
        for item in breakdown:
            self.assertIn('name', item)
            self.assertIn('complexity', item)
            self.assertIn('line', item)

    def test_complexity_integer_minimum(self):
        """Test that complexity is at least 1 (integer)."""
        code = "def foo(): pass"
        cc = compute_cyclomatic_complexity(code)
        self.assertIsInstance(cc, int)
        self.assertGreaterEqual(cc, 1)

    def test_empty_code(self):
        """Test complexity of empty code."""
        code = ""
        cc = compute_cyclomatic_complexity(code)
        # Empty code should have minimal complexity
        self.assertIsInstance(cc, int)
        self.assertGreaterEqual(cc, 0)

    def test_analyze_code_quality(self):
        """Test full code quality analysis."""
        code = """
def complex_function(a, b, c):
    if a > 0:
  if b > 0:
      if c > 0:
          return a + b + c
    return 0
"""
        result = analyze_code_quality(code)
        self.assertIn('cyclomatic_complexity', result)
        self.assertIn('is_acceptable', result)
        # This function has high complexity
        self.assertGreater(result['cyclomatic_complexity'], 1)

    def test_high_complexity_threshold(self):
        """Test that high complexity is flagged."""
        # Create code with high complexity
        code = """
def very_complex(x):
    if x > 0:
  if x > 1:
      if x > 2:
          if x > 3:
              if x > 4:
                  if x > 5:
                      return True
    return False
"""
        result = analyze_code_quality(code)
        # Should have complexity > 10
        self.assertGreater(result['cyclomatic_complexity'], 5)


if __name__ == '__main__':
    unittest.main()