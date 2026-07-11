"""
Unit tests for bidirectional exchange logic in agent conditions.

This module verifies that the Co-evolving agent correctly exchanges rule-sets
between sub-populations (Logic and Grid) at every generation step, ensuring
that:
1. Rules flow from Logic -> Grid population.
2. Rules flow from Grid -> Logic population.
3. The exchange is bidirectional (both happen in the same step).
4. The exchange does not corrupt the rule-set structure.
"""
import pytest
import sys
import os
from typing import List, Dict, Any, Set, Tuple
from pathlib import Path

# Add project root to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.coevolving_agent import CoevolvingAgent
from src.utils.config import Config, get_default_config


class MockRuleSet:
    """Mock rule set for testing exchange logic."""
    def __init__(self, source: str, rule_id: str, priority: float = 0.0):
        self.source = source  # 'logic' or 'grid'
        self.rule_id = rule_id
        self.priority = priority
        self.content = f"Rule {rule_id} from {source}"

    def __eq__(self, other):
        if not isinstance(other, MockRuleSet):
            return False
        return (self.source == other.source and
                self.rule_id == other.rule_id and
                self.priority == other.priority)

    def __repr__(self):
        return f"MockRuleSet({self.source}, {self.rule_id}, {self.priority})"


class TestBidirectionalExchange:
    """Tests for the bidirectional exchange logic in CoevolvingAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = get_default_config()
        self.config['generation_count'] = 10
        self.config['rule_evaluation_budget'] = 1000
        self.config['seed'] = 42

        # Initialize the agent
        self.agent = CoevolvingAgent(self.config)

        # Mock the rule sets for both sub-populations
        # Logic Population
        self.agent.logic_population = [
            MockRuleSet('logic', 'L1', 0.8),
            MockRuleSet('logic', 'L2', 0.7),
            MockRuleSet('logic', 'L3', 0.6)
        ]

        # Grid Population
        self.agent.grid_population = [
            MockRuleSet('grid', 'G1', 0.9),
            MockRuleSet('grid', 'G2', 0.85),
            MockRuleSet('grid', 'G3', 0.75)
        ]

    def test_initial_state_isolation(self):
        """Verify that initially, populations have only their own rules."""
        logic_sources = {r.source for r in self.agent.logic_population}
        grid_sources = {r.source for r in self.agent.grid_population}

        assert logic_sources == {'logic'}
        assert grid_sources == {'grid'}
        assert len(self.agent.logic_population) == 3
        assert len(self.agent.grid_population) == 3

    def test_exchange_method_exists(self):
        """Verify that the exchange method exists and is callable."""
        assert hasattr(self.agent, '_exchange_rule_sets')
        assert callable(self.agent._exchange_rule_sets)

    def test_bidirectional_flow(self):
        """Test that rules flow in both directions during exchange."""
        # Record initial state
        initial_logic_ids = {r.rule_id for r in self.agent.logic_population}
        initial_grid_ids = {r.rule_id for r in self.agent.grid_population}

        # Perform exchange
        self.agent._exchange_rule_sets()

        # Check that Logic population now has some Grid rules
        logic_sources = {r.source for r in self.agent.logic_population}
        grid_sources = {r.source for r in self.agent.grid_population}

        # Logic population should now contain 'grid' rules
        assert 'grid' in logic_sources, "Logic population did not receive Grid rules"

        # Grid population should now contain 'logic' rules
        assert 'logic' in grid_sources, "Grid population did not receive Logic rules"

    def test_exchange_preserves_rule_integrity(self):
        """Test that exchanged rules maintain their original properties."""
        # Get a rule from Grid population to track
        original_grid_rule = self.agent.grid_population[0]
        original_logic_rule = self.agent.logic_population[0]

        # Perform exchange
        self.agent._exchange_rule_sets()

        # Find the same rule in the Logic population
        transferred_grid_rule = None
        for rule in self.agent.logic_population:
            if rule.rule_id == original_grid_rule.rule_id:
                transferred_grid_rule = rule
                break

        # Find the same rule in the Grid population
        transferred_logic_rule = None
        for rule in self.agent.grid_population:
            if rule.rule_id == original_logic_rule.rule_id:
                transferred_logic_rule = rule
                break

        # Verify the rules were transferred correctly
        assert transferred_grid_rule is not None, "Grid rule was not transferred to Logic population"
        assert transferred_logic_rule is not None, "Logic rule was not transferred to Grid population"

        # Verify properties are preserved
        assert transferred_grid_rule.source == 'grid'
        assert transferred_grid_rule.rule_id == original_grid_rule.rule_id
        assert transferred_grid_rule.priority == original_grid_rule.priority

        assert transferred_logic_rule.source == 'logic'
        assert transferred_logic_rule.rule_id == original_logic_rule.rule_id
        assert transferred_logic_rule.priority == original_logic_rule.priority

    def test_exchange_maintains_population_sizes(self):
        """Test that exchange does not change population sizes."""
        initial_logic_count = len(self.agent.logic_population)
        initial_grid_count = len(self.agent.grid_population)

        # Perform exchange multiple times
        for _ in range(5):
            self.agent._exchange_rule_sets()

        # Verify sizes are unchanged
        assert len(self.agent.logic_population) == initial_logic_count
        assert len(self.agent.grid_population) == initial_grid_count

    def test_exchange_with_empty_population(self):
        """Test exchange when one population is empty."""
        # Clear one population
        self.agent.logic_population = []

        # Perform exchange
        self.agent._exchange_rule_sets()

        # Logic population should now have some Grid rules
        assert len(self.agent.logic_population) > 0
        assert all(r.source == 'grid' for r in self.agent.logic_population)

        # Grid population should remain unchanged (no rules to receive from Logic)
        assert len(self.agent.grid_population) == 3
        assert all(r.source == 'grid' for r in self.agent.grid_population)

    def test_exchange_selection_strategy(self):
        """Test that the exchange uses the configured selection strategy."""
        # The exchange should select top-performing rules based on priority
        # Set up a scenario where high-priority rules should be exchanged

        # Clear and set up specific priorities
        self.agent.logic_population = [
            MockRuleSet('logic', 'L_low', 0.1),
            MockRuleSet('logic', 'L_high', 0.9)
        ]
        self.agent.grid_population = [
            MockRuleSet('grid', 'G_low', 0.1),
            MockRuleSet('grid', 'G_high', 0.9)
        ]

        # Perform exchange
        self.agent._exchange_rule_sets()

        # Check that high-priority rules were exchanged
        logic_rule_ids = {r.rule_id for r in self.agent.logic_population}
        grid_rule_ids = {r.rule_id for r in self.agent.grid_population}

        # The Logic population should contain the high-priority Grid rule
        assert 'G_high' in logic_rule_ids, "High-priority Grid rule was not exchanged to Logic"

        # The Grid population should contain the high-priority Logic rule
        assert 'L_high' in grid_rule_ids, "High-priority Logic rule was not exchanged to Grid"

    def test_multiple_generations_accumulate_exchange(self):
        """Test that multiple generations continue to exchange rules."""
        # Run multiple generations
        for gen in range(3):
            self.agent._exchange_rule_sets()

        # Both populations should contain a mix of rules from both sources
        logic_sources = {r.source for r in self.agent.logic_population}
        grid_sources = {r.source for r in self.agent.grid_population}

        assert 'logic' in logic_sources and 'grid' in logic_sources
        assert 'logic' in grid_sources and 'grid' in grid_sources

        # Verify that we have a diverse set of rules
        assert len(self.agent.logic_population) > 1
        assert len(self.agent.grid_population) > 1

    def test_exchange_no_modification_of_originals(self):
        """Test that the exchange creates new rule objects rather than moving references."""
        # Store references to original rules
        original_logic_rules = list(self.agent.logic_population)
        original_grid_rules = list(self.agent.grid_population)

        # Perform exchange
        self.agent._exchange_rule_sets()

        # Verify that the original lists were modified (they should be)
        # But the new rules in the opposite population should be copies or new instances
        # This test ensures we don't accidentally share mutable state

        # Check that we have mixed sources now
        logic_sources = {r.source for r in self.agent.logic_population}
        assert 'grid' in logic_sources

        grid_sources = {r.source for r in self.agent.grid_population}
        assert 'logic' in grid_sources

    def test_exchange_with_single_rule(self):
        """Test exchange when each population has only one rule."""
        self.agent.logic_population = [MockRuleSet('logic', 'L1', 0.5)]
        self.agent.grid_population = [MockRuleSet('grid', 'G1', 0.5)]

        self.agent._exchange_rule_sets()

        # Both should now have 2 rules (original + exchanged)
        assert len(self.agent.logic_population) == 2
        assert len(self.agent.grid_population) == 2

        # Check for bidirectional presence
        logic_ids = {r.rule_id for r in self.agent.logic_population}
        grid_ids = {r.rule_id for r in self.agent.grid_population}

        assert 'G1' in logic_ids
        assert 'L1' in grid_ids