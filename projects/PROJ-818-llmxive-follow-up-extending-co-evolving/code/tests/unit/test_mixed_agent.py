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
        """Create a default config for testing."""
        cfg = get_default_config()
        cfg['population_size'] = 5
        cfg['max_generations'] = 3
        cfg['evaluations_per_generation'] = 10
        return cfg

    @pytest.fixture
    def agent(self, config):
        """Create a MixedAgent instance for testing."""
        return MixedAgent(config, run_id="test_run_1")

    def test_initialization(self, agent):
        """Test that MixedAgent initializes correctly."""
        assert agent.run_id == "test_run_1"
        assert len(agent.current_population) == 5
        assert agent.evaluation_stats.total_evaluations == 0
        assert len(agent.history) == 0

    def test_population_structure(self, agent):
        """Test that population members have the correct structure."""
        for individual in agent.current_population:
            assert 'logic_rules' in individual
            assert 'grid_rules' in individual
            assert 'fitness' in individual
            assert 'age' in individual
            assert individual['fitness'] == 0.0
            assert individual['age'] == 0
            assert isinstance(individual['logic_rules'], list)
            assert isinstance(individual['grid_rules'], list)

    def test_random_task_selection(self, agent):
        """Test that task domain selection is random."""
        domains = set()
        for _ in range(100):
            domain = agent._select_random_task_domain()
            domains.add(domain)
            assert domain in ['logic', 'grid']
        assert len(domains) == 2  # Should have seen both domains

    def test_train_generation_logic(self, agent):
        """Test training generation with logic tasks."""
        # Force logic domain by mocking
        original_select = agent._select_random_task_domain
        agent._select_random_task_domain = lambda: 'logic'
        
        stats = agent.train_generation(num_evaluations=5)
        
        assert stats['total_evaluations'] == 5
        assert stats['logic_evaluations'] == 5
        assert stats['grid_evaluations'] == 0
        assert len(agent.history) == 1
        assert agent.evaluation_stats.total_evaluations == 5

    def test_train_generation_grid(self, agent):
        """Test training generation with grid tasks."""
        # Force grid domain
        agent._select_random_task_domain = lambda: 'grid'
        
        stats = agent.train_generation(num_evaluations=5)
        
        assert stats['total_evaluations'] == 5
        assert stats['logic_evaluations'] == 0
        assert stats['grid_evaluations'] == 5
        assert len(agent.history) == 1

    def test_mixed_training_generation(self, agent):
        """Test training generation with mixed domains."""
        # Reset mock
        agent._select_random_task_domain = lambda: random.choice(['logic', 'grid'])
        import random as r
        r.seed(42)  # For reproducibility
        
        stats = agent.train_generation(num_evaluations=10)
        
        assert stats['total_evaluations'] == 10
        # Should have a mix of logic and grid evaluations
        total_domain_evals = stats['logic_evaluations'] + stats['grid_evaluations']
        assert total_domain_evals == 10
        assert stats['avg_fitness'] >= 0.0
        assert stats['avg_fitness'] <= 1.0

    def test_evaluation_stats_persistence(self, agent):
        """Test that evaluation stats are correctly accumulated."""
        initial_total = agent.evaluation_stats.total_evaluations
        
        agent.train_generation(num_evaluations=5)
        agent.train_generation(num_evaluations=3)
        
        assert agent.evaluation_stats.total_evaluations == initial_total + 8

    def test_save_and_load_state(self, agent, tmp_path):
        """Test saving and loading agent state."""
        filepath = tmp_path / "test_state.json"
        
        # Train a bit first
        agent.train_generation(num_evaluations=5)
        
        # Save state
        agent.save_state(str(filepath))
        assert filepath.exists()
        
        # Load into new agent
        new_agent = MixedAgent(agent.config, run_id="new_run")
        new_agent.load_state(str(filepath))
        
        assert new_agent.run_id == "test_run_1"  # Run ID from saved state
        assert len(new_agent.current_population) == len(agent.current_population)
        assert new_agent.evaluation_stats.total_evaluations == agent.evaluation_stats.total_evaluations

    def test_get_population(self, agent):
        """Test that get_population returns the correct population."""
        population = agent.get_population()
        assert len(population) == 5
        assert population is agent.current_population

    def test_get_evaluation_stats(self, agent):
        """Test that get_evaluation_stats returns correct stats."""
        stats = agent.get_evaluation_stats()
        assert stats.total_evaluations == 0
        assert stats.logic_evaluations == 0
        assert stats.grid_evaluations == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])