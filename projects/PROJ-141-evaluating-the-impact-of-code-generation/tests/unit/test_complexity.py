"""
Unit tests for cyclomatic complexity calculation (T029).
"""
import pytest
import sys
import os
import json

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from quality.complexity import (
    compute_cyclomatic_complexity,
    get_complexity_breakdown,
    analyze_code_quality
)


class TestCyclomaticComplexity:
    """Tests for cyclomatic complexity calculation."""
    
    def test_empty_code(self):
        """Test that empty code raises ValueError."""
        with pytest.raises(ValueError):
            compute_cyclomatic_complexity("")
        
        with pytest.raises(ValueError):
            compute_cyclomatic_complexity("   ")
    
    def test_simple_function_complexity_one(self):
        """Test that a simple function has complexity 1."""
        code = """
def hello():
    print("Hello, World!")
"""
        result = compute_cyclomatic_complexity(code)
        assert result == 1
    
    def test_if_statement_increases_complexity(self):
        """Test that an if statement increases complexity by 1."""
        code = """
def check_number(x):
    if x > 0:
  return "positive"
    else:
  return "non-positive"
"""
        result = compute_cyclomatic_complexity(code)
        # Base (1) + if (1) = 2
        assert result == 2
    
    def test_multiple_if_statements(self):
        """Test multiple if statements increase complexity."""
        code = """
def classify_number(x):
    if x > 0:
  return "positive"
    if x < 0:
  return "negative"
    return "zero"
"""
        result = compute_cyclomatic_complexity(code)
        # Base (1) + if (1) + if (1) = 3
        assert result == 3
    
    def test_loop_increases_complexity(self):
        """Test that a for loop increases complexity."""
        code = """
def sum_list(items):
    total = 0
    for item in items:
  total += item
    return total
"""
        result = compute_cyclomatic_complexity(code)
        # Base (1) + for (1) = 2
        assert result == 2
    
    def test_nested_conditions(self):
        """Test nested conditions increase complexity."""
        code = """
def complex_check(x, y):
    if x > 0:
  if y > 0:
      return "both positive"
  else:
      return "x positive, y not"
    else:
  return "x not positive"
"""
        result = compute_cyclomatic_complexity(code)
        # Base (1) + if (1) + if (1) + else (0, covered by if) = 3
        # Actually: 1 (base) + 1 (outer if) + 1 (inner if) = 3
        assert result == 3
    
    def test_try_except_increases_complexity(self):
        """Test that try-except increases complexity."""
        code = """
def safe_divide(a, b):
    try:
  return a / b
    except ZeroDivisionError:
  return None
"""
        result = compute_cyclomatic_complexity(code)
        # Base (1) + try (1) = 2 (except is part of try block)
        assert result == 2
    
    def test_complex_function(self):
        """Test a more complex function."""
        code = """
def process_data(data, threshold=10):
    result = []
    for item in data:
  if item > threshold:
      if item % 2 == 0:
          result.append(item * 2)
      else:
          result.append(item)
  else:
      result.append(0)
    return result
"""
        result = compute_cyclomatic_complexity(code)
        # Base (1) + for (1) + if (1) + if (1) + else (0) + else (0) = 4
        assert result == 4
    
    def test_minimum_complexity_is_one(self):
        """Test that complexity is always at least 1."""
        code = "pass"
        result = compute_cyclomatic_complexity(code)
        assert result >= 1
    
    def test_breakdown_includes_all_functions(self):
        """Test that breakdown includes all functions."""
        code = """
def func1():
    pass

def func2():
    if True:
  pass

class MyClass:
    def method1(self):
  pass
"""
        breakdown = get_complexity_breakdown(code)
        names = [item['name'] for item in breakdown]
        assert 'func1' in names
        assert 'func2' in names
        assert 'MyClass' in names
        assert 'method1' in names
    
    def test_analyze_code_quality_returns_dict(self):
        """Test that analyze_code_quality returns a dictionary."""
        code = "def test(): pass"
        result = analyze_code_quality(code)
        assert isinstance(result, dict)
        assert 'cyclomatic_complexity' in result
        assert 'lines_of_code' in result
        assert 'breakdown' in result
    
    def test_syntax_error_handling(self):
        """Test that syntax errors are handled properly."""
        code = "def broken("  # Missing closing parenthesis
        with pytest.raises(SyntaxError):
            compute_cyclomatic_complexity(code)
    
    def test_unsupported_language(self):
        """Test that unsupported languages raise ValueError."""
        code = "print('hello')"
        with pytest.raises(ValueError):
            compute_cyclomatic_complexity(code, language="java")