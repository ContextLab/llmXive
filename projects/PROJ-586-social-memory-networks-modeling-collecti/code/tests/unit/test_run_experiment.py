"""
Unit tests for run_experiment.py
"""
import pytest
import tempfile
from pathlib import Path
import sys

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_experiment import (
    GameResult,
    ExperimentConfig,
    simulate_one_game,
    run_simulation,
    write_results_csv
)


class TestExperimentConfig:
    def test_config_creation(self):
        config = ExperimentConfig(
            context_condition="full",
            agent_counts=[3, 5],
            num_games=10,
            seed=42
        )
        assert config.context_condition == "full"
        assert config.agent_counts == [3, 5]
        assert config.num_games == 10
        assert config.seed == 42


class TestSimulateOneGame:
    def test_simulate_full_context(self):
        config = ExperimentConfig(
            context_condition="full",
            agent_counts=[3],
            num_games=1,
            seed=42
        )
        spec_metrics, ret_metrics, result = simulate_one_game(1, config)

        assert isinstance(result, GameResult)
        assert result.game_id == 1
        assert result.context_condition == "full"
        assert result.agent_count == 3
        assert result.specialization_index >= 0.0
        assert result.specialization_index <= 1.0
        assert result.retrieval_efficiency >= 0.0
        assert result.retrieval_efficiency <= 1.0
        assert len(result.agent_skills) == 3

    def test_simulate_limited_context(self):
        config = ExperimentConfig(
            context_condition="limited",
            agent_counts=[3],
            num_games=1,
            seed=42
        )
        spec_metrics, ret_metrics, result = simulate_one_game(1, config)

        assert isinstance(result, GameResult)
        assert result.context_condition == "limited"
        # In limited context, retrieval might be lower, but we just check validity
        assert result.retrieval_efficiency >= 0.0


class TestRunSimulation:
    def test_run_simulation_single_count(self):
        config = ExperimentConfig(
            context_condition="full",
            agent_counts=[3],
            num_games=5,
            seed=42
        )
        results = run_simulation(config)

        assert len(results) == 5
        for r in results:
            assert r.agent_count == 3
            assert r.context_condition == "full"

    def test_run_simulation_multiple_counts(self):
        config = ExperimentConfig(
            context_condition="full",
            agent_counts=[3, 5],
            num_games=2,
            seed=42
        )
        results = run_simulation(config)

        # Should run 2 games for 3 agents, and 2 games for 5 agents
        assert len(results) == 4
        counts = [r.agent_count for r in results]
        assert counts.count(3) == 2
        assert counts.count(5) == 2


class TestWriteResultsCsv:
    def test_write_csv(self):
        config = ExperimentConfig(
            context_condition="full",
            agent_counts=[3],
            num_games=2,
            seed=42
        )
        results = run_simulation(config)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        try:
            write_results_csv(results, temp_path)
            assert temp_path.exists()
            content = temp_path.read_text()
            assert "game_id" in content
            assert "specialization_index" in content
            assert "retrieval_efficiency" in content
        finally:
            temp_path.unlink()
