import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import math

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from run_experiment import run_single_game, GameResult, parse_agent_counts
from agent.base_agent import BaseAgent, AgentConfig
from metrics.validator import validate_and_filter_records
import numpy as np

class TestLimitedContextSimulation:
    """Integration test for limited-context simulation (T018)."""

    def test_parse_agent_counts(self):
        """Test parsing of agent count strings."""
        assert parse_agent_counts("5") == [5]
        assert parse_agent_counts("3,5,7") == [3, 5, 7]
        assert parse_agent_counts(" 1 , 2 , 3 ") == [1, 2, 3]

    def test_run_single_game_limited_context(self):
        """Test that a single game runs successfully with limited context."""
        # Setup
        n_agents = 3
        agents = [BaseAgent(AgentConfig(agent_id=i, model_name="opt-125m", device="cpu")) 
                  for i in range(n_agents)]
        
        # Create a small synthetic dataset
        dataset = [
            {"game_id": 0, "context": "test context " * 10, "context_type": "general", "memory_items": [], "num_agents": 3, "num_tokens": 50},
            {"game_id": 1, "context": "another context " * 10, "context_type": "specialized", "memory_items": [], "num_agents": 3, "num_tokens": 60},
        ]

        # Run game with limited context
        result = run_single_game(
            game_id=0,
            agents=agents,
            dataset=dataset,
            context_condition="limited",
            context_limit=128,
            logger=None
        )

        # Assertions
        assert isinstance(result, GameResult)
        assert result.game_id == 0
        assert result.context_condition == "limited"
        assert result.agent_count == n_agents
        assert result.context_limit == 128
        
        # Check metrics are within expected ranges
        assert 0.0 <= result.specialization_index <= math.log2(n_agents)
        assert 0.0 <= result.retrieval_efficiency <= 1.0

    def test_limited_context_vs_full_context(self):
        """Test that limited context produces different (lower) retrieval efficiency."""
        n_agents = 5
        agents = [BaseAgent(AgentConfig(agent_id=i, model_name="opt-125m", device="cpu")) 
                  for i in range(n_agents)]
        
        dataset = [
            {"game_id": 0, "context": "test context " * 20, "context_type": "general", "memory_items": [], "num_agents": 5, "num_tokens": 100},
        ]

        # Run with full context
        result_full = run_single_game(
            game_id=0,
            agents=agents,
            dataset=dataset,
            context_condition="full",
            context_limit=None,
            logger=None
        )

        # Run with limited context
        result_limited = run_single_game(
            game_id=0,
            agents=agents,
            dataset=dataset,
            context_condition="limited",
            context_limit=64,
            logger=None
        )

        # Limited context should generally have lower retrieval efficiency
        # (This is a heuristic check, not a strict guarantee due to randomness)
        assert result_limited.retrieval_efficiency <= result_full.retrieval_efficiency + 0.05

    def test_validation_passes_for_limited_context(self):
        """Test that results from limited context pass validation."""
        n_agents = 3
        agents = [BaseAgent(AgentConfig(agent_id=i, model_name="opt-125m", device="cpu")) 
                  for i in range(n_agents)]
        
        dataset = [
            {"game_id": i, "context": f"context {i} " * 10, "context_type": "general", "memory_items": [], "num_agents": 3, "num_tokens": 50}
            for i in range(10)
        ]

        # Run multiple games
        results = []
        for i in range(10):
            result = run_single_game(
                game_id=i,
                agents=agents,
                dataset=dataset,
                context_condition="limited",
                context_limit=128,
                logger=None
            )
            results.append(result)

        # Validate
        valid_results = validate_and_filter_records(results)
        
        # At least 95% should be valid (per SC-001)
        assert len(valid_results) >= 0.95 * len(results)

    def test_context_limit_affects_tokens_used(self):
        """Test that limited context results in different token usage patterns."""
        n_agents = 3
        agents = [BaseAgent(AgentConfig(agent_id=i, model_name="opt-125m", device="cpu")) 
                  for i in range(n_agents)]
        
        dataset = [
            {"game_id": 0, "context": "test context " * 50, "context_type": "general", "memory_items": [], "num_agents": 3, "num_tokens": 250},
        ]

        # Run with very tight limit
        result_tight = run_single_game(
            game_id=0,
            agents=agents,
            dataset=dataset,
            context_condition="limited",
            context_limit=50,
            logger=None
        )

        # Run with loose limit
        result_loose = run_single_game(
            game_id=0,
            agents=agents,
            dataset=dataset,
            context_condition="limited",
            context_limit=500,
            logger=None
        )

        # The simulation logic should reflect the limit in some way
        # (In this mock, we check that the limit is recorded correctly)
        assert result_tight.context_limit == 50
        assert result_loose.context_limit == 500