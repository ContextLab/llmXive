"""
Integration test for limited-context simulation (User Story 2).

This test verifies that the limited-context experiment runs successfully
and produces valid output with expected schema.
"""
import csv
import os
import tempfile
from pathlib import Path

import pytest

from run_experiment import main, build_parser


class TestLimitedContextSimulation:
    """Integration tests for US-2 limited-context condition."""

    def test_limited_context_runs_and_writes_csv(self):
        """Test that limited-context simulation runs and writes results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results_limited.csv"
            
            # Run the experiment
            parser = build_parser()
            args = parser.parse_args([
                "--context", "limited",
                "--agents", "3",
                "--games", "10",
                "--output", str(output_path),
                "--seed", "42"
            ])
            
            # Execute main logic (we call the core functions directly to avoid sys.argv)
            from run_experiment import run_simulation, write_results_csv
            
            results = run_simulation(
                context_condition="limited",
                agent_counts=[3],
                num_games=10,
                dataset_name="wikidata_sample",
                context_threshold=256,
                seed=42
            )
            
            write_results_csv(results, str(output_path))
            
            # Verify output exists
            assert output_path.exists(), "Output CSV was not created"
            
            # Verify CSV schema
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 10, f"Expected 10 rows, got {len(rows)}"
            
            # Check required columns
            required_cols = {
                'game_id', 'agent_count', 'context_condition',
                'specialization_index', 'retrieval_efficiency', 'timestamp'
            }
            assert required_cols.issubset(set(rows[0].keys())), "Missing required columns"
            
            # Verify data types and ranges
            for row in rows:
                assert row['context_condition'] == 'limited'
                assert int(row['agent_count']) == 3
                spec = float(row['specialization_index'])
                ret = float(row['retrieval_efficiency'])
                assert 0.0 <= spec <= 1.0, f"Specialization out of range: {spec}"
                assert 0.0 <= ret <= 1.0, f"Retrieval efficiency out of range: {ret}"

    def test_limited_context_vs_full_context_metrics(self):
        """Test that limited and full contexts produce different metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            limited_path = Path(tmpdir) / "limited.csv"
            full_path = Path(tmpdir) / "full.csv"
            
            from run_experiment import run_simulation, write_results_csv
            
            # Run limited context
            limited_results = run_simulation(
                context_condition="limited",
                agent_counts=[5],
                num_games=50,
                dataset_name="wikidata_sample",
                context_threshold=128,  # Smaller threshold for more effect
                seed=123
            )
            write_results_csv(limited_results, str(limited_path))
            
            # Run full context
            full_results = run_simulation(
                context_condition="full",
                agent_counts=[5],
                num_games=50,
                dataset_name="wikidata_sample",
                context_threshold=128,
                seed=123
            )
            write_results_csv(full_results, str(full_path))
            
            # Compute means
            limited_ret = sum(float(r.retrieval_efficiency) for r in limited_results) / len(limited_results)
            full_ret = sum(float(r.retrieval_efficiency) for r in full_results) / len(full_results)
            
            # In limited context, retrieval efficiency should generally be lower
            # (or at least different) compared to full context
            # Note: This is a statistical expectation, not a hard guarantee for small N
            # We assert they are not identical (which would indicate a bug)
            assert abs(limited_ret - full_ret) > 0.001, \
                "Limited and full context retrieval efficiencies are suspiciously identical"

    def test_limited_context_with_multiple_agent_counts(self):
        """Test limited context with varying agent counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results_limited_multi.csv"
            
            from run_experiment import run_simulation, write_results_csv
            
            results = run_simulation(
                context_condition="limited",
                agent_counts=[3, 5, 7],
                num_games=10,
                dataset_name="wikidata_sample",
                context_threshold=256,
                seed=42
            )
            
            write_results_csv(results, str(output_path))
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Should have 30 rows (10 games * 3 agent counts)
            assert len(rows) == 30
            
            agent_counts_in_results = sorted(set(int(r['agent_count']) for r in rows))
            assert agent_counts_in_results == [3, 5, 7]
            assert all(r['context_condition'] == 'limited' for r in rows)