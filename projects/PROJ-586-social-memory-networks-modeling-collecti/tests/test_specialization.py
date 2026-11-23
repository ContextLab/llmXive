"""Tests for specialization index computation."""
import pytest
import math
from typing import List, Dict, Any

from metrics.specialization import (
    SpecializationMetrics,
    compute_gini_coefficient,
    compute_shannon_entropy,
    compute_specialization_index,
    validate_specialization_index,
    batch_compute_specialization,
    compute_specialization_index_v1
)


class TestSpecializationIndexComputation:
    """Tests for the main specialization index computation."""

    def test_perfect_equality(self):
        """All agents contribute equally -> specialization = 0."""
        agent_facts = [
            {'agent_id': 0, 'facts': ['a', 'b', 'c']},
            {'agent_id': 1, 'facts': ['d', 'e', 'f']},
            {'agent_id': 2, 'facts': ['g', 'h', 'i']}
        ]
        index, metrics = compute_specialization_index(agent_facts)
        assert 0.0 <= index <= 0.1, f"Expected near-zero specialization, got {index}"
        assert metrics.is_valid

    def test_perfect_specialization(self):
        """One agent contributes everything -> high specialization."""
        agent_facts = [
            {'agent_id': 0, 'facts': ['a', 'b', 'c', 'd', 'e']},
            {'agent_id': 1, 'facts': []},
            {'agent_id': 2, 'facts': []}
        ]
        index, metrics = compute_specialization_index(agent_facts)
        assert index > 0.5, f"Expected high specialization, got {index}"
        assert metrics.is_valid

    def test_empty_list(self):
        """Empty agent list returns 0 specialization."""
        index, metrics = compute_specialization_index([])
        assert index == 0.0
        assert metrics.is_valid

    def test_none_input(self):
        """None input returns 0 specialization."""
        index, metrics = compute_specialization_index(None)
        assert index == 0.0
        assert metrics.is_valid

    def test_dict_input(self):
        """Dict mapping agent_id to facts works correctly."""
        agent_facts = {
            0: ['a', 'b'],
            1: ['c'],
            2: ['d', 'e', 'f']
        }
        index, metrics = compute_specialization_index(agent_facts)
        assert 0.0 <= index <= 1.0
        assert metrics.is_valid

    def test_list_of_lists(self):
        """List of lists (facts per agent) works correctly."""
        agent_facts = [
            ['a', 'b', 'c'],
            ['d', 'e'],
            ['f']
        ]
        index, metrics = compute_specialization_index(agent_facts)
        assert 0.0 <= index <= 1.0
        assert metrics.is_valid

    def test_with_explicit_num_agents(self):
        """Explicit num_agents parameter works."""
        agent_facts = [
            {'agent_id': 0, 'facts': ['a', 'b']}
        ]
        index, metrics = compute_specialization_index(agent_facts, num_agents=3)
        assert 0.0 <= index <= 1.0
        assert metrics.is_valid

    def test_bounds_validation(self):
        """Result is always bounded in [0, 1]."""
        # Test with extreme values
        agent_facts = [
            {'agent_id': 0, 'facts': list(range(1000))},
            {'agent_id': 1, 'facts': []},
            {'agent_id': 2, 'facts': []}
        ]
        index, metrics = compute_specialization_index(agent_facts)
        assert 0.0 <= index <= 1.0, f"Index {index} out of bounds"
        assert metrics.is_valid


class TestGiniCoefficient:
    """Tests for Gini coefficient computation."""

    def test_perfect_equality(self):
        """All equal values -> Gini = 0."""
        values = [5, 5, 5, 5]
        gini = compute_gini_coefficient(values)
        assert abs(gini) < 0.01, f"Expected near-zero Gini, got {gini}"

    def test_perfect_inequality(self):
        """One value has everything -> Gini near 1."""
        values = [10, 0, 0, 0]
        gini = compute_gini_coefficient(values)
        assert gini > 0.7, f"Expected high Gini, got {gini}"

    def test_empty_list(self):
        """Empty list returns 0."""
        gini = compute_gini_coefficient([])
        assert gini == 0.0

    def test_all_zeros(self):
        """All zeros returns 0."""
        gini = compute_gini_coefficient([0, 0, 0])
        assert gini == 0.0


class TestShannonEntropy:
    """Tests for Shannon entropy computation."""

    def test_perfect_equality(self):
        """All equal values -> max normalized entropy."""
        values = [1, 1, 1, 1]
        entropy = compute_shannon_entropy(values)
        assert abs(entropy - 1.0) < 0.01, f"Expected near-1 entropy, got {entropy}"

    def test_perfect_inequality(self):
        """One value has everything -> entropy near 0."""
        values = [10, 0, 0, 0]
        entropy = compute_shannon_entropy(values)
        assert entropy < 0.1, f"Expected near-zero entropy, got {entropy}"

    def test_empty_list(self):
        """Empty list returns 0."""
        entropy = compute_shannon_entropy([])
        assert entropy == 0.0


class TestValidation:
    """Tests for validation logic."""

    def test_valid_range(self):
        """Valid range returns True."""
        is_valid, msg = validate_specialization_index(0.5)
        assert is_valid
        assert "valid range" in msg

    def test_negative_value(self):
        """Negative value returns False."""
        is_valid, msg = validate_specialization_index(-0.1)
        assert not is_valid
        assert "negative" in msg

    def test_value_above_one(self):
        """Value > 1 returns False."""
        is_valid, msg = validate_specialization_index(1.1)
        assert not is_valid
        assert "exceeds maximum" in msg


class TestBatchCompute:
    """Tests for batch computation."""

    def test_multiple_games(self):
        """Batch computation over multiple games."""
        game_results = [
            {'agent_facts': [{'agent_id': 0, 'facts': ['a']}, {'agent_id': 1, 'facts': ['b']}], 'num_agents': 2},
            {'agent_facts': [{'agent_id': 0, 'facts': ['a', 'b']}, {'agent_id': 1, 'facts': []}], 'num_agents': 2},
            {'agent_facts': [{'agent_id': 0, 'facts': ['a']}, {'agent_id': 1, 'facts': ['b']}], 'num_agents': 2}
        ]
        stats = batch_compute_specialization(game_results)
        assert stats['count'] == 3
        assert 0.0 <= stats['mean'] <= 1.0
        assert stats['valid_count'] <= stats['count']

    def test_empty_list(self):
        """Empty game list returns zeros."""
        stats = batch_compute_specialization([])
        assert stats['count'] == 0
        assert stats['mean'] == 0.0


class TestLegacyAlias:
    """Tests for legacy function alias."""

    def test_v1_alias_works(self):
        """compute_specialization_index_v1 works as expected."""
        agent_skills = [
            {'agent_id': 0, 'facts': ['a', 'b']},
            {'agent_id': 1, 'facts': ['c']}
        ]
        index, metrics = compute_specialization_index_v1(agent_skills, num_agents=2)
        assert 0.0 <= index <= 1.0
        assert metrics.is_valid