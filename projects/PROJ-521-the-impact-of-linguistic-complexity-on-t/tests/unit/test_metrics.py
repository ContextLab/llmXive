"""
Unit tests for linguistic complexity metrics in code/utils.py.
"""
import pytest
import sys
import os

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils import (
    pin_random_seed,
    calculate_mtld,
    calculate_flesch_kincaid,
    calculate_average_sentence_length,
    get_all_metrics
)
import random
import numpy as np


def test_pin_random_seed():
    """Test that pin_random_seed sets the seeds correctly."""
    pin_random_seed(123)
    assert random.randint(0, 100) == random.randint(0, 100)  # Should be same if seed is pinned
    # Reset and test again
    pin_random_seed(123)
    val1 = random.randint(0, 100)
    pin_random_seed(123)
    val2 = random.randint(0, 100)
    assert val1 == val2


def test_mtld_short_text():
    """Test MTLD calculation on very short text."""
    short_text = "Hello world."
    mtld_score = calculate_mtld(short_text)
    assert mtld_score == 0.0  # Defined behavior for short text


def test_mtld_reproducibility():
    """Test that MTLD is deterministic."""
    text = "This is a test. This is only a test. A real test."
    pin_random_seed(42)
    score1 = calculate_mtld(text)
    pin_random_seed(42)
    score2 = calculate_mtld(text)
    assert score1 == score2


def test_mtld_forward_vs_bidirectional():
    """Test that forward and bidirectional MTLD can differ."""
    text = "The cat sat on the mat. The dog ran on the grass."
    fwd = calculate_mtld(text, measure='fwd')
    bi = calculate_mtld(text, measure='bi')
    # They don't have to be different, but the function should run without error
    assert isinstance(fwd, float)
    assert isinstance(bi, float)


def test_flesch_kincaid_basic():
    """Test Flesch-Kincaid calculation."""
    text = "This is a simple sentence. It is easy to read."
    fk = calculate_flesch_kincaid(text)
    assert isinstance(fk, float)
    # FK should be a reasonable number (not negative, not infinite)
    assert not np.isnan(fk)
    assert not np.isinf(fk)


def test_flesch_kincaid_empty():
    """Test Flesch-Kincaid on empty string."""
    fk = calculate_flesch_kincaid("")
    # textstat might return 0 or raise an error, we just check it runs
    assert isinstance(fk, float)


def test_avg_sentence_length_basic():
    """Test average sentence length calculation."""
    text = "Short. Medium sentence here. A longer sentence with more words in it."
    avg_len = calculate_average_sentence_length(text)
    # 1 + 3 + 8 = 12 words, 3 sentences -> 4.0
    assert abs(avg_len - 4.0) < 0.01


def test_avg_sentence_length_single():
    """Test average sentence length with one sentence."""
    text = "This is a single sentence."
    avg_len = calculate_average_sentence_length(text)
    assert avg_len == 5.0  # 5 words


def test_get_all_metrics():
    """Test the combined metrics function."""
    text = "The quick brown fox jumps over the lazy dog. It was a sunny day."
    metrics = get_all_metrics(text)
    assert 'mtld' in metrics
    assert 'flesch_kincaid' in metrics
    assert 'avg_sentence_length' in metrics
    assert isinstance(metrics['mtld'], float)
    assert isinstance(metrics['flesch_kincaid'], float)
    assert isinstance(metrics['avg_sentence_length'], float)


def test_metrics_consistency():
    """Test that individual metric functions match get_all_metrics."""
    text = "Sample text for testing purposes. More words here."
    metrics = get_all_metrics(text)
    assert metrics['mtld'] == calculate_mtld(text)
    assert metrics['flesch_kincaid'] == calculate_flesch_kincaid(text)
    assert metrics['avg_sentence_length'] == calculate_average_sentence_length(text)


def test_mtld_invalid_measure():
    """Test that invalid measure type raises ValueError."""
    with pytest.raises(ValueError):
        calculate_mtld("Test text", measure='invalid')