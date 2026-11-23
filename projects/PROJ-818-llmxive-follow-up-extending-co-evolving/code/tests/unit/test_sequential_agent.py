"""
Unit tests for SequentialAgent.

These tests verify the sequential training behavior, domain switching,
and rule set evaluation logic.
"""
import pytest
import sys
import os
from typing import List, Dict, Any
from pathlib import Path
from src.agents.sequential_agent import SequentialAgent
from src.utils.config import Config


class TestSequentialAgent:
    """Test suite for SequentialAgent."""

    @pytest.fixture
    def config(self):
        """Create a default configuration for testing."""
        return Config({
            'seed': 42,
            'generation_count': 5,
            'domain_order': ['logic', 'grid'],
            'max_domain_iterations': 1
        })

    @pytest.fixture
    def agent(self, config):
        """Create a SequentialAgent instance."""
        return SequentialAgent(config)

    def test_initialization(self, agent):
        """Test that SequentialAgent initializes correctly."""
        assert agent.current_domain_index == 0
        assert agent.get_current_domain() == 'logic'
        assert len(agent.domain_instances) == 0
        assert agent.domain_iteration_counts == {'logic': 0, 'grid': 0}

    def test_load_domain_instances(self, agent):
        """Test loading instances for a domain."""
        logic_instances = [
            {'id': 'logic_1', 'domain': 'logic', 'instance_data': {'axioms': ['A'], 'target': 'B'}},
            {'id': 'logic_2', 'domain': 'logic', 'instance_data': {'axioms': ['C'], 'target': 'D'}}
        ]
        
        agent.load_domain_instances('logic', logic_instances)
        
        assert 'logic' in agent.domain_instances
        assert len(agent.domain_instances['logic']) == 2
        assert agent.domain_instances['logic'][0]['id'] == 'logic_1'

    def test_domain_advancement(self, agent):
        """Test advancing to the next domain."""
        assert agent.get_current_domain() == 'logic'
        
        agent.advance_domain()
        assert agent.get_current_domain() == 'grid'
        
        agent.advance_domain()
        assert agent.get_current_domain() is None
        assert agent.is_training_complete() is True

    def test_is_training_complete(self, agent):
        """Test training completion detection."""
        assert agent.is_training_complete() is False
        
        agent.advance_domain()
        agent.advance_domain()
        assert agent.is_training_complete() is True

    def test_evaluate_logic_rule_set(self, agent):
        """Test evaluation of logic rule sets."""
        rule_set = {
            'id': 'test_rule_set',
            'rules': ['A', 'B']
        }
        instance = {
            'domain': 'logic',
            'instance_data': {
                'axioms': ['A', 'B'],
                'target': 'C'
            }
        }
        
        is_valid, confidence = agent._evaluate_logic_rule_set(rule_set, instance['instance_data'])
        
        # Should have high confidence due to rule coverage
        assert confidence > 0.5
        assert is_valid is True

    def test_evaluate_grid_rule_set(self, agent):
        """Test evaluation of grid rule sets."""
        rule_set = {
            'id': 'test_rule_set',
            'rules': ['avoid_obstacles']
        }
        instance = {
            'domain': 'grid',
            'instance_data': {
                'grid': {
                    'rows': 5,
                    'cols': 5,
                    'start': (0, 0),
                    'goal': (4, 4),
                    'obstacles': []
                }
            }
        }
        
        is_valid, confidence = agent._evaluate_grid_rule_set(rule_set, instance['instance_data'])
        
        # Should be valid with a clear path
        assert is_valid is True
        assert confidence > 0.0

    def test_train_on_instance_logic(self, agent):
        """Test training on a logic instance."""
        agent.load_domain_instances('logic', [
            {'id': 'logic_1', 'domain': 'logic', 'instance_data': {'axioms': ['A'], 'target': 'B'}}
        ])
        
        instance = {'id': 'logic_1', 'domain': 'logic', 'instance_data': {'axioms': ['A'], 'target': 'B'}}
        result = agent.train_on_instance(instance)
        
        # Should successfully train
        assert result is True
        assert agent.evaluation_count > 0

    def test_train_on_instance_wrong_domain(self, agent):
        """Test that training skips instances from non-current domains."""
        agent.load_domain_instances('grid', [
            {'id': 'grid_1', 'domain': 'grid', 'instance_data': {'grid': {}}}
        ])
        
        instance = {'id': 'grid_1', 'domain': 'grid', 'instance_data': {'grid': {}}}
        result = agent.train_on_instance(instance)
        
        # Should skip because current domain is 'logic'
        assert result is False

    def test_run_training_epoch(self, agent, config):
        """Test running a training epoch."""
        # Load instances for current domain
        agent.load_domain_instances('logic', [
            {'id': f'logic_{i}', 'domain': 'logic', 'instance_data': {'axioms': ['A'], 'target': 'B'}}
            for i in range(5)
        ])
        
        all_instances = agent.domain_instances['logic']
        result = agent.run_training_epoch(all_instances)
        
        assert result['success'] is True
        assert result['domain'] == 'logic'
        assert result['instances_processed'] == 5
        assert 'accuracy' in result
        assert 'average_confidence' in result

    def test_state_serialization(self, agent):
        """Test saving and restoring agent state."""
        # Train a bit to change state
        agent.load_domain_instances('logic', [
            {'id': 'logic_1', 'domain': 'logic', 'instance_data': {'axioms': ['A'], 'target': 'B'}}
        ])
        agent.train_on_instance({'id': 'logic_1', 'domain': 'logic', 'instance_data': {'axioms': ['A'], 'target': 'B'}})
        
        state = agent.get_state()
        
        # Create new agent and restore state
        new_agent = SequentialAgent(agent.config)
        new_agent.set_state(state)
        
        assert new_agent.generation_count == agent.generation_count
        assert new_agent.evaluation_count == agent.evaluation_count
        assert new_agent.current_domain_index == agent.current_domain_index

    def test_multiple_domain_training(self, agent):
        """Test training across multiple domains."""
        agent.load_domain_instances('logic', [
            {'id': 'logic_1', 'domain': 'logic', 'instance_data': {'axioms': ['A'], 'target': 'B'}}
        ])
        agent.load_domain_instances('grid', [
            {'id': 'grid_1', 'domain': 'grid', 'instance_data': {'grid': {'rows': 3, 'cols': 3, 'start': (0, 0), 'goal': (2, 2), 'obstacles': []}}}
        ])
        
        all_instances = []
        for domain, instances in agent.domain_instances.items():
            all_instances.extend(instances)
        
        # Run epoch for logic domain
        result1 = agent.run_training_epoch(all_instances)
        assert result1['domain'] == 'logic'
        
        # Advance domain
        agent.advance_domain()
        
        # Run epoch for grid domain
        result2 = agent.run_training_epoch(all_instances)
        assert result2['domain'] == 'grid'

    def test_empty_domain_training(self, agent):
        """Test training with no instances for current domain."""
        # Don't load any instances
        result = agent.run_training_epoch([])
        
        assert result['success'] is True
        assert result['message'] == 'No instances for current domain'
        assert result['domain'] == 'logic'

    def test_rule_set_refinement(self, agent):
        """Test that rule sets are refined after successful training."""
        rule_set = {
            'id': 'test',
            'rules': ['initial_rule']
        }
        agent.current_rule_sets = [rule_set]
        
        instance = {
            'domain': 'logic',
            'instance_data': {
                'axioms': ['new_axiom'],
                'target': 'result'
            }
        }
        
        agent._refine_rule_set(rule_set, instance)
        
        # Rule set should be updated with new patterns
        assert 'new_axiom' in rule_set['rules'] or len(rule_set['rules']) > 1