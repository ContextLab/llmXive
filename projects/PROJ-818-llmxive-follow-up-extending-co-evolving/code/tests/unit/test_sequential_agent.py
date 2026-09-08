"""
Unit tests for the SequentialAgent implementation.
"""
import pytest
import sys
import os
from typing import List, Dict, Any
from pathlib import Path
from src.agents.sequential_agent import SequentialAgent
from src.utils.config import get_default_config

class TestSequentialAgent:
    """Test suite for SequentialAgent."""

    @pytest.fixture
    def config(self):
        """Create a default configuration for testing."""
        return get_default_config()

    @pytest.fixture
    def agent(self, config):
        """Create a SequentialAgent instance for testing."""
        return SequentialAgent(config, seed=42)

    @pytest.fixture
    def sample_logic_data(self):
        """Generate sample logic proof data."""
        return [
            {
                "type": "logic",
                "premises": ["P0 IMPLIES P1", "P0"],
                "conclusion": "P1",
                "id": f"logic_{i}"
            }
            for i in range(10)
        ]

    @pytest.fixture
    def sample_grid_data(self):
        """Generate sample grid world data."""
        return [
            {
                "type": "grid",
                "size": 5,
                "start": (0, 0),
                "goal": (4, 4),
                "obstacles": [(1, 1), (2, 2)],
                "id": f"grid_{i}"
            }
            for i in range(10)
        ]

    def test_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.current_domain_index == 0
        assert agent.domains == ['logic', 'grid']
        assert all(v == 0 for v in agent.domain_progress.values())
        assert all(v == 0 for v in agent.evaluation_counts.values())

    def test_train_step_logic(self, agent, sample_logic_data):
        """Test training step on logic domain."""
        batch = sample_logic_data[:5]
        result = agent.train_step(batch, 'logic')
        
        assert result['domain'] == 'logic'
        assert result['batch_size'] == 5
        assert 'accuracy' in result
        assert result['total_evaluations'] == 5

    def test_train_step_grid(self, agent, sample_grid_data):
        """Test training step on grid domain."""
        batch = sample_grid_data[:5]
        result = agent.train_step(batch, 'grid')
        
        assert result['domain'] == 'grid'
        assert result['batch_size'] == 5
        assert 'accuracy' in result
        assert result['total_evaluations'] == 5

    def test_train_on_domain(self, agent, sample_logic_data):
        """Test training exclusively on one domain."""
        result = agent.train_on_domain('logic', sample_logic_data, steps_per_epoch=3)
        
        assert result['domain'] == 'logic'
        assert result['epochs_completed'] == 3
        assert 'avg_accuracy' in result
        assert result['total_samples_processed'] > 0

    def test_train_full_sequence(self, agent, sample_logic_data, sample_grid_data):
        """Test the full sequential training protocol."""
        result = agent.train_full_sequence(
            logic_data=sample_logic_data,
            grid_data=sample_grid_data,
            steps_per_domain=2
        )
        
        assert 'training_order' in result
        assert result['training_order'] == ['logic', 'grid']
        assert 'logic' in result['domain_results']
        assert 'grid' in result['domain_results']
        assert 'final_state' in result
        
        # Verify evaluation counts are tracked
        total_evals = result['final_state']['total_evaluations']
        assert total_evals > 0

    def test_invalid_domain(self, agent, sample_logic_data):
        """Test that training on invalid domain raises error."""
        with pytest.raises(ValueError):
            agent.train_on_domain('invalid_domain', sample_logic_data)

    def test_empty_batch(self, agent):
        """Test handling of empty batch."""
        result = agent.train_step([], 'logic')
        assert result['status'] == 'skipped'
        assert result['reason'] == 'empty_batch'

    def test_no_data(self, agent):
        """Test training with no data."""
        result = agent.train_on_domain('logic', [], steps_per_epoch=5)
        assert result['status'] == 'skipped'
        assert result['reason'] == 'no_data'

    def test_get_state(self, agent):
        """Test state retrieval."""
        state = agent.get_state()
        
        assert 'rule_set' in state
        assert 'evaluation_counts' in state
        assert 'domain_progress' in state
        assert 'history_length' in state

    def test_set_state(self, agent):
        """Test state restoration."""
        initial_state = agent.get_state()
        
        # Modify state
        initial_state['rule_set'] = ['test_rule']
        initial_state['evaluation_counts'] = {'logic': 10, 'grid': 5}
        
        agent.set_state(initial_state)
        
        restored_state = agent.get_state()
        assert restored_state['rule_set'] == ['test_rule']
        assert restored_state['evaluation_counts']['logic'] == 10

    def test_average_accuracy(self, agent, sample_logic_data, sample_grid_data):
        """Test average accuracy calculation."""
        # Initially should be 0
        assert agent.get_average_accuracy() == 0.0
        
        # Train and check
        agent.train_on_domain('logic', sample_logic_data, steps_per_epoch=1)
        avg_acc = agent.get_average_accuracy()
        assert isinstance(avg_acc, float)
        assert 0.0 <= avg_acc <= 1.0

    def test_save_results(self, agent, tmp_path, sample_logic_data, sample_grid_data):
        """Test saving results to file."""
        agent.train_full_sequence(sample_logic_data, sample_grid_data, steps_per_domain=1)
        
        output_path = tmp_path / "test_results.json"
        agent.save_results(str(output_path))
        
        assert output_path.exists()
        
        # Verify file is valid JSON
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'agent_type' in data
        assert data['agent_type'] == 'SequentialAgent'
        assert 'final_state' in data