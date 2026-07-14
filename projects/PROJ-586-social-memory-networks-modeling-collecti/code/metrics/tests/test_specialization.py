"""Tests for specialization metrics computation."""
import pytest
import math
from typing import List, Dict, Any

from metrics.specialization import (
    compute_specialization_index,
    compute_gini_coefficient,
    compute_shannon_entropy,
    validate_specialization_index,
    batch_compute_specialization,
    SpecializationMetrics
)


class TestSpecializationIndexComputation:
    """Test cases for compute_specialization_index."""

    def test_empty_input_returns_zero(self):
        """Empty input should return specialization index of 0."""
        index, metrics = compute_specialization_index([])
        assert index == 0.0
        assert metrics.specialization_index == 0.0

    def test_none_input_returns_zero(self):
        """None input should return specialization index of 0."""
        index, metrics = compute_specialization_index(None)
        assert index == 0.0

    def test_single_agent(self):
        """Single agent should have specialization index of 0."""
        agent_facts = {0: ['fact1', 'fact2', 'fact3']}
        index, metrics = compute_specialization_index(agent_facts)
        assert index == 0.0
        assert validate_specialization_index(index, 1)

    def test_perfectly_equal_distribution(self):
        """Perfectly equal distribution should have minimal specialization."""
        # 2 agents, each with 5 facts
        agent_facts = {0: ['f1', 'f2', 'f3', 'f4', 'f5'],
                      1: ['f6', 'f7', 'f8', 'f9', 'f10']}
        index, metrics = compute_specialization_index(agent_facts)
        # Should be 0 or very close to 0 (perfect equality)
        assert index <= 0.001
        assert validate_specialization_index(index, 2)

    def test_perfectly_unequal_distribution(self):
        """Perfectly unequal distribution should have high specialization."""
        # 2 agents, one has all facts, other has none
        agent_facts = {0: ['f1', 'f2', 'f3', 'f4', 'f5'],
                      1: []}
        index, metrics = compute_specialization_index(agent_facts)
        # Should be close to log2(2) = 1.0
        expected_max = math.log2(2)
        assert index <= expected_max + 0.001
        assert validate_specialization_index(index, 2)

    def test_bounded_by_log2_n_agents(self):
        """Specialization index must be bounded by log2(N_agents)."""
        for n_agents in [2, 3, 4, 5, 10]:
            # Create a highly unequal distribution
            agent_facts = {i: [f'fact_{i}_{j}' for j in range(100)] if i == 0 else []
                           for i in range(n_agents)}
            index, metrics = compute_specialization_index(agent_facts)
            max_possible = math.log2(n_agents)
            assert index <= max_possible + 1e-9, f"Index {index} exceeds max {max_possible} for {n_agents} agents"
            assert index >= 0.0

    def test_dict_input_format(self):
        """Test with dict mapping agent_id to facts list."""
        agent_facts = {0: ['a', 'b'], 1: ['c'], 2: ['d', 'e', 'f']}
        index, metrics = compute_specialization_index(agent_facts)
        assert isinstance(index, float)
        assert isinstance(metrics, SpecializationMetrics)
        assert 0.0 <= index <= math.log2(3)

    def test_list_of_lists_format(self):
        """Test with list of lists (each inner list is facts for one agent)."""
        agent_facts = [['a', 'b'], ['c'], ['d', 'e', 'f']]
        index, metrics = compute_specialization_index(agent_facts)
        assert isinstance(index, float)
        assert metrics.per_agent_contributions == {0: 2, 1: 1, 2: 3}

    def test_num_agents_override(self):
        """Test that num_agents parameter overrides inferred count."""
        agent_facts = {0: ['a'], 1: ['b']}
        index, metrics = compute_specialization_index(agent_facts, num_agents=5)
        # With 5 agents but only 2 having facts, should be higher specialization
        assert index >= 0.0
        assert index <= math.log2(5)

    def test_per_agent_contributions_populated(self):
        """Test that per_agent_contributions is populated correctly."""
        agent_facts = {0: ['a', 'b', 'c'], 1: ['d'], 2: ['e', 'f']}
        index, metrics = compute_specialization_index(agent_facts)
        assert metrics.per_agent_contributions == {0: 3, 1: 1, 2: 2}


class TestGiniCoefficient:
    """Test cases for Gini coefficient computation."""

    def test_perfect_equality(self):
        """Perfect equality should yield Gini of 0."""
        values = [10, 10, 10, 10]
        gini = compute_gini_coefficient(values)
        assert abs(gini) < 0.001

    def test_perfect_inequality(self):
        """Perfect inequality should yield Gini close to 1."""
        values = [0, 0, 0, 100]
        gini = compute_gini_coefficient(values)
        assert 0.7 < gini <= 1.0  # Gini for this distribution is 0.75

    def test_empty_list(self):
        """Empty list should return 0."""
        gini = compute_gini_coefficient([])
        assert gini == 0.0

    def test_all_zeros(self):
        """All zeros should return 0."""
        gini = compute_gini_coefficient([0, 0, 0])
        assert gini == 0.0


class TestShannonEntropy:
    """Test cases for Shannon entropy computation."""

    def test_perfect_equality(self):
        """Perfect equality should yield max entropy."""
        values = [10, 10, 10, 10]
        entropy, max_entropy = compute_shannon_entropy(values)
        assert abs(entropy - max_entropy) < 0.001
        assert abs(max_entropy - math.log2(4)) < 0.001

    def test_perfect_inequality(self):
        """Perfect inequality should yield 0 entropy."""
        values = [0, 0, 0, 100]
        entropy, max_entropy = compute_shannon_entropy(values)
        assert entropy == 0.0

    def test_empty_list(self):
        """Empty list should return 0."""
        entropy, max_entropy = compute_shannon_entropy([])
        assert entropy == 0.0
        assert max_entropy == 0.0


class TestValidation:
    """Test cases for validation functions."""

    def test_valid_index(self):
        """Valid index should pass validation."""
        assert validate_specialization_index(0.5, 4)
        assert validate_specialization_index(0.0, 4)
        assert validate_specialization_index(math.log2(4), 4)

    def test_invalid_negative_index(self):
        """Negative index should fail validation."""
        assert not validate_specialization_index(-0.1, 4)

    def test_invalid_too_high_index(self):
        """Index exceeding log2(N) should fail validation."""
        assert not validate_specialization_index(math.log2(4) + 0.1, 4)

    def test_single_agent(self):
        """Single agent should only accept 0 index."""
        assert validate_specialization_index(0.0, 1)
        assert not validate_specialization_index(0.1, 1)


class TestBatchCompute:
    """Test cases for batch computation."""

    def test_batch_processing(self):
        """Test batch processing of multiple game results."""
        class FakeResult:
            def __init__(self, facts_per_agent):
                self.facts_per_agent = facts_per_agent

        results = [
            FakeResult({0: ['a', 'b'], 1: ['c', 'd']}),
            FakeResult({0: ['a', 'b', 'c'], 1: ['d']}),
            FakeResult({0: ['a'], 1: ['b'], 2: ['c']})
        ]

        indices, metrics_list = batch_compute_specialization(results)

        assert len(indices) == 3
        assert len(metrics_list) == 3
        for idx in indices:
            assert isinstance(idx, float)
            assert 0.0 <= idx

    def test_empty_batch(self):
        """Empty batch should return empty lists."""
        indices, metrics_list = batch_compute_specialization([])
        assert indices == []
        assert metrics_list == []
