import pytest
import sys
import os
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.sequential_agent import SequentialAgent
from src.utils.config import Config

class TestSequentialAgent:
    """Unit tests for SequentialAgent."""

    @pytest.fixture
    def config(self):
        return Config(seed=42, max_generations=10)

    @pytest.fixture
    def agent(self, config):
        return SequentialAgent(config, seed=42)

    def test_initial_state(self, agent):
        """Test that agent initializes with correct default state."""
        assert agent.current_domain_index == 0
        assert agent.domain_history == []
        assert agent.evaluation_count == 0
        assert agent.rule_sets == {}

    def test_domain_block_grouping(self, agent):
        """Test that training data is correctly grouped into domain blocks."""
        training_data = [
            {'domain_type': 'logic', 'data': {}},
            {'domain_type': 'grid', 'data': {}},
            {'domain_type': 'logic', 'data': {}},
            {'domain_type': 'grid', 'data': {}},
        ]
        
        blocks = agent._get_domain_blocks(training_data)
        
        # Should have 2 blocks: logic and grid
        assert len(blocks) == 2
        
        # Check contents (sorted by domain name)
        assert blocks[0][0]['domain_type'] == 'grid'
        assert blocks[1][0]['domain_type'] == 'logic'
        
        # Check counts
        assert len(blocks[0]) == 2
        assert len(blocks[1]) == 2

    def test_training_updates_history(self, agent):
        """Test that training updates domain history."""
        training_data = [
            {'domain_type': 'logic', 'data': {'axioms': ['A'], 'conclusion': 'A'}},
            {'domain_type': 'grid', 'data': {'size': [5, 5], 'start': [0, 0], 'end': [4, 4], 'obstacles': []}}
        ]
        
        agent.train(training_data, max_generations=4)
        
        assert len(agent.domain_history) == 2
        assert 'grid' in agent.domain_history
        assert 'logic' in agent.domain_history
        assert agent.evaluation_count > 0

    def test_reset(self, agent):
        """Test that reset clears state."""
        # Train first to change state
        training_data = [
            {'domain_type': 'logic', 'data': {'axioms': ['A'], 'conclusion': 'A'}}
        ]
        agent.train(training_data, max_generations=1)
        
        # Verify state changed
        assert agent.evaluation_count > 0
        
        # Reset
        agent.reset()
        
        # Verify state reset
        assert agent.current_domain_index == 0
        assert agent.domain_history == []
        assert agent.evaluation_count == 0
        assert agent.rule_sets == {}

    def test_empty_training_data(self, agent):
        """Test handling of empty training data."""
        state = agent.train([], max_generations=10)
        assert state['evaluation_count'] == 0
        assert state['domain_history'] == []

    def test_single_domain_training(self, agent):
        """Test training with only one domain type."""
        training_data = [
            {'domain_type': 'logic', 'data': {'axioms': ['A'], 'conclusion': 'A'}},
            {'domain_type': 'logic', 'data': {'axioms': ['B'], 'conclusion': 'B'}}
        ]
        
        agent.train(training_data, max_generations=10)
        
        assert len(agent.domain_history) == 1
        assert agent.domain_history[0] == 'logic'
        assert agent.evaluation_count > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])