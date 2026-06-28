"""Tests for cue-retrieval efficiency metric.

These tests verify the correctness of the retrieval efficiency computation
as specified in FR-005.
"""

import pytest
import numpy as np
from typing import List, Dict, Any
from metrics.retrieval import (
    RetrievalMetrics,
    compute_retrieval_rate,
    compute_retrieval_efficiency,
    validate_retrieval_efficiency,
    compute_game_level_retrieval
)


class TestRetrievalRateComputation:
    """Tests for compute_retrieval_rate function."""

    def test_perfect_retrieval(self):
        """All cues retrieved should give rate of 1.0."""
        rate = compute_retrieval_rate(10, 10, 3)
        assert rate == 1.0

    def test_zero_retrieval(self):
        """No cues retrieved should give rate of 0.0."""
        rate = compute_retrieval_rate(0, 10, 3)
        assert rate == 0.0

    def test_partial_retrieval(self):
        """Partial retrieval should give proportional rate."""
        rate = compute_retrieval_rate(5, 10, 3)
        assert rate == 0.5

    def test_no_agents(self):
        """Zero agents should give rate of 0.0."""
        rate = compute_retrieval_rate(5, 10, 0)
        assert rate == 0.0

    def test_no_cues(self):
        """Zero cues should give rate of 0.0."""
        rate = compute_retrieval_rate(0, 0, 3)
        assert rate == 0.0


class TestRetrievalEfficiencyComputation:
    """Tests for compute_retrieval_efficiency function."""

    def test_perfect_retrieval_efficiency(self):
        """Perfect retrieval should give efficiency of N_agents."""
        metrics, efficiency = compute_retrieval_efficiency(10, 10, 3)
        assert efficiency == 3.0
        assert metrics.efficiency == 3.0

    def test_random_baseline_efficiency(self):
        """Retrieval at baseline should give efficiency of 1.0."""
        # With 3 agents, baseline = 1/3
        # To get efficiency of 1.0, we need retrieval_rate = 1/3
        # With 3 cues, 1 retrieved gives rate = 1/3
        metrics, efficiency = compute_retrieval_efficiency(1, 3, 3)
        assert np.isclose(efficiency, 1.0, atol=1e-6)

    def test_zero_efficiency(self):
        """Zero retrieval should give efficiency of 0.0."""
        metrics, efficiency = compute_retrieval_efficiency(0, 10, 3)
        assert efficiency == 0.0

    def test_high_efficiency(self):
        """High retrieval rate should give high efficiency."""
        # 9/10 retrieval with 3 agents
        # rate = 0.9, baseline = 1/3
        # efficiency = 0.9 / (1/3) = 2.7
        metrics, efficiency = compute_retrieval_efficiency(9, 10, 3)
        assert np.isclose(efficiency, 2.7, atol=1e-6)

    def test_baseline_rate_computation(self):
        """Baseline rate should be 1/N_agents."""
        metrics, _ = compute_retrieval_efficiency(5, 10, 5)
        assert metrics.baseline_rate == 0.2  # 1/5

    def test_metrics_contains_all_fields(self):
        """Metrics object should contain all expected fields."""
        metrics, _ = compute_retrieval_efficiency(5, 10, 3)
        assert hasattr(metrics, 'retrieval_rate')
        assert hasattr(metrics, 'baseline_rate')
        assert hasattr(metrics, 'efficiency')
        assert hasattr(metrics, 'n_agents')
        assert hasattr(metrics, 'n_cues_total')
        assert hasattr(metrics, 'n_cues_retrieved')

    def test_to_dict(self):
        """Metrics should convert to dict correctly."""
        metrics, _ = compute_retrieval_efficiency(5, 10, 3)
        d = metrics.to_dict()
        assert d['retrieval_rate'] == 0.5
        assert d['baseline_rate'] == 1/3
        assert d['efficiency'] == 1.5
        assert d['n_agents'] == 3

    def test_invalid_negative_agents(self):
        """Negative agent count should raise ValueError."""
        with pytest.raises(ValueError):
            compute_retrieval_efficiency(5, 10, -1)

    def test_invalid_negative_cues_total(self):
        """Negative total cues should raise ValueError."""
        with pytest.raises(ValueError):
            compute_retrieval_efficiency(5, -1, 3)

    def test_invalid_negative_cues_retrieved(self):
        """Negative retrieved cues should raise ValueError."""
        with pytest.raises(ValueError):
            compute_retrieval_efficiency(-1, 10, 3)

    def test_invalid_retrieved_exceeds_total(self):
        """Retrieved exceeding total should raise ValueError."""
        with pytest.raises(ValueError):
            compute_retrieval_efficiency(15, 10, 3)


class TestValidation:
    """Tests for validate_retrieval_efficiency function."""

    def test_valid_metrics(self):
        """Valid metrics should pass validation."""
        metrics = RetrievalMetrics(
            retrieval_rate=0.5,
            baseline_rate=1/3,
            efficiency=1.5,
            n_agents=3,
            n_cues_total=10,
            n_cues_retrieved=5
        )
        is_valid, error = validate_retrieval_efficiency(metrics)
        assert is_valid
        assert error is None

    def test_invalid_retrieval_rate_negative(self):
        """Negative retrieval rate should fail validation."""
        metrics = RetrievalMetrics(
            retrieval_rate=-0.1,
            baseline_rate=1/3,
            efficiency=-0.3,
            n_agents=3,
            n_cues_total=10,
            n_cues_retrieved=0
        )
        is_valid, error = validate_retrieval_efficiency(metrics)
        assert not is_valid
        assert "retrieval_rate" in error

    def test_invalid_retrieval_rate_exceeds_one(self):
        """Retrieval rate > 1 should fail validation."""
        metrics = RetrievalMetrics(
            retrieval_rate=1.5,
            baseline_rate=1/3,
            efficiency=4.5,
            n_agents=3,
            n_cues_total=10,
            n_cues_retrieved=15
        )
        is_valid, error = validate_retrieval_efficiency(metrics)
        assert not is_valid
        assert "retrieval_rate" in error

    def test_invalid_retrieved_exceeds_total(self):
        """Retrieved > total should fail validation."""
        metrics = RetrievalMetrics(
            retrieval_rate=1.0,
            baseline_rate=1/3,
            efficiency=3.0,
            n_agents=3,
            n_cues_total=10,
            n_cues_retrieved=15
        )
        is_valid, error = validate_retrieval_efficiency(metrics)
        assert not is_valid


class TestGameLevelRetrieval:
    """Tests for compute_game_level_retrieval function."""

    def test_basic_game_result(self):
        """Should compute metrics from valid game result."""
        game_result = {
            'n_cues_total': 10,
            'n_cues_retrieved': 5,
            'agent_count': 3
        }
        metrics, efficiency = compute_game_level_retrieval(game_result)
        assert metrics.retrieval_rate == 0.5
        assert metrics.n_agents == 3

    def test_missing_keys_defaults_to_zero(self):
        """Missing keys should default to 0."""
        game_result = {}
        metrics, efficiency = compute_game_level_retrieval(game_result)
        assert metrics.retrieval_rate == 0.0
        assert metrics.n_agents == 0

    def test_partial_game_result(self):
        """Should handle partial game result with defaults."""
        game_result = {
            'n_cues_total': 10,
            'n_cues_retrieved': 8
        }
        metrics, efficiency = compute_game_level_retrieval(game_result)
        assert metrics.retrieval_rate == 0.0  # n_agents defaults to 0
        assert metrics.n_agents == 0

    def test_efficiency_with_multiple_agents(self):
        """Should compute correct efficiency for different agent counts."""
        game_result = {
            'n_cues_total': 10,
            'n_cues_retrieved': 8,
            'agent_count': 4
        }
        metrics, efficiency = compute_game_level_retrieval(game_result)
        # rate = 0.8, baseline = 1/4 = 0.25, efficiency = 0.8/0.25 = 3.2
        assert np.isclose(efficiency, 3.2, atol=1e-6)