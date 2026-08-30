import pytest
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.pdf_parser import parse_inequality, extract_effect_sizes

def test_parse_inequality_less_than():
    """Test parsing 'p < 0.05' into (0.0, 0.05, 'inequality')."""
    result = parse_inequality("p < 0.05")
    assert result[0] == 0.0
    assert result[1] == 0.05
    assert result[2] == "inequality"

def test_parse_inequality_greater_than():
    """Test parsing 'p > 0.05' into (0.05, 1.0, 'inequality')."""
    result = parse_inequality("p > 0.05")
    assert result[0] == 0.05
    assert result[1] == 1.0
    assert result[2] == "inequality"

def test_parse_inequality_exact():
    """Test parsing exact p-value."""
    result = parse_inequality("p = 0.03")
    assert result[0] == 0.03
    assert result[1] == 0.03
    assert result[2] == "exact"

def test_extract_cohen_d():
    """Test extraction of Cohen's d with confidence interval."""
    text = "The effect size was large (Cohen's d = 0.5 [0.2, 0.8])."
    results = extract_effect_sizes(text)
    
    # Filter for Cohen's d
    d_results = [r for r in results if r.get('type') == 'cohen_d']
    assert len(d_results) > 0
    
    d = d_results[0]
    assert d['value'] == 0.5
    assert d['ci_lower'] == 0.2
    assert d['ci_upper'] == 0.8

def test_extract_hedges_g():
    """Test extraction of Hedges' g."""
    text = "Hedges' g was calculated as 0.75."
    results = extract_effect_sizes(text)
    g_results = [r for r in results if r.get('type') == 'hedges_g']
    assert len(g_results) > 0
    assert g_results[0]['value'] == 0.75

def test_no_effect_size_found():
    """Test that empty list is returned when no effect size is found."""
    text = "This is a theoretical paper with no statistics."
    results = extract_effect_sizes(text)
    assert len(results) == 0
