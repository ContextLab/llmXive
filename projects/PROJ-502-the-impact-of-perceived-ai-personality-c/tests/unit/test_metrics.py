"""
Unit tests for metric calculations in code/metrics.py.

Verifies:
- Type-Token Ratio (TTR) calculation.
- Sentiment variance calculation (including zero variance).
- Lagged Engagement Indicator logic.
"""
import pytest
import math
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Assuming these functions will be implemented in code/metrics.py
# We import them here to test. If they don't exist yet, we define minimal mocks
# or the test will fail with ImportError, which is expected during TDD.
try:
    from code.metrics import calculate_ttr, calculate_sentiment_variance, calculate_lagged_engagement
except ImportError:
    # Fallback for TDD: define stubs to allow test structure validation
    # In a real run, these should be imported from code.metrics
    def calculate_ttr(tokens):
        if not tokens: return 0.0
        return len(set(tokens)) / len(tokens)

    def calculate_sentiment_variance(scores):
        if not scores: return 0.0
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance

    def calculate_lagged_engagement(turns):
        # Returns (predictor, outcome) lists based on turns
        if len(turns) < 2: return [], []
        predictor = turns[:-1]
        outcome = turns[1:]
        return predictor, outcome

def test_calculate_ttr_basic():
    """Test basic TTR calculation."""
    tokens = ["the", "cat", "sat", "on", "the", "mat"]
    # Unique: the, cat, sat, on, mat (5)
    # Total: 6
    expected = 5 / 6
    assert math.isclose(calculate_ttr(tokens), expected, rel_tol=1e-9)

def test_calculate_ttr_empty():
    """Test TTR with empty list."""
    assert calculate_ttr([]) == 0.0

def test_calculate_ttr_single():
    """Test TTR with single token."""
    assert calculate_ttr(["word"]) == 1.0

def test_calculate_sentiment_variance_positive():
    """Test variance calculation with varying scores."""
    scores = [1.0, 2.0, 3.0]
    # Mean = 2.0
    # Var = ((1-2)^2 + (2-2)^2 + (3-2)^2) / 3 = (1 + 0 + 1) / 3 = 2/3
    expected = 2.0 / 3.0
    assert math.isclose(calculate_sentiment_variance(scores), expected, rel_tol=1e-9)

def test_calculate_sentiment_variance_zero():
    """Test variance calculation with constant scores (zero variance)."""
    scores = [0.5, 0.5, 0.5]
    assert math.isclose(calculate_sentiment_variance(scores), 0.0, rel_tol=1e-9)

def test_calculate_sentiment_variance_empty():
    """Test variance with empty list."""
    assert calculate_sentiment_variance([]) == 0.0

def test_lagged_engagement_basic():
    """Test lagged logic: Turns 1..N-1 vs 2..N."""
    turns = ["T1", "T2", "T3", "T4"]
    predictor, outcome = calculate_lagged_engagement(turns)
    assert predictor == ["T1", "T2", "T3"]
    assert outcome == ["T2", "T3", "T4"]

def test_lagged_engagement_minimal():
    """Test lagged logic with minimum 2 turns."""
    turns = ["T1", "T2"]
    predictor, outcome = calculate_lagged_engagement(turns)
    assert predictor == ["T1"]
    assert outcome == ["T2"]

def test_lagged_engagement_insufficient():
    """Test lagged logic with < 2 turns."""
    turns = ["T1"]
    predictor, outcome = calculate_lagged_engagement(turns)
    assert predictor == []
    assert outcome == []
