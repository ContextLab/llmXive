"""Tests for retrieval metric calculations."""
import pytest
from metrics.retrieval import compute_retrieval_efficiency, RetrievalMetrics

def test_efficiency_basic():
    metrics, eff = compute_retrieval_efficiency(5, 10, 5)
    assert isinstance(metrics, RetrievalMetrics)
    assert metrics.correct == 5
    assert metrics.total == 10
    # Expected rate = 0.5, baseline = 0.2 -> efficiency = 2.5
    assert pytest.approx(eff, rel=1e-6) == 2.5

def test_negative_inputs_are_clamped():
    _, eff = compute_retrieval_efficiency(-5, -10, -3)
    # After clamping: correct=0, total=0 -> rate=0, baseline=1/1
    assert eff == 0.0

def test_zero_agents_defaults_to_one():
    _, eff = compute_retrieval_efficiency(5, 10, 0)
    # baseline becomes 1/1
    assert pytest.approx(eff, rel=1e-6) == 5.0