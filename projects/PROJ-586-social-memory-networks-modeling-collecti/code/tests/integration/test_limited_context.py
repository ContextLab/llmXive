"""
Integration test for limited-context simulation.

This test verifies that the limited-context simulation runs correctly,
produces valid metrics, and outputs the expected CSV file.
"""
import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import math
import tempfile
import pandas as pd

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_dir))

from run_experiment import parse_args, run_experiment
from data.loaders import generate_all_datasets, get_dataset_spec
from metrics.retrieval import compute_retrieval_efficiency, validate_retrieval_efficiency
from metrics.specialization import compute_specialization_index, validate_specialization_index
from metrics.validator import validate_experiment_metrics


class TestLimitedContextSimulation:
    """Integration tests for limited-context simulation."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def limited_context_args(self, temp_output_dir):
        """Create arguments for limited-context simulation."""
        return {
            'context': 'limited',
            'agents': 3,
            'games': 10,  # Use small number for integration test
            'output_dir': str(temp_output_dir),
            'context_window': 256,
            'seed': 42,
        }

    def test_limited_context_simulation_runs(self, limited_context_args):
        """Test that limited-context simulation runs without errors."""
        # Create args namespace
        args = type('Args', (), limited_context_args)()

        # Run the simulation
        results = run_experiment(args)

        # Verify results are returned
        assert results is not None
        assert 'games' in results
        assert 'metrics' in results

    def test_limited_context_produces_valid_metrics(self, limited_context_args):
        """Test that limited-context simulation produces valid metrics."""
        args = type('Args', (), limited_context_args)()
        results = run_experiment(args)

        # Validate specialization metrics
        specialization_valid = validate_specialization_index(
            results['metrics']['specialization']
        )
        assert specialization_valid.valid, f"Specialization validation failed: {specialization_valid.reason}"

        # Validate retrieval metrics
        retrieval_valid = validate_retrieval_efficiency(
            results['metrics']['retrieval']
        )
        assert retrieval_valid.valid, f"Retrieval validation failed: {retrieval_valid.reason}"

    def test_limited_context_output_file_created(self, limited_context_args):
        """Test that limited-context simulation creates output CSV file."""
        args = type('Args', (), limited_context_args)()
        run_experiment(args)

        # Check that output file was created
        output_path = Path(args.output_dir) / 'results_limited.csv'
        assert output_path.exists(), f"Output file not created: {output_path}"

        # Load and verify CSV contents
        df = pd.read_csv(output_path)

        # Verify required columns exist
        required_columns = [
            'game_id',
            'specialization_index',
            'retrieval_efficiency',
            'context_condition',
            'agent_count'
        ]
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

        # Verify context condition is 'limited'
        assert all(df['context_condition'] == 'limited'), "Context condition should be 'limited'"

    def test_limited_context_metrics_in_expected_range(self, limited_context_args):
        """Test that limited-context metrics are within expected ranges."""
        args = type('Args', (), limited_context_args)()
        results = run_experiment(args)

        # Check specialization index range (0 to log2(N_agents))
        n_agents = args.agents
        max_specialization = math.log2(n_agents)
        spec_values = results['metrics']['specialization']['values']

        for spec in spec_values:
            assert 0 <= spec <= max_specialization, \
                f"Specialization {spec} out of range [0, {max_specialization}]"

        # Check retrieval efficiency range (0 to 1)
        retrieval_values = results['metrics']['retrieval']['values']
        for eff in retrieval_values:
            assert 0 <= eff <= 1, f"Retrieval efficiency {eff} out of range [0, 1]"

    def test_limited_context_game_count(self, limited_context_args):
        """Test that the correct number of games are simulated."""
        args = type('Args', (), limited_context_args)()
        results = run_experiment(args)

        assert len(results['games']) == args.games, \
            f"Expected {args.games} games, got {len(results['games'])}"

    def test_limited_context_reproducible_with_seed(self, temp_output_dir):
        """Test that limited-context simulation is reproducible with seed."""
        # Run first simulation
        args1 = type('Args', (), {
            'context': 'limited',
            'agents': 3,
            'games': 10,
            'output_dir': str(temp_output_dir / 'run1'),
            'context_window': 256,
            'seed': 42,
        })()
        results1 = run_experiment(args1)

        # Run second simulation with same seed
        args2 = type('Args', (), {
            'context': 'limited',
            'agents': 3,
            'games': 10,
            'output_dir': str(temp_output_dir / 'run2'),
            'context_window': 256,
            'seed': 42,
        })()
        results2 = run_experiment(args2)

        # Compare results (should be identical with same seed)
        assert len(results1['games']) == len(results2['games'])

        # Compare first game metrics
        assert results1['games'][0]['specialization_index'] == \
               results2['games'][0]['specialization_index']
        assert results1['games'][0]['retrieval_efficiency'] == \
               results2['games'][0]['retrieval_efficiency']

    def test_limited_context_validation_passes(self, limited_context_args):
        """Test that limited-context metrics pass validation requirements."""
        args = type('Args', (), limited_context_args)()
        results = run_experiment(args)

        # Validate all experiment metrics
        validation = validate_experiment_metrics(
            results['games'],
            min_valid_percentage=0.95
        )

        assert validation.valid, \
            f"Experiment validation failed: {validation.reason}. " \
            f"Valid percentage: {validation.valid_percentage:.2%}"

    def test_limited_context_vs_full_context_structure(self, limited_context_args, temp_output_dir):
        """Test that limited-context output has same structure as full-context."""
        # Run limited-context
        args_limited = type('Args', (), {
            'context': 'limited',
            'agents': 3,
            'games': 10,
            'output_dir': str(temp_output_dir / 'limited'),
            'context_window': 256,
            'seed': 42,
        })()
        run_experiment(args_limited)

        # Run full-context for comparison
        args_full = type('Args', (), {
            'context': 'full',
            'agents': 3,
            'games': 10,
            'output_dir': str(temp_output_dir / 'full'),
            'context_window': 1024,
            'seed': 42,
        })()
        run_experiment(args_full)

        # Load both CSV files
        limited_df = pd.read_csv(Path(temp_output_dir / 'limited' / 'results_limited.csv'))
        full_df = pd.read_csv(Path(temp_output_dir / 'full' / 'results_full.csv'))

        # Verify same structure
        assert list(limited_df.columns) == list(full_df.columns), \
            "Limited and full context outputs should have same columns"

        assert len(limited_df) == len(full_df), \
            "Both simulations should produce same number of games"

    def test_limited_context_agent_count_parameter(self, temp_output_dir):
        """Test that limited-context simulation respects agent count parameter."""
        for n_agents in [3, 5, 7]:
            args = type('Args', (), {
                'context': 'limited',
                'agents': n_agents,
                'games': 5,
                'output_dir': str(temp_output_dir / f'agents_{n_agents}'),
                'context_window': 256,
                'seed': 42,
            })()
            run_experiment(args)

            # Verify output
            output_path = Path(args.output_dir) / 'results_limited.csv'
            assert output_path.exists()

            df = pd.read_csv(output_path)
            assert all(df['agent_count'] == n_agents), \
                f"Agent count should be {n_agents} for all rows"

            # Verify specialization index max is log2(n_agents)
            max_specialization = math.log2(n_agents)
            assert all(df['specialization_index'] <= max_specialization), \
                f"Specialization should not exceed {max_specialization}"