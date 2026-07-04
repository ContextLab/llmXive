"""Unit tests for specialization metrics."""
import pytest
from metrics.specialization import (
    compute_specialization_index,
    SpecializationMetrics,
    validate_specialization_index,
    validate_specialization_metrics,
    compute_game_level_specialization
)


class TestSpecializationIndexComputation:
    """Tests for compute_specialization_index."""

    def test_uniform_distribution(self):
        """Perfectly uniform distribution should have low specialization."""
        # Each agent has one unique skill -> uniform distribution
        # HHI = sum((1/3)^2) = 3 * 1/9 = 0.333
        agent_skills = [['skill_A'], ['skill_B'], ['skill_C']]
        idx, metrics = compute_specialization_index(agent_skills)
        assert 0.30 <= idx <= 0.36  # Allow small float variance
        assert validate_specialization_index(idx)

    def test_high_specialization(self):
        """One agent holding all skills should have high specialization."""
        # One agent has all skills -> HHI = 1.0
        agent_skills = [['skill_A', 'skill_B', 'skill_C'], [], []]
        idx, metrics = compute_specialization_index(agent_skills)
        assert idx == 1.0
        assert validate_specialization_index(idx)

    def test_empty_list(self):
        """Empty list should return 0.0."""
        idx, metrics = compute_specialization_index([])
        assert idx == 0.0
        assert isinstance(metrics, SpecializationMetrics)

    def test_single_agent(self):
        """Single agent should have HHI = 1.0."""
        agent_skills = [['skill_A', 'skill_B']]
        idx, metrics = compute_specialization_index(agent_skills)
        assert idx == 1.0

    def test_keyword_args(self):
        """Test keyword argument calling convention."""
        agent_skills = [['skill_A'], ['skill_B']]
        idx, metrics = compute_specialization_index(agents=agent_skills, num_agents=2)
        assert idx == 0.5  # 2 skills, 1 each -> (0.5)^2 + (0.5)^2 = 0.5

    def test_legacy_int_call(self):
        """Test legacy integer calling convention."""
        # Legacy call with int should not crash, returns 0.0 if no list
        idx, metrics = compute_specialization_index(5, 10)
        assert idx == 0.0

    def test_distribution_sum(self):
        """Skill distribution should sum to 1.0."""
        agent_skills = [['A', 'B'], ['B', 'C'], ['C']]
        idx, metrics = compute_specialization_index(agent_skills)
        if metrics.skill_distribution:
            assert abs(sum(metrics.skill_distribution) - 1.0) < 1e-6


class TestGameLevelSpecialization:
    """Tests for compute_game_level_specialization."""

    def test_basic_calculation(self):
        """Basic HHI calculation."""
        agent_skills = [['A', 'A'], ['B'], ['C']]
        # Total 4 skills: 2 A, 1 B, 1 C
        # HHI = (2/4)^2 + (1/4)^2 + (1/4)^2 = 0.25 + 0.0625 + 0.0625 = 0.375
        hhi = compute_game_level_specialization(agent_skills)
        assert abs(hhi - 0.375) < 1e-6

    def test_empty_input(self):
        """Empty input returns 0.0."""
        assert compute_game_level_specialization([]) == 0.0
        assert compute_game_level_specialization([[], []]) == 0.0


class TestValidation:
    """Tests for validation functions."""

    def test_valid_index(self):
        assert validate_specialization_index(0.5) is True
        assert validate_specialization_index(0.0) is True
        assert validate_specialization_index(1.0) is True

    def test_invalid_index(self):
        assert validate_specialization_index(-0.1) is False
        assert validate_specialization_index(1.1) is False

    def test_valid_metrics(self):
        metrics = SpecializationMetrics(
            specialization_index=0.5,
            skill_distribution=[0.5, 0.5],
            herfindahl_index=0.5
        )
        assert validate_specialization_metrics(metrics) is True

    def test_invalid_metrics_range(self):
        metrics = SpecializationMetrics(
            specialization_index=1.5,
            skill_distribution=[],
            herfindahl_index=1.5
        )
        assert validate_specialization_metrics(metrics) is False
