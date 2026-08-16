"""
Unit tests for code/metrics.py.

Tests Shannon entropy calculation and diversity score computation.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Ensure code directory is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from metrics import shannon_entropy, calculate_diversity_score


def test_shannon_entropy_empty_list():
    """Test entropy of an empty list is 0."""
    result = shannon_entropy([])
    assert result == 0.0


def test_shannon_entropy_single_item():
    """Test entropy of a single item is 0."""
    result = shannon_entropy(["A"])
    assert result == 0.0


def test_shannon_entropy_uniform_distribution():
    """Test entropy of a uniform distribution (max entropy)."""
    # Two items, equal probability -> log2(2) = 1.0
    result = shannon_entropy(["A", "B"])
    assert np.isclose(result, 1.0, atol=1e-5)

    # Four items, equal probability -> log2(4) = 2.0
    result = shannon_entropy(["A", "B", "C", "D"])
    assert np.isclose(result, 2.0, atol=1e-5)


def test_shannon_entropy_skewed_distribution():
    """Test entropy of a skewed distribution."""
    # High probability on one item -> lower entropy
    # ["A", "A", "A", "B"] -> p(A)=0.75, p(B)=0.25
    # H = - (0.75*log2(0.75) + 0.25*log2(0.25))
    # H ≈ 0.811
    result = shannon_entropy(["A", "A", "A", "B"])
    expected = - (0.75 * np.log2(0.75) + 0.25 * np.log2(0.25))
    assert np.isclose(result, expected, atol=1e-5)


def test_calculate_diversity_score_basic():
    """Test diversity score calculation on a simple list."""
    categories = ["Math", "Math", "Science", "History"]
    score = calculate_diversity_score(categories)
    # p(Math)=0.5, p(Science)=0.25, p(History)=0.25
    # H = - (0.5*log2(0.5) + 0.25*log2(0.25) + 0.25*log2(0.25))
    # H = 0.5 + 0.5 + 0.5 = 1.5
    assert np.isclose(score, 1.5, atol=1e-5)


def test_calculate_diversity_score_empty():
    """Test diversity score for empty list."""
    score = calculate_diversity_score([])
    assert score == 0.0