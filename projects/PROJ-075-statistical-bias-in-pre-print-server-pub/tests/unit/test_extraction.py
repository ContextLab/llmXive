"""
Unit tests for the PDF parser in utils/pdf_parser.py
"""
import pytest
from utils.pdf_parser import parse_inequality, extract_effect_sizes, extract_p_values

def test_parse_inequality():
    """Test parsing of p-value inequalities.
    
    Expected: "p < 0.05" -> (0.0, 0.05, "inequality")
    """
    result = parse_inequality("p < 0.05")
    assert result is not None
    assert result[0] == 0.0  # lower bound
    assert result[1] == 0.05  # upper bound
    assert result[2] == "inequality"  # type

def test_parse_inequality_greater_than():
    """Test parsing of greater than inequality."""
    result = parse_inequality("p > 0.10")
    assert result is not None
    assert result[0] == 0.10
    assert result[1] == 1.0  # Upper bound for >
    assert result[2] == "inequality"

def test_extract_cohen_d():
    """Test extraction of Cohen's d with confidence interval.
    
    Expected: "d = 0.5 [0.2, 0.8]" -> value=0.5, ci_lower=0.2, ci_upper=0.8
    """
    text = "The effect size was d = 0.5 [0.2, 0.8], indicating a moderate effect."
    results = extract_effect_sizes(text)
    
    assert len(results) > 0
    d_result = results[0]
    assert abs(d_result['value'] - 0.5) < 0.001
    assert abs(d_result['ci_lower'] - 0.2) < 0.001
    assert abs(d_result['ci_upper'] - 0.8) < 0.001
    assert d_result['type'] == 'cohen_d'

def test_extract_p_values_exact():
    """Test extraction of exact p-values."""
    text = "The analysis yielded p = 0.032 for the main effect."
    results = extract_p_values(text)
    
    assert len(results) > 0
    p_result = results[0]
    assert abs(p_result['value'] - 0.032) < 0.001
    assert p_result['type'] == 'exact'

def test_extract_p_values_inequality():
    """Test extraction of p-value inequalities."""
    text = "Results were significant with p < 0.001."
    results = extract_p_values(text)
    
    assert len(results) > 0
    p_result = results[0]
    assert p_result['type'] == 'inequality'
    assert p_result['lower_bound'] == 0.0
    assert p_result['upper_bound'] == 0.001
