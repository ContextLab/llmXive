"""
Unit tests for scaling simulation in run_experiment.py.
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import csv
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from run_experiment import run_single_game, run_experiment, parse_agent_counts, GameResult

class TestScalingSimulation:
    """Tests for the scaling simulation functionality."""

    def test_parse_agent_counts_simple(self):
        """Test parsing simple agent count string."""
        result = parse_agent_counts("3,5,7")
        assert result == [3, 5, 7]

    def test_parse_agent_counts_range(self):
        """Test parsing agent count range."""
        result = parse_agent_counts("3-7")
        assert result == [3, 4, 5, 6, 7]

    def test_parse_agent_counts_mixed(self):
        """Test parsing mixed agent count string."""
        result = parse_agent_counts("3,5-7")
        assert result == [3, 5, 6, 7]

    def test_run_single_game_returns_valid_result(self):
        """Test that run_single_game returns a valid GameResult."""
        result = run_single_game(
            agent_count=5,
            context_condition="full",
            game_id=1,
            seed=42
        )
        
        assert isinstance(result, GameResult)
        assert result.agent_count == 5
        assert result.context_condition == "full"
        assert result.game_id == 1
        assert 0 <= result.specialization_index <= 2.32  # log2(5)
        assert 0 <= result.retrieval_efficiency <= 1.0

    def test_run_single_game_specialization_scales(self):
        """Test that specialization index scales with agent count."""
        result_3 = run_single_game(3, "full", 1, 42)
        result_7 = run_single_game(7, "full", 2, 42)
        
        # Specialization should increase with agent count
        assert result_7.specialization_index > result_3.specialization_index

    def test_run_experiment_generates_correct_number_of_results(self):
        """Test that run_experiment generates the correct number of results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = run_experiment(
                agent_counts=[3, 5],
                games_per_config=10,
                context_condition="full",
                output_dir=Path(tmpdir),
                seed=42
            )
            
            assert len(results) == 20  # 2 configs * 10 games
            
            # Check that results are distributed correctly
            counts = {}
            for r in results:
                counts[r.agent_count] = counts.get(r.agent_count, 0) + 1
            
            assert counts[3] == 10
            assert counts[5] == 10

    def test_run_experiment_saves_files(self):
        """Test that run_experiment saves output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_experiment(
                agent_counts=[3],
                games_per_config=5,
                context_condition="full",
                output_dir=Path(tmpdir),
                seed=42
            )
            
            # Check that files were created
            assert (Path(tmpdir) / "results_agents_3_full.csv").exists()
            assert (Path(tmpdir) / "results_scaling_full.csv").exists()

    def test_run_experiment_csv_format(self):
        """Test that output CSV has correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_experiment(
                agent_counts=[3],
                games_per_config=3,
                context_condition="full",
                output_dir=Path(tmpdir),
                seed=42
            )
            
            csv_path = Path(tmpdir) / "results_agents_3_full.csv"
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                expected_header = [
                    'game_id', 'agent_count', 'specialization_index',
                    'retrieval_efficiency', 'context_condition', 'is_synthetic'
                ]
                
                assert header == expected_header

    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with the same seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results1 = run_experiment(
                agent_counts=[3],
                games_per_config=5,
                context_condition="full",
                output_dir=Path(tmpdir),
                seed=42
            )
            
            results2 = run_experiment(
                agent_counts=[3],
                games_per_config=5,
                context_condition="full",
                output_dir=Path(tmpdir),
                seed=42
            )
            
            # Results should be identical
            for r1, r2 in zip(results1, results2):
                assert r1.specialization_index == r2.specialization_index
                assert r1.retrieval_efficiency == r2.retrieval_efficiency
