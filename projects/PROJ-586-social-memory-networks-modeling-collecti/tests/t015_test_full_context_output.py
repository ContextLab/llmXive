"""
Tests for T015: Full context output generation.

These tests verify that the full context experiment produces
the expected CSV output with correct schema and real measurements.
"""
import csv
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from t015_generate_full_results import (
    GameResult,
    compute_specialization_index,
    compute_retrieval_efficiency,
    simulate_one_game,
    run_simulation,
    write_results_csv,
)


class TestGameResultSchema:
    """Test GameResult dataclass schema."""

    def test_game_result_creation(self):
        """Test creating a GameResult."""
        result = GameResult(
            game_id=1,
            agent_count=5,
            context_condition="full",
            specialization_index=0.85,
            retrieval_efficiency=0.92,
        )
        assert result.game_id == 1
        assert result.agent_count == 5
        assert result.context_condition == "full"
        assert result.specialization_index == 0.85
        assert result.retrieval_efficiency == 0.92

    def test_game_result_defaults(self):
        """Test GameResult default values."""
        result = GameResult(
            game_id=1,
            agent_count=3,
            context_condition="full",
            specialization_index=0.5,
            retrieval_efficiency=0.5,
        )
        assert result.agent_assignments == []
        assert result.retrieval_events == []


class TestSpecializationIndexComputation:
    """Test specialization index computation."""

    def test_compute_with_list(self):
        """Test compute_specialization_index with list input."""
        agents = [0, 1, 2, 0, 1, 2]
        index, metrics = compute_specialization_index(agents, num_agents=3)
        assert isinstance(index, float)
        assert 0.0 <= index <= 1.0
        assert metrics is not None

    def test_compute_with_empty_list(self):
        """Test with empty agent list."""
        index, metrics = compute_specialization_index([], num_agents=0)
        assert index == 0.0

    def test_compute_with_single_agent(self):
        """Test with single agent."""
        index, metrics = compute_specialization_index([0, 0, 0], num_agents=1)
        assert index == 0.0  # No specialization with one agent

    def test_flexible_signature(self):
        """Test flexible call signatures."""
        # List input
        index1, _ = compute_specialization_index([0, 1, 2])
        assert isinstance(index1, float)

        # Keyword input
        index2, _ = compute_specialization_index(agents=[0, 1, 2], num_agents=3)
        assert isinstance(index2, float)


class TestRetrievalEfficiencyComputation:
    """Test retrieval efficiency computation."""

    def test_compute_basic(self):
        """Test basic retrieval efficiency computation."""
        metrics, efficiency = compute_retrieval_efficiency(
            retrieved=90, total=100, agents=5
        )
        assert efficiency == 0.9
        assert metrics["retrieved"] == 90
        assert metrics["total"] == 100

    def test_compute_edge_cases(self):
        """Test edge cases."""
        # Zero retrieval
        _, eff = compute_retrieval_efficiency(0, 10, 3)
        assert eff == 0.0

        # Full retrieval
        _, eff = compute_retrieval_efficiency(10, 10, 3)
        assert eff == 1.0

        # More retrieved than total (should clamp)
        _, eff = compute_retrieval_efficiency(15, 10, 3)
        assert eff == 1.0

    def test_flexible_signature(self):
        """Test flexible call signatures."""
        # Positional
        _, eff1 = compute_retrieval_efficiency(90, 100, 5)
        assert eff1 == 0.9

        # Keyword
        _, eff2 = compute_retrieval_efficiency(
            retrieved=90, total=100, agents=5
        )
        assert eff2 == 0.9


class TestSimulation:
    """Test game simulation."""

    def test_simulate_one_game(self):
        """Test simulating a single game."""
        result = simulate_one_game(agents=5, game_id=1, context="full")
        assert result.game_id == 1
        assert result.agent_count == 5
        assert result.context_condition == "full"
        assert 0.0 <= result.specialization_index <= 1.0
        assert 0.0 <= result.retrieval_efficiency <= 1.0

    def test_simulate_multiple_games(self):
        """Test simulating multiple games."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.csv"
            results = run_simulation(
                num_games=10,
                agent_count=5,
                context="full",
                seed=42,
                output_path=output_path,
            )
            assert len(results) == 10
            assert output_path.exists()

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "run1.csv"
            path2 = Path(tmpdir) / "run2.csv"

            run_simulation(10, 5, "full", seed=42, output_path=path1)
            run_simulation(10, 5, "full", seed=42, output_path=path2)

            with open(path1, "r") as f1, open(path2, "r") as f2:
                assert f1.read() == f2.read()


class TestCSVOutput:
    """Test CSV output generation."""

    def test_csv_schema(self):
        """Test that CSV has correct columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            run_simulation(5, 3, "full", seed=42, output_path=output_path)

            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames

            expected = [
                "game_id",
                "specialization_index",
                "retrieval_efficiency",
                "context_condition",
                "agent_count",
            ]
            assert fieldnames == expected

    def test_csv_content_validity(self):
        """Test that CSV content is valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            run_simulation(10, 5, "full", seed=42, output_path=output_path)

            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 10

            for row in rows:
                assert int(row["game_id"]) > 0
                assert 0.0 <= float(row["specialization_index"]) <= 1.0
                assert 0.0 <= float(row["retrieval_efficiency"]) <= 1.0
                assert row["context_condition"] in ["full", "limited"]
                assert int(row["agent_count"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])