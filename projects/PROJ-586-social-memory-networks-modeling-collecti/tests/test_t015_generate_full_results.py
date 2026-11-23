"""Tests for T015 implementation."""
import pytest
import csv
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from t015_generate_full_results import (
    simulate_one_game_realistic,
    run_simulation,
    parse_args,
    MIN_SUCCESS_ROWS,
    TARGET_GAMES
)
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from memory.buffer import MemoryBuffer, reset_shared_buffer


class TestT015Simulation:
    """Test suite for T015 simulation functions."""

    def test_simulate_one_game_returns_valid_result(self):
        """Test that simulate_one_game returns a valid result dictionary."""
        import random
        rng = random.Random(42)
        
        result = simulate_one_game_realistic(game_id=1, num_agents=5, rng=rng)
        
        assert isinstance(result, dict)
        assert "game_id" in result
        assert "specialization_index" in result
        assert "retrieval_efficiency" in result
        assert "context_condition" in result
        assert "agent_count" in result
        assert result["context_condition"] == "full"
        assert result["agent_count"] == 5
        assert result["success"] is True

    def test_specialization_index_bounds(self):
        """Test that specialization index is within expected bounds."""
        import random
        rng = random.Random(42)
        
        result = simulate_one_game_realistic(game_id=1, num_agents=5, rng=rng)
        
        # Specialization index should be between 0 and log2(5)
        import math
        max_index = math.log2(5)
        assert 0.0 <= result["specialization_index"] <= max_index

    def test_retrieval_efficiency_bounds(self):
        """Test that retrieval efficiency is between 0 and 1."""
        import random
        rng = random.Random(42)
        
        result = simulate_one_game_realistic(game_id=1, num_agents=5, rng=rng)
        
        assert 0.0 <= result["retrieval_efficiency"] <= 1.0

    def test_buffer_reset_between_games(self):
        """Test that memory buffer is reset between games."""
        import random
        rng = random.Random(42)
        
        # First game
        result1 = simulate_one_game_realistic(game_id=1, num_agents=3, rng=rng)
        
        # Second game should start with empty buffer
        result2 = simulate_one_game_realistic(game_id=2, num_agents=3, rng=rng)
        
        # Both should succeed independently
        assert result1["success"] is True
        assert result2["success"] is True

    def test_run_simulation_creates_csv(self, tmp_path):
        """Test that run_simulation creates a valid CSV file."""
        output_file = tmp_path / "test_results.csv"
        
        success_count = run_simulation(
            num_games=10,
            num_agents=3,
            seed=42,
            output_path=str(output_file)
        )
        
        assert success_count >= 9  # At least 90% success rate
        assert output_file.exists()
        
        # Verify CSV structure
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == success_count
            assert "game_id" in reader.fieldnames
            assert "specialization_index" in reader.fieldnames
            assert "retrieval_efficiency" in reader.fieldnames
            assert "context_condition" in reader.fieldnames
            assert "agent_count" in reader.fieldnames

    def test_csv_column_values(self, tmp_path):
        """Test that CSV column values are valid."""
        output_file = tmp_path / "test_results.csv"
        
        run_simulation(
            num_games=5,
            num_agents=4,
            seed=42,
            output_path=str(output_file)
        )
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check game_id is integer
                assert row["game_id"].isdigit()
                
                # Check metrics are numeric
                assert float(row["specialization_index"]) >= 0
                assert float(row["retrieval_efficiency"]) >= 0
                assert float(row["retrieval_efficiency"]) <= 1
                
                # Check context condition
                assert row["context_condition"] == "full"
                
                # Check agent count
                assert row["agent_count"] == "4"

    def test_seed_reproducibility(self, tmp_path):
        """Test that same seed produces same results."""
        output1 = tmp_path / "results1.csv"
        output2 = tmp_path / "results2.csv"
        
        run_simulation(num_games=10, num_agents=3, seed=123, output_path=str(output1))
        run_simulation(num_games=10, num_agents=3, seed=123, output_path=str(output2))
        
        with open(output1, 'r') as f1, open(output2, 'r') as f2:
            content1 = f1.read()
            content2 = f2.read()
            assert content1 == content2

    def test_high_success_rate(self, tmp_path):
        """Test that simulation achieves high success rate (>95%)."""
        output_file = tmp_path / "test_results.csv"
        
        success_count = run_simulation(
            num_games=100,
            num_agents=5,
            seed=42,
            output_path=str(output_file)
        )
        
        success_rate = success_count / 100
        assert success_rate >= 0.95, f"Success rate {success_rate} is below 95%"

class TestMetricsIntegration:
    """Test integration with metrics modules."""

    def test_specialization_index_computation(self):
        """Test specialization index computation with various inputs."""
        # Empty input
        idx, metrics = compute_specialization_index([], num_agents=3)
        assert idx == 0.0
        
        # Uniform distribution
        facts = [["a"], ["b"], ["c"]]
        idx, metrics = compute_specialization_index(facts, num_agents=3)
        assert idx > 0  # Should have some specialization

    def test_retrieval_efficiency_computation(self):
        """Test retrieval efficiency computation."""
        # Perfect retrieval
        eff, metrics = compute_retrieval_efficiency(10, 10, 3)
        assert eff == 1.0
        
        # No retrieval
        eff, metrics = compute_retrieval_efficiency(0, 10, 3)
        assert eff == 0.0
        
        # Partial retrieval
        eff, metrics = compute_retrieval_efficiency(5, 10, 3)
        assert 0 < eff < 1

class TestParseArgs:
    """Test argument parsing."""

    def test_default_values(self):
        """Test default argument values."""
        import sys
        sys.argv = ["test"]  # Simulate no arguments
        args = parse_args()
        
        assert args.games == TARGET_GAMES
        assert args.agents == 5
        assert args.seed == 42

    def test_custom_values(self):
        """Test custom argument values."""
        import sys
        sys.argv = ["test", "--games", "50", "--agents", "3", "--seed", "123"]
        args = parse_args()
        
        assert args.games == 50
        assert args.agents == 3
        assert args.seed == 123