"""
Unit tests for T015 output generation.

These tests verify that the T015 script produces the correct CSV structure
and that the metrics are computed correctly on real (simulated) data.
"""
import pytest
import csv
import tempfile
from pathlib import Path
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from t015_generate_full_results import run_single_game_experiment, write_results_to_csv

class TestT015OutputGeneration:
    """Test cases for T015 output generation."""

    def test_csv_structure(self):
        """Verify that the output CSV has the correct columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.csv"
            
            # Run a tiny experiment
            results = run_single_game_experiment(num_games=5, num_agents=3, seed=42)
            
            # Write to CSV
            write_results_to_csv(results, output_path)
            
            # Read back and verify structure
            assert output_path.exists(), "Output file was not created"
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                expected_headers = [
                    "game_id",
                    "specialization_index",
                    "retrieval_efficiency",
                    "context_condition",
                    "agent_count"
                ]
                
                assert headers == expected_headers, f"Expected {expected_headers}, got {headers}"
                
                rows = list(reader)
                assert len(rows) == 5, f"Expected 5 rows, got {len(rows)}"

    def test_metric_ranges(self):
        """Verify that computed metrics are within expected ranges."""
        results = run_single_game_experiment(num_games=10, num_agents=4, seed=42)
        
        for row in results:
            spec_idx = row['specialization_index']
            ret_eff = row['retrieval_efficiency']
            
            # Specialization index should be non-negative
            assert spec_idx >= 0, f"Specialization index {spec_idx} is negative"
            
            # Retrieval efficiency should be between 0 and 1
            assert 0 <= ret_eff <= 1, f"Retrieval efficiency {ret_eff} out of range [0, 1]"

    def test_context_condition(self):
        """Verify that context_condition is set to 'full'."""
        results = run_single_game_experiment(num_games=5, num_agents=3, seed=42)
        
        for row in results:
            assert row['context_condition'] == 'full', f"Expected 'full', got {row['context_condition']}"

    def test_agent_count_consistency(self):
        """Verify that agent_count matches the input argument."""
        for n_agents in [3, 5, 7]:
            results = run_single_game_experiment(num_games=5, num_agents=n_agents, seed=42)
            
            for row in results:
                assert row['agent_count'] == n_agents, f"Expected {n_agents}, got {row['agent_count']}"

    def test_reproducibility(self):
        """Verify that running with the same seed produces the same results."""
        results1 = run_single_game_experiment(num_games=10, num_agents=4, seed=123)
        results2 = run_single_game_experiment(num_games=10, num_agents=4, seed=123)
        
        # Compare metrics (should be identical due to fixed seed)
        for r1, r2 in zip(results1, results2):
            assert r1['specialization_index'] == r2['specialization_index'], \
                "Specialization index not reproducible"
            assert r1['retrieval_efficiency'] == r2['retrieval_efficiency'], \
                "Retrieval efficiency not reproducible"

    def test_empty_experiment_handling(self):
        """Verify behavior when no games can be run (edge case)."""
        # This is a theoretical test; in practice, the fallback should always provide data
        # We test the write function with empty results
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_results.csv"
            write_results_to_csv([], output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 0, "Expected empty file with headers only"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])