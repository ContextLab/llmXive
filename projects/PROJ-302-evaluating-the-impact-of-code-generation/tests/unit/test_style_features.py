import pytest
from feature_extraction.style_features import (
    calculate_indentation_consistency,
    calculate_line_length_stats,
    calculate_comment_density,
    extract_style_features
)

def test_calculate_indentation_consistent():
    """Test indentation consistency for well-indented code."""
    code = """def func():
    if True:
  print("Hello")
"""
    score = calculate_indentation_consistency(code)
    assert score == 1.0  # Perfectly consistent

def test_calculate_indentation_inconsistent():
    """Test indentation consistency for poorly-indented code."""
    code = """def func():
   if True:
    print("Hello")
"""
    score = calculate_indentation_consistency(code)
    assert score < 1.0

def test_calculate_line_length_stats():
    """Test line length statistics."""
    code = "line1\nvery_long_line_that_exceeds_limit\nshort\n"
    stats = calculate_line_length_stats(code)
    
    assert 'mean' in stats
    assert 'max' in stats
    assert stats['max'] > stats['mean']

def test_calculate_comment_density():
    """Test comment density calculation."""
    code = """# This is a comment
def func():
    pass
"""
    density = calculate_comment_density(code)
    assert 0 < density < 1

def test_extract_style_features():
    """Test extraction of all style features."""
    code = """# Header comment
def example():
    x = 1
    y = 2
    return x + y
"""
    features = extract_style_features(code)
    
    assert 'indentation_consistency' in features
    assert 'line_length_mean' in features
    assert 'comment_density' in features