"""Tests for specialization metric calculations."""
import pytest
from metrics.specialization import compute_specialization_index

def test_specialization_basic():
    # With 4 agents, max log2(N) = 2
    idx = compute_specialization_index(num_specialized=2, n_agents=4)
    assert pytest.approx(idx, rel=1e-6) == 1.0

def test_zero_agents_returns_zero():
    idx = compute_specialization_index(num_specialized=0, n_agents=0)
    assert idx == 0.0