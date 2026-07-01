"""
Unit tests for code/utils/parsers.py
"""
import pytest
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.parsers import extract_sample_size, extract_effect_size

class TestExtractSampleSize:
    def test_extract_n_equals(self):
        text = "The study included N=150 participants."
        assert extract_sample_size(text) == 150

    def test_extract_n_space_equals(self):
        text = "Sample size = 200 was used."
        assert extract_sample_size(text) == 200

    def test_extract_lowercase_n(self):
        text = "n=50 subjects were recruited."
        assert extract_sample_size(text) == 50

    def test_extract_no_match(self):
        text = "No sample size mentioned here."
        assert extract_sample_size(text) == 0

    def test_extract_empty(self):
        assert extract_sample_size("") == 0
        assert extract_sample_size(None) == 0

    def test_extract_multiple(self):
        # Should return the first match
        text = "N=100 in group A, N=200 in group B."
        assert extract_sample_size(text) == 100

class TestExtractEffectSize:
    def test_extract_cohens_d(self):
        text = "The effect size was Cohen's d = 0.54."
        value, metric, df = extract_effect_size(text)
        assert metric == "Cohen's d"
        assert abs(value - 0.54) < 0.01
        assert df is None

    def test_extract_d_short(self):
        text = "d = 0.8 showed a strong effect."
        value, metric, df = extract_effect_size(text)
        assert metric == "Cohen's d"
        assert abs(value - 0.8) < 0.01

    def test_extract_f_statistic(self):
        text = "Results showed F(1, 20) = 4.56, p < 0.05."
        value, metric, df = extract_effect_size(text)
        assert metric == "F"
        assert abs(value - 4.56) < 0.01
        assert df == (1, 20)

    def test_extract_f_statistic_no_spaces(self):
        text = "F(2,50)=3.21 was significant."
        value, metric, df = extract_effect_size(text)
        assert metric == "F"
        assert abs(value - 3.21) < 0.01
        assert df == (2, 50)

    def test_extract_no_effect_size(self):
        text = "No statistical metrics reported."
        value, metric, df = extract_effect_size(text)
        assert value == 0.0
        assert metric == "None"
        assert df is None

    def test_extract_empty(self):
        value, metric, df = extract_effect_size("")
        assert value == 0.0
        assert metric == "None"
        assert df is None

    def test_priority_f_over_d(self):
        # If both exist, F should be preferred based on current logic
        text = "Cohen's d = 0.5 and F(1, 10) = 5.0."
        value, metric, df = extract_effect_size(text)
        assert metric == "F"
        assert df == (1, 10)

# Task T018 specific test for regex patterns
def test_regex_patterns():
    """
    Validates that the regex patterns in parsers.py correctly identify:
    - N=\\d+
    - Cohen's d=\\d+\\.\\d+
    - F\\(\\d+,\\d+\\)=\\d+\\.\\d+
    """
    # Test N pattern
    n_text = "N=100"
    assert extract_sample_size(n_text) == 100

    # Test Cohen's d pattern
    d_text = "Cohen's d=0.5"
    val, met, _ = extract_effect_size(d_text)
    assert met == "Cohen's d"
    assert abs(val - 0.5) < 0.01

    # Test F pattern
    f_text = "F(1,20)=4.5"
    val, met, df = extract_effect_size(f_text)
    assert met == "F"
    assert df == (1, 20)
    assert abs(val - 4.5) < 0.01