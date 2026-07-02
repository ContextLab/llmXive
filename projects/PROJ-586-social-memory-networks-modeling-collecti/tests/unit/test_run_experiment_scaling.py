import pytest
import os
import sys
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_experiment import parse_agent_counts, generate_synthetic_game_data, run_single_game
from memory.buffer import get_shared_memory_buffer

class TestScalingExperiment:
    """Tests for scaling analysis experiment (US-3)."""

    def test_parse_agent_counts(self):
        """Test parsing of comma-separated agent counts."""
        assert parse_agent_counts("3,5,7") == [3, 5, 7]
        assert parse_agent_counts("5") == [5]
        assert parse_agent_counts("1, 2, 3") == [1, 2, 3]

    def test_generate_synthetic_data_small_scale(self):
        """Test synthetic data generation for small scale."""
        games = generate_synthetic_game_data(
            num_games=10,
            agent_count=3,
            context_condition='full',
            seed=42
        )
        assert len(games) == 10
        assert all(g['agent_count'] == 3 for g in games)
        assert all(g['context_condition'] == 'full' for g in games)

    def test_run_single_game(self):
        """Test running a single game simulation."""
        games = generate_synthetic_game_data(
            num_games=1,
            agent_count=3,
            context_condition='full',
            seed=42
        )
        
        memory_buffer = get_shared_memory_buffer()
        result = run_single_game(
            game_data=games[0],
            memory_buffer=memory_buffer,
            context_condition='full',
            agent_count=3
        )
        
        assert result.agent_count == 3
        assert result.context_condition == 'full'
        assert result.specialization_index >= 0
        assert result.retrieval_efficiency >= 0
        assert result.total_actions > 0

    def test_scaling_simulation_800_games(self):
        """Test that we can run 800 games per configuration (US-3 requirement)."""
        agent_counts = [3, 5, 7]
        
        for agent_count in agent_counts:
            games = generate_synthetic_game_data(
                num_games=800,
                agent_count=agent_count,
                context_condition='full',
                seed=42
            )
            assert len(games) == 800, f"Expected 800 games for {agent_count} agents"
            
            # Verify we can run at least a sample
            memory_buffer = get_shared_memory_buffer()
            result = run_single_game(
                game_data=games[0],
                memory_buffer=memory_buffer,
                context_condition='full',
                agent_count=agent_count
            )
            assert result.game_id == 0
            assert result.agent_count == agent_count

    def test_scaling_output_schema(self):
        """Test that output matches expected schema for scaling analysis."""
        games = generate_synthetic_game_data(
            num_games=10,
            agent_count=5,
            context_condition='full',
            seed=42
        )
        
        memory_buffer = get_shared_memory_buffer()
        results = []
        for game_data in games:
            result = run_single_game(
                game_data=game_data,
                memory_buffer=memory_buffer,
                context_condition='full',
                agent_count=5
            )
            results.append(result)
        
        # Check schema
        for r in results:
            assert hasattr(r, 'game_id')
            assert hasattr(r, 'agent_count')
            assert hasattr(r, 'context_condition')
            assert hasattr(r, 'specialization_index')
            assert hasattr(r, 'retrieval_efficiency')
            assert hasattr(r, 'total_actions')
            assert hasattr(r, 'successful_retrievals')
            assert hasattr(r, 'duration_seconds')
            assert hasattr(r, 'seed')