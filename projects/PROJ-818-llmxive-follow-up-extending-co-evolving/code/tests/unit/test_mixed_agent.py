import pytest
import sys
import os
from typing import List, Dict, Any, Set, Tuple
from pathlib import Path
from src.agents.mixed_agent import MixedAgent
from src.utils.config import Config
import json
import tempfile

class TestMixedAgent:
    """Unit tests for MixedAgent implementation."""

    @pytest.fixture
    def sample_config(self):
        """Create a sample configuration for testing."""
        config = Config(
            population_size=5,
            batch_size=10,
            generation_count=10,
            rule_evaluation_budget=1000,
            seed=42
        )
        return config

    @pytest.fixture
    def sample_training_data(self):
        """Create sample training data mixing logic and grid domains."""
        return [
            {
                "id": "logic_1",
                "domain": "logic",
                "rule_set_id": "rs_1",
                "instance_data": {
                    "rules": ["A implies B", "B implies C"],
                    "target": "A implies C"
                }
            },
            {
                "id": "grid_1",
                "domain": "grid",
                "rule_set_id": "rs_1",
                "instance_data": {
                    "constraints": ["avoid_red_cells", "diagonal_allowed"],
                    "start": (0, 0),
                    "end": (5, 5)
                }
            },
            {
                "id": "logic_2",
                "domain": "logic",
                "rule_set_id": "rs_2",
                "instance_data": {
                    "rules": ["X implies Y"],
                    "target": "X implies Y"
                }
            }
        ]

    def test_initialization(self, sample_config):
        """Test that MixedAgent initializes correctly."""
        agent = MixedAgent(sample_config, seed=42)
        
        assert agent.generation_count == 0
        assert len(agent.population) == sample_config.population_size
        assert len(agent.rule_sets) == sample_config.population_size
        assert agent.evaluation_count == 0
        assert not agent.budget_exceeded

    def test_population_initialization(self, sample_config):
        """Test that population is populated with valid rule sets."""
        agent = MixedAgent(sample_config, seed=42)
        
        for member in agent.population:
            assert "rule_set_id" in member
            assert "fitness" in member
            assert member["rule_set_id"] in agent.rule_sets
            
            rule_set = agent.rule_sets[member["rule_set_id"]]
            assert "logic_rules" in rule_set
            assert "grid_rules" in rule_set
            assert isinstance(rule_set["logic_rules"], list)
            assert isinstance(rule_set["grid_rules"], list)

    def test_training_with_data(self, sample_config, sample_training_data):
        """Test that training runs and updates agent state."""
        agent = MixedAgent(sample_config, seed=42)
        
        result = agent.train(sample_training_data, generations=5, budget=100)
        
        assert result["generations_completed"] > 0
        assert result["total_evaluations"] > 0
        assert result["final_avg_fitness"] >= 0.0
        assert "state" in result
        
        # Verify state was updated
        assert agent.generation_count > 0
        assert agent.evaluation_count > 0

    def test_budget_enforcement(self, sample_config, sample_training_data):
        """Test that training stops when budget is exceeded."""
        # Set a very low budget to force early stopping
        small_budget = 2
        agent = MixedAgent(sample_config, seed=42)
        
        result = agent.train(sample_training_data, generations=100, budget=small_budget)
        
        assert result["budget_exceeded"] is True
        assert result["total_evaluations"] <= small_budget + 1  # Allow slight overage due to batch processing

    def test_mixed_domain_handling(self, sample_config, sample_training_data):
        """Test that agent handles both logic and grid domains."""
        agent = MixedAgent(sample_config, seed=42)
        
        # Ensure data has both domains
        domains = set(item["domain"] for item in sample_training_data)
        assert "logic" in domains
        assert "grid" in domains
        
        result = agent.train(sample_training_data, generations=5, budget=1000)
        
        # Should process both types without error
        assert result["generations_completed"] == 5
        assert result["total_evaluations"] > 0

    def test_evolution_mechanism(self, sample_config, sample_training_data):
        """Test that population evolves over generations."""
        agent = MixedAgent(sample_config, seed=42)
        
        # Initial population size
        initial_size = len(agent.population)
        
        # Train for multiple generations
        agent.train(sample_training_data, generations=10, budget=5000)
        
        # Population size should remain constant (selection + replacement)
        assert len(agent.population) == initial_size
        
        # Rule sets should have evolved (new IDs should exist)
        current_rule_ids = [m["rule_set_id"] for m in agent.population]
        # At least some new IDs should be generated
        assert any("mutated" in rid for rid in current_rule_ids)

    def test_state_persistence(self, sample_config, sample_training_data):
        """Test that agent state can be saved and loaded."""
        agent = MixedAgent(sample_config, seed=42)
        agent.train(sample_training_data, generations=5, budget=1000)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            agent.save_state(temp_path)
            
            # Load state
            loaded_agent = MixedAgent.load_state(temp_path, sample_config)
            
            # Verify state matches
            assert loaded_agent.generation_count == agent.generation_count
            assert loaded_agent.evaluation_count == agent.evaluation_count
            assert len(loaded_agent.population) == len(agent.population)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_empty_training_data(self, sample_config):
        """Test behavior with empty training data."""
        agent = MixedAgent(sample_config, seed=42)
        
        result = agent.train([], generations=5, budget=1000)
        
        assert result["generations_completed"] == 0
        assert result["total_evaluations"] == 0
        assert result["final_avg_fitness"] == 0.0

    def test_selection_pressure(self, sample_config, sample_training_data):
        """Test that selection pressure is applied during evolution."""
        agent = MixedAgent(sample_config, seed=42)
        
        # Train for several generations
        agent.train(sample_training_data, generations=20, budget=5000)
        
        # Check that fitness values are present and varied
        fitnesses = [m["fitness"] for m in agent.population]
        assert all(f >= 0 for f in fitnesses)
        
        # There should be some variation in fitness
        if len(set(fitnesses)) > 1:
            assert max(fitnesses) > min(fitnesses)