"""
Unit tests for validation.py metrics and rubric logic.
Ensures LOC, CC, and rubric evaluation work correctly on real code structures.
"""

import ast
import os
import tempfile
import shutil
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validation import (
    calculate_loc,
    calculate_cyclomatic_complexity,
    analyze_file_metrics,
    check_documentation_criteria,
    evaluate_repository_rubric
)

class TestLocCalculation:
    def test_simple_function_loc(self):
        code = """
def hello():
    print("world")
"""
        tree = ast.parse(code)
        loc = calculate_loc(tree)
        assert loc == 3

    def test_class_with_methods_loc(self):
        code = """
class MyClass:
    def method1(self):
  pass
    
    def method2(self):
  pass
"""
        tree = ast.parse(code)
        loc = calculate_loc(tree)
        # Should span from class def to last method
        assert loc >= 6

class TestCyclomaticComplexity:
    def test_simple_function_cc(self):
        code = """
def simple():
    return 1
"""
        tree = ast.parse(code)
        cc = calculate_cyclomatic_complexity(tree)
        assert cc == 1

    def test_if_else_cc(self):
        code = """
def check(x):
    if x > 0:
  return 1
    else:
  return 0
"""
        tree = ast.parse(code)
        cc = calculate_cyclomatic_complexity(tree)
        assert cc == 2  # 1 base + 1 if

    def test_loop_and_exception_cc(self):
        code = """
def process(items):
    try:
  for i in items:
      if i:
          print(i)
    except:
  pass
"""
        tree = ast.parse(code)
        cc = calculate_cyclomatic_complexity(tree)
        # 1 base + 1 for + 1 if + 1 except = 4
        assert cc == 4

class TestFileMetrics:
    def test_analyze_real_file(self):
        # Create a temp file with known content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def add(a, b):
    if a > 0:
  return a + b
    return 0
""")
            temp_path = f.name

        try:
            metrics = analyze_file_metrics(temp_path)
            assert metrics is not None
            assert "loc" in metrics
            assert "cyclomatic_complexity" in metrics
            assert metrics["cyclomatic_complexity"] >= 2
        finally:
            os.unlink(temp_path)

class TestRubricEvaluation:
    def test_full_rubric_pass(self):
        criteria = {
            "has_readme": True,
            "has_setup_instructions": True,
            "has_api_reference": True,
            "details": {}
        }
        result = evaluate_repository_rubric(criteria)
        assert result["final_score"] == 1.0
        assert result["passed_threshold"] is True

    def test_partial_rubric_fail(self):
        criteria = {
            "has_readme": True,
            "has_setup_instructions": False,
            "has_api_reference": False,
            "details": {}
        }
        result = evaluate_repository_rubric(criteria)
        assert result["final_score"] == 1.0 / 3.0
        assert result["passed_threshold"] is False