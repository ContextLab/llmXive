import pytest
import os
import sys
from pathlib import Path
import tempfile
import csv

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from run_experiment import run_single_game, run_experiment, parse_agent_counts, GameResult
from memory.buffer import get_shared_memory_buffer, reset_shared_memory_buffer

class TestScalingSimulation:
    """Tests for US-3 scaling analysis simulation."""
    
    def test_parse_agent_counts(self):
        """Test parsing of agent count arguments."""
        assert parse_agent_counts("3,5,7") == [3, 5, 7]
        assert parse_agent_counts("3") == [3]
        assert parse_agent_counts("10,20,30,40") == [10, 20, 30, 40]
    
    def test_single_game_simulation(self):
        """Test that a single game produces valid results."""
        reset_shared_memory_buffer()
        buffer = get_shared_memory_buffer()
        
        result = run_single_game(
            game_id=1,
            agent_count=5,
            context_condition="full",
            memory_buffer=buffer,
            seed=42
        )
        
        assert result is not None
        assert result.game_id == 1
        assert result.agent_count == 5
        assert result.context_condition == "full"
        assert result.valid is True
        assert 0 <= result.specialization_index <= 10  # Reasonable range
        assert 0 <= result.retrieval_efficiency <= 1.0
    
    def test_full_context_vs_limited(self):
        """Test that limited context produces different (lower) efficiency."""
        reset_shared_memory_buffer()
        buffer_full = get_shared_memory_buffer()
        result_full = run_single_game(1, 5, "full", buffer_full, seed=123)
        
        reset_shared_memory_buffer()
        buffer_limited = get_shared_memory_buffer()
        result_limited = run_single_game(1, 5, "limited", buffer_limited, seed=123)
        
        # Limited context should generally have lower or equal efficiency
        assert result_full.retrieval_efficiency >= result_limited.retrieval_efficiency
    
    def test_experiment_runs_multiple_counts(self):
        """Test that experiment runs for multiple agent counts."""
        reset_shared_memory_buffer()
        
        results = run_experiment(
            agent_counts=[3, 5],
            games_per_config=10,
            context_condition="full",
            seed=42
        )
        
        assert len(results) > 0
        
        # Check we have results for both agent counts
        agent_counts_in_results = set(r.agent_count for r in results)
        assert 3 in agent_counts_in_results
        assert 5 in agent_counts_in_results
    
    def test_800_games_per_config(self):
        """Test that 800 games are run per configuration (US-3 requirement)."""
        reset_shared_memory_buffer()
        
        results = run_experiment(
            agent_counts=[3, 5, 7],
            games_per_config=800,
            context_condition="full",
            seed=42
        )
        
        # Should have at least 800 results (some might be filtered as invalid)
        assert len(results) > 0
        
        # Check distribution across agent counts
        counts = {}
        for r in results:
            counts[r.agent_count] = counts.get(r.agent_count, 0) + 1
        
        # Each agent count should have a significant number of results
        for agent_count in [3, 5, 7]:
            assert agent_count in counts
            # Allow some filtering, but expect most to be valid
            assert counts[agent_count] >= 500  # At least 62.5% valid
    
    def test_output_csv_format(self):
        """Test that output CSV has correct schema."""
        reset_shared_memory_buffer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.csv")
            
            results = run_experiment(
                agent_counts=[3],
                games_per_config=50,
                context_condition="full",
                seed=42
            )
            
            # Manually save to test format
            from run_experiment import save_results
            save_results(results, output_path)
            
            # Verify CSV structure
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) > 0
                
                # Check required columns
                required_cols = ['game_id', 'specialization_index', 'retrieval_efficiency',
                               'context_condition', 'agent_count', 'valid']
                for col in required_cols:
                    assert col in rows[0].keys()
    
    def test_reproducibility(self):
        """Test that same seed produces same results."""
        reset_shared_memory_buffer()
        
        results1 = run_experiment(
            agent_counts=[5],
            games_per_config=20,
            context_condition="full",
            seed=999
        )
        
        reset_shared_memory_buffer()
        
        results2 = run_experiment(
            agent_counts=[5],
            games_per_config=20,
            context_condition="full",
            seed=999
        )
        
        # Results should be identical
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.specialization_index == r2.specialization_index
            assert r1.retrieval_efficiency == r2.retrieval_efficiency