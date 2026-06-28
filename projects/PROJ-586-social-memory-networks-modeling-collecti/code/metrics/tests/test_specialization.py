"""
Unit tests for specialization index computation.

These tests verify the correctness of the specialization index
implementation in code/metrics/specialization.py.
"""

import pytest
import numpy as np
from typing import List, Dict, Any

from metrics.specialization import (
    compute_specialization_index,
    compute_game_level_specialization,
    validate_specialization_index,
    SpecializationMetrics
)


class TestSpecializationIndexComputation:
    """Tests for the main specialization index computation function."""

    def test_empty_game_results(self):
        """Specialization index should be 0 for empty results."""
        index, metrics = compute_specialization_index([])
        assert index == 0.0
        assert metrics.n_agents == 0
        assert metrics.specialization_index == 0.0

    def test_single_agent(self):
        """Single agent should have specialization index of 0."""
        game_results = [
            {'agent_id': 'agent_1', 'retrieved_items': ['item1', 'item2'],
             'known_items': ['item1'], 'game_id': 1}
        ]
        index, metrics = compute_specialization_index(game_results)
        assert index == 0.0
        assert metrics.n_agents == 1
        assert metrics.max_specialization == 0.0

    def test_two_agents_no_overlap(self):
        """Two agents with completely different items should have high specialization."""
        game_results = [
            {'agent_id': 'agent_1', 'retrieved_items': ['item1', 'item2'],
             'known_items': [], 'game_id': 1},
            {'agent_id': 'agent_2', 'retrieved_items': ['item3', 'item4'],
             'known_items': [], 'game_id': 1}
        ]
        index, metrics = compute_specialization_index(game_results)
        # Maximum for 2 agents is log₂(2) = 1.0
        assert metrics.max_specialization == 1.0
        # With no overlap, specialization should be high
        assert index > 0.5

    def test_two_agents_full_overlap(self):
        """Two agents with identical items should have low specialization."""
        game_results = [
            {'agent_id': 'agent_1', 'retrieved_items': ['item1', 'item2'],
             'known_items': [], 'game_id': 1},
            {'agent_id': 'agent_2', 'retrieved_items': ['item1', 'item2'],
             'known_items': [], 'game_id': 1}
        ]
        index, metrics = compute_specialization_index(game_results)
        # Maximum for 2 agents is log₂(2) = 1.0
        assert metrics.max_specialization == 1.0
        # With full overlap, specialization should be low (near 0)
        assert index < 0.3

    def test_bounds_validity(self):
        """Specialization index must be within [0, log₂(N)]."""
        game_results = [
            {'agent_id': f'agent_{i}', 'retrieved_items': [f'item_{i}'],
             'known_items': [], 'game_id': 1}
            for i in range(4)
        ]
        index, metrics = compute_specialization_index(game_results)
        max_specialization = np.log2(4)  # Should be 2.0

        assert index >= 0.0
        assert index <= max_specialization
        assert metrics.max_specialization == max_specialization

    def test_multiple_games_aggregation(self):
        """Specialization should aggregate correctly across multiple games."""
        game_results = []
        for game_id in range(10):
            game_results.extend([
                {'agent_id': 'agent_1', 'retrieved_items': [f'game{game_id}_item1'],
                 'known_items': [], 'game_id': game_id},
                {'agent_id': 'agent_2', 'retrieved_items': [f'game{game_id}_item2'],
                 'known_items': [], 'game_id': game_id}
            ])

        index, metrics = compute_specialization_index(game_results)
        assert metrics.n_agents == 2
        assert 0.0 <= index <= 1.0

    def test_returns_specialization_metrics(self):
        """Function should return a SpecializationMetrics object."""
        game_results = [
            {'agent_id': 'agent_1', 'retrieved_items': ['item1'],
             'known_items': [], 'game_id': 1},
            {'agent_id': 'agent_2', 'retrieved_items': ['item2'],
             'known_items': [], 'game_id': 1}
        ]
        index, metrics = compute_specialization_index(game_results)

        assert isinstance(metrics, SpecializationMetrics)
        assert hasattr(metrics, 'specialization_index')
        assert hasattr(metrics, 'agent_specialization_scores')
        assert hasattr(metrics, 'overlap_matrix')
        assert hasattr(metrics, 'n_agents')
        assert hasattr(metrics, 'max_specialization')

    def test_agent_specialization_scores_length(self):
        """Agent specialization scores should match number of agents."""
        n_agents = 5
        game_results = [
            {'agent_id': f'agent_{i}', 'retrieved_items': [f'item_{i}'],
             'known_items': [], 'game_id': 1}
            for i in range(n_agents)
        ]
        index, metrics = compute_specialization_index(game_results)

        assert len(metrics.agent_specialization_scores) == n_agents
        for score in metrics.agent_specialization_scores:
            assert 0.0 <= score <= 1.0

    def test_overlap_matrix_shape(self):
        """Overlap matrix should be N×N square matrix."""
        n_agents = 3
        game_results = [
            {'agent_id': f'agent_{i}', 'retrieved_items': [f'item_{i}'],
             'known_items': [], 'game_id': 1}
            for i in range(n_agents)
        ]
        index, metrics = compute_specialization_index(game_results)

        assert metrics.overlap_matrix.shape == (n_agents, n_agents)
        # Diagonal should be 0 (no self-overlap)
        assert np.allclose(np.diag(metrics.overlap_matrix), 0.0)


class TestGameLevelSpecialization:
    """Tests for single game specialization computation."""

    def test_single_game_computation(self):
        """Should compute specialization for a single game."""
        game_result = {
            'agents': [
                {'agent_id': 'agent_1', 'retrieved_items': ['item1'],
                 'known_items': []},
                {'agent_id': 'agent_2', 'retrieved_items': ['item2'],
                 'known_items': []}
            ]
        }
        index = compute_game_level_specialization(game_result)
        assert 0.0 <= index <= 1.0

    def test_single_agent_game(self):
        """Single agent game should return 0."""
        game_result = {
            'agents': [
                {'agent_id': 'agent_1', 'retrieved_items': ['item1'],
                 'known_items': []}
            ]
        }
        index = compute_game_level_specialization(game_result)
        assert index == 0.0


class TestValidation:
    """Tests for specialization index validation."""

    def test_valid_index(self):
        """Valid index should pass validation."""
        is_valid, message = validate_specialization_index(0.5, n_agents=4)
        assert is_valid
        assert 'within valid range' in message

    def test_invalid_negative(self):
        """Negative index should fail validation."""
        is_valid, message = validate_specialization_index(-0.1, n_agents=4)
        assert not is_valid
        assert 'below minimum' in message

    def test_invalid_exceeds_max(self):
        """Index exceeding max should fail validation."""
        is_valid, message = validate_specialization_index(3.0, n_agents=2)
        # log₂(2) = 1.0, so 3.0 should exceed
        assert not is_valid
        assert 'exceeds maximum' in message

    def test_zero_agents(self):
        """Zero agents should fail validation."""
        is_valid, message = validate_specialization_index(0.0, n_agents=0)
        assert not is_valid
        assert 'positive' in message
