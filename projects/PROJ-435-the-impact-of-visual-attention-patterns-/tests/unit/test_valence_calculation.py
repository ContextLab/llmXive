import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Import from the project's utility module
from code.utils.valence_calculation import tokenize, calculate_nrc_coverage, get_nrc_valence, get_vader_valence

@pytest.fixture
def sample_text():
    return "This is a happy and positive headline about success."

@pytest.fixture
def sample_nrc_lexicon():
    # Simplified NRC lexicon for testing
    return {
        "happy": {"joy": 1, "positive": 1},
        "positive": {"positive": 1},
        "success": {"joy": 1, "positive": 1},
        "sad": {"sadness": 1, "negative": 1},
        "failure": {"anger": 1, "negative": 1}
    }

def test_tokenize_simple():
    text = "This is a test."
    tokens = tokenize(text)
    assert tokens == ["this", "is", "a", "test"]

def test_tokenize_with_punctuation():
    text = "Hello, world! How are you?"
    tokens = tokenize(text)
    assert tokens == ["hello", "world", "how", "are", "you"]

def test_calculate_nrc_coverage_high(sample_text, sample_nrc_lexicon):
    tokens = tokenize(sample_text)
    coverage = calculate_nrc_coverage(tokens, sample_nrc_lexicon)
    # "happy", "positive", "success" are in lexicon
    # Total tokens: 8 ("this", "is", "a", "happy", "and", "positive", "about", "success")
    # Covered: 3
    expected_coverage = 3 / 8
    assert abs(coverage - expected_coverage) < 0.01

def test_calculate_nrc_coverage_low():
    text = "xyz abc qwerty"
    tokens = tokenize(text)
    sample_lexicon = {"happy": {"joy": 1}}
    coverage = calculate_nrc_coverage(tokens, sample_lexicon)
    assert coverage == 0.0

def test_get_nrc_valence_positive(sample_nrc_lexicon):
    text = "happy success positive"
    valence = get_nrc_valence(text, sample_nrc_lexicon)
    # Should be positive
    assert valence > 0

def test_get_nrc_valence_negative(sample_nrc_lexicon):
    text = "sad failure"
    valence = get_nrc_valence(text, sample_nrc_lexicon)
    # Should be negative
    assert valence < 0

def test_get_vader_valence_positive():
    text = "This is absolutely wonderful and amazing!"
    valence = get_vader_valence(text)
    assert valence > 0

def test_get_vader_valence_negative():
    text = "This is terrible and awful."
    valence = get_vader_valence(text)
    assert valence < 0

def test_get_vader_valence_neutral():
    text = "The sky is blue."
    valence = get_vader_valence(text)
    # Should be close to 0
    assert abs(valence) < 0.1
