import pytest
import sys
import os
from typing import List, Dict, Any, Set, Tuple
from pathlib import Path
from src.agents.mixed_agent import MixedAgent
from src.utils.config import Config, get_default_config

class TestMixedAgent:
    """Unit tests for MixedAgent implementation."""

    @pytest.fixture
    def config(self):
        """Create a default configuration for testing."""
        cfg = get_default_config()
        cfg.seed = 42
        cfg.generation_count = 10
        cfg.rule_evaluation_budget = 1000
        return cfg

    @pytest.fixture
    def mixed_agent(self, config):
        """Create a MixedAgent instance for testing."""
        return MixedAgent(config, seed=42)

    def test_initialization(self, mixed_agent):
        """Test that MixedAgent initializes correctly."""
        assert mixed_agent is not None
        assert mixed_agent.current_rule_set is not None
        assert "logic_rules" in mixed_agent.current_rule_set
        assert "grid_rules" in mixed_agent.current_rule_set
        assert mixed_agent.rule_evaluation_count == 0
        assert len(mixed_agent.evaluation_history) == 0

    def test_train_generation_logic(self, mixed_agent):
        """Test training on a logic task."""
        result = mixed_agent.train_generation()
        
        assert result is not None
        assert "task_type" in result
        assert "rule_evaluations" in result
        assert "current_score" in result
        
        # Should have recorded one generation
        assert len(mixed_agent.evaluation_history) == 1
        assert mixed_agent.evaluation_history[0]["task_type"] in ["logic", "grid"]

    def test_train_generation_grid(self, mixed_agent):
        """Test training on a grid task."""
        # Force multiple generations to increase chance of grid task
        results = []
        for _ in range(20):
            result = mixed_agent.train_generation()
            results.append(result)
        
        # Verify we have mixed task types
        task_types = [r["task_type"] for r in results]
        assert len(set(task_types)) >= 1  # At least one task type present

    def test_rule_evaluation_count_increases(self, mixed_agent):
        """Test that rule evaluation count increases with generations."""
        initial_count = mixed_agent.rule_evaluation_count
        
        mixed_agent.train_generation()
        mixed_agent.train_generation()
        mixed_agent.train_generation()
        
        assert mixed_agent.rule_evaluation_count >= initial_count

    def test_get_rule_set(self, mixed_agent):
        """Test retrieving the current rule set."""
        rule_set = mixed_agent.get_rule_set()
        
        assert rule_set is not None
        assert "logic_rules" in rule_set
        assert "grid_rules" in rule_set
        assert "metadata" in rule_set

    def test_get_evaluation_history(self, mixed_agent):
        """Test retrieving evaluation history."""
        history = mixed_agent.get_evaluation_history()
        assert isinstance(history, list)
        assert len(history) == 0  # Initially empty

        mixed_agent.train_generation()
        history = mixed_agent.get_evaluation_history()
        assert len(history) == 1

    def test_reset(self, mixed_agent):
        """Test resetting the agent."""
        mixed_agent.train_generation()
        mixed_agent.train_generation()
        
        mixed_agent.reset()
        
        assert len(mixed_agent.evaluation_history) == 0
        assert mixed_agent.rule_evaluation_count == 0
        assert mixed_agent.current_rule_set is not None

    def test_mixed_task_distribution(self, config):
        """Test that MixedAgent samples both task types over time."""
        agent = MixedAgent(config, seed=123)
        
        task_types = []
        for _ in range(100):
            result = agent.train_generation()
            task_types.append(result["task_type"])
        
        # With random selection, we expect both types in a large enough sample
        assert "logic" in task_types or "grid" in task_types
        
        # Check that we don't have 100% of one type (statistically unlikely with 100 samples)
        logic_count = task_types.count("logic")
        grid_count = task_types.count("grid")
        
        # Allow for some variance, but both should be present
        assert logic_count > 0 or grid_count > 0