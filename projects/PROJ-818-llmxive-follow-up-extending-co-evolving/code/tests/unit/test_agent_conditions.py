"""
Unit tests for the bidirectional exchange logic in CoevolvingAgent.

This module verifies that:
1. The CoevolvingAgent correctly manages sub-populations.
2. Bidirectional exchange of rule-sets occurs between sub-populations.
3. The exchange logic maintains population integrity and does not lose data.
4. The exchange is truly bidirectional (both populations receive rules).
"""

import pytest
import sys
import os
from typing import List, Dict, Any, Set, Tuple
from pathlib import Path
from src.agents.coevolving_agent import CoevolvingAgent
from src.utils.config import Config, get_default_config

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class MockRuleSet:
    """
    A simplified mock rule set for testing purposes.
    In real usage, this would be a sympy expression or similar.
    """
    def __init__(self, rule_id: str, domain: str, complexity: int = 1):
        self.rule_id = rule_id
        self.domain = domain
        self.complexity = complexity
        self.performance_score = 0.5  # Default neutral score

    def __eq__(self, other):
        if not isinstance(other, MockRuleSet):
            return False
        return self.rule_id == other.rule_id and self.domain == other.domain

    def __hash__(self):
        return hash((self.rule_id, self.domain))

    def __repr__(self):
        return f"MockRuleSet(id={self.rule_id}, domain={self.domain}, score={self.performance_score})"


class TestBidirectionalExchange:
    """
    Unit tests for the bidirectional exchange logic in CoevolvingAgent.
    """

    @pytest.fixture
    def mock_config(self):
        """Create a minimal config for testing."""
        config = get_default_config()
        config["coevolving"] = {
            "num_subpopulations": 2,
            "exchange_rate": 0.3,
            "exchange_interval": 1,  # Exchange every generation
            "selection_pressure": 0.1
        }
        config["generation"] = {
            "num_proofs": 10,
            "num_grids": 10
        }
        config["seeds"] = {
            "base_seed": 42
        }
        return config

    @pytest.fixture
    def coevolving_agent(self, mock_config):
        """Create a CoevolvingAgent with mock configuration."""
        # We need to mock the data loading since we're testing exchange logic
        # The agent should be initialized with two sub-populations
        agent = CoevolvingAgent(mock_config)
        return agent

    def test_initialization_creates_subpopulations(self, coevolving_agent):
        """Test that initialization creates the correct number of sub-populations."""
        assert hasattr(coevolving_agent, 'sub_populations')
        assert len(coevolving_agent.sub_populations) == 2
        assert all(isinstance(pop, list) for pop in coevolving_agent.sub_populations.values())

    def test_exchange_logic_is_bidirectional(self, coevolving_agent):
        """
        Test that the exchange logic is truly bidirectional.
        Rules should flow from population A to B AND from B to A.
        """
        # Initialize with distinct rule sets for each population
        # Population 0: Rules with IDs starting with "A"
        # Population 1: Rules with IDs starting with "B"
        coevolving_agent.sub_populations[0] = [
            MockRuleSet(f"A_{i}", "logic", i) for i in range(5)
        ]
        coevolving_agent.sub_populations[1] = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(5)
        ]

        # Store initial state
        initial_pop0_ids = {r.rule_id for r in coevolving_agent.sub_populations[0]}
        initial_pop1_ids = {r.rule_id for r in coevolving_agent.sub_populations[1]}

        # Perform exchange
        coevolving_agent._perform_bidirectional_exchange()

        # Check that both populations now contain rules from the other
        final_pop0_ids = {r.rule_id for r in coevolving_agent.sub_populations[0]}
        final_pop1_ids = {r.rule_id for r in coevolving_agent.sub_populations[1]}

        # Population 0 should have received some rules from Population 1
        received_from_1 = final_pop0_ids - initial_pop0_ids
        assert len(received_from_1) > 0, "Population 0 did not receive any rules from Population 1"

        # Population 1 should have received some rules from Population 0
        received_from_0 = final_pop1_ids - initial_pop1_ids
        assert len(received_from_0) > 0, "Population 1 did not receive any rules from Population 0"

    def test_exchange_respects_exchange_rate(self, coevolving_agent):
        """
        Test that the number of exchanged rules respects the configured exchange rate.
        """
        num_rules_per_pop = 10
        exchange_rate = 0.3  # 30% exchange

        # Initialize populations
        coevolving_agent.sub_populations[0] = [
            MockRuleSet(f"A_{i}", "logic", i) for i in range(num_rules_per_pop)
        ]
        coevolving_agent.sub_populations[1] = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(num_rules_per_pop)
        ]

        # Perform exchange
        coevolving_agent._perform_bidirectional_exchange()

        # Calculate expected number of exchanged rules
        expected_min_exchanged = int(num_rules_per_pop * exchange_rate * 0.8)  # Allow some variance
        expected_max_exchanged = int(num_rules_per_pop * exchange_rate * 1.2)

        # Count how many rules from pop1 are now in pop0
        pop0_rule_ids = {r.rule_id for r in coevolving_agent.sub_populations[0]}
        exchanged_count = sum(1 for rule_id in pop0_rule_ids if rule_id.startswith("B_"))

        # The exchange should be within reasonable bounds of the expected rate
        assert expected_min_exchanged <= exchanged_count <= expected_max_exchanged, \
            f"Exchange count {exchanged_count} outside expected range [{expected_min_exchanged}, {expected_max_exchanged}]"

    def test_no_data_loss_during_exchange(self, coevolving_agent):
        """
        Test that no rules are lost during the exchange process.
        The total number of rules across both populations should remain constant.
        """
        # Initialize with distinct rule sets
        coevolving_agent.sub_populations[0] = [
            MockRuleSet(f"A_{i}", "logic", i) for i in range(5)
        ]
        coevolving_agent.sub_populations[1] = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(5)
        ]

        initial_total = (
            len(coevolving_agent.sub_populations[0]) +
            len(coevolving_agent.sub_populations[1])
        )

        # Perform exchange
        coevolving_agent._perform_bidirectional_exchange()

        final_total = (
            len(coevolving_agent.sub_populations[0]) +
            len(coevolving_agent.sub_populations[1])
        )

        assert initial_total == final_total, \
            f"Rule count changed from {initial_total} to {final_total} during exchange"

    def test_exchange_maintains_population_size_constraints(self, coevolving_agent):
        """
        Test that the exchange maintains population sizes within reasonable bounds.
        Neither population should become empty or excessively large.
        """
        # Initialize with equal populations
        coevolving_agent.sub_populations[0] = [
            MockRuleSet(f"A_{i}", "logic", i) for i in range(10)
        ]
        coevolving_agent.sub_populations[1] = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(10)
        ]

        # Perform multiple exchanges
        for _ in range(5):
            coevolving_agent._perform_bidirectional_exchange()

        # Check that both populations still have rules
        assert len(coevolving_agent.sub_populations[0]) > 0, "Population 0 became empty"
        assert len(coevolving_agent.sub_populations[1]) > 0, "Population 1 became empty"

        # Check that neither population is excessively large (should be roughly equal)
        pop0_size = len(coevolving_agent.sub_populations[0])
        pop1_size = len(coevolving_agent.sub_populations[1])
        total_size = pop0_size + pop1_size

        # Each population should be between 20% and 80% of total
        assert 0.2 * total_size <= pop0_size <= 0.8 * total_size, \
            f"Population 0 size {pop0_size} out of bounds [20%, 80%] of total {total_size}"
        assert 0.2 * total_size <= pop1_size <= 0.8 * total_size, \
            f"Population 1 size {pop1_size} out of bounds [20%, 80%] of total {total_size}"

    def test_exchange_selects_rules_based_on_performance(self, coevolving_agent, mock_config):
        """
        Test that the exchange logic considers rule performance when selecting rules.
        Better performing rules should be more likely to be exchanged.
        """
        # Create rules with varying performance scores
        # Population 0: High performance rules
        coevolving_agent.sub_populations[0] = [
            MockRuleSet(f"A_{i}", "logic", i) for i in range(5)
        ]
        for rule in coevolving_agent.sub_populations[0]:
            rule.performance_score = 0.9  # High score

        # Population 1: Low performance rules
        coevolving_agent.sub_populations[1] = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(5)
        ]
        for rule in coevolving_agent.sub_populations[1]:
            rule.performance_score = 0.1  # Low score

        # Perform exchange
        coevolving_agent._perform_bidirectional_exchange()

        # Check that high-performing rules from pop0 made it to pop1
        pop1_rule_ids = {r.rule_id for r in coevolving_agent.sub_populations[1]}
        received_high_perf = any(rule_id.startswith("A_") for rule_id in pop1_rule_ids)

        assert received_high_perf, "High-performing rules from Population 0 were not exchanged to Population 1"

    def test_exchange_with_single_rule_population(self, coevolving_agent):
        """
        Test exchange behavior when one population has only one rule.
        Should still work without errors.
        """
        coevolving_agent.sub_populations[0] = [MockRuleSet("A_0", "logic")]
        coevolving_agent.sub_populations[1] = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(5)
        ]

        # Should not raise an exception
        coevolving_agent._perform_bidirectional_exchange()

        # Both populations should still have rules
        assert len(coevolving_agent.sub_populations[0]) > 0
        assert len(coevolving_agent.sub_populations[1]) > 0

    def test_exchange_with_empty_population_raises_error(self, coevolving_agent):
        """
        Test that exchange fails gracefully when a population is empty.
        This should raise a ValueError or similar.
        """
        coevolving_agent.sub_populations[0] = []
        coevolving_agent.sub_populations[1] = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(5)
        ]

        with pytest.raises(ValueError):
            coevolving_agent._perform_bidirectional_exchange()

    def test_exchange_preserves_rule_identity(self, coevolving_agent):
        """
        Test that rules maintain their identity (rule_id, domain) after exchange.
        Rules should not be modified during the exchange process.
        """
        # Create rules with specific attributes
        original_rules_pop0 = [
            MockRuleSet(f"A_{i}", "logic", i) for i in range(5)
        ]
        original_rules_pop1 = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(5)
        ]

        coevolving_agent.sub_populations[0] = original_rules_pop0
        coevolving_agent.sub_populations[1] = original_rules_pop1

        # Perform exchange
        coevolving_agent._perform_bidirectional_exchange()

        # Check that all rules in both populations have valid identities
        for rule in coevolving_agent.sub_populations[0]:
            assert hasattr(rule, 'rule_id')
            assert hasattr(rule, 'domain')
            assert isinstance(rule.rule_id, str)
            assert isinstance(rule.domain, str)

        for rule in coevolving_agent.sub_populations[1]:
            assert hasattr(rule, 'rule_id')
            assert hasattr(rule, 'domain')
            assert isinstance(rule.rule_id, str)
            assert isinstance(rule.domain, str)

    def test_exchange_is_deterministic_with_seed(self, mock_config):
        """
        Test that exchange is deterministic when using the same seed.
        Running exchange twice with the same seed should produce identical results.
        """
        # Set a fixed seed in config
        mock_config["seeds"]["base_seed"] = 12345

        # Create two agents with the same config
        agent1 = CoevolvingAgent(mock_config)
        agent2 = CoevolvingAgent(mock_config)

        # Initialize with identical populations
        agent1.sub_populations[0] = [MockRuleSet(f"A_{i}", "logic", i) for i in range(5)]
        agent1.sub_populations[1] = [MockRuleSet(f"B_{i}", "grid", i) for i in range(5)]
        agent2.sub_populations[0] = [MockRuleSet(f"A_{i}", "logic", i) for i in range(5)]
        agent2.sub_populations[1] = [MockRuleSet(f"B_{i}", "grid", i) for i in range(5)]

        # Perform exchange on both
        agent1._perform_bidirectional_exchange()
        agent2._perform_bidirectional_exchange()

        # Compare results
        pop0_ids_1 = {r.rule_id for r in agent1.sub_populations[0]}
        pop0_ids_2 = {r.rule_id for r in agent2.sub_populations[0]}
        pop1_ids_1 = {r.rule_id for r in agent1.sub_populations[1]}
        pop1_ids_2 = {r.rule_id for r in agent2.sub_populations[1]}

        assert pop0_ids_1 == pop0_ids_2, "Population 0 exchange results differ between runs"
        assert pop1_ids_1 == pop1_ids_2, "Population 1 exchange results differ between runs"

    def test_exchange_integration_with_agent_lifecycle(self, coevolving_agent):
        """
        Test that exchange integrates properly with the agent's lifecycle.
        Exchange should be callable multiple times as part of the training loop.
        """
        # Initialize populations
        coevolving_agent.sub_populations[0] = [
            MockRuleSet(f"A_{i}", "logic", i) for i in range(5)
        ]
        coevolving_agent.sub_populations[1] = [
            MockRuleSet(f"B_{i}", "grid", i) for i in range(5)
        ]

        # Simulate multiple generations with exchange
        for generation in range(3):
            # In a real scenario, there would be evolution here
            # For this test, we just check that exchange works repeatedly
            coevolving_agent._perform_bidirectional_exchange()

            # Verify populations are still valid
            assert len(coevolving_agent.sub_populations[0]) > 0
            assert len(coevolving_agent.sub_populations[1]) > 0

        # Final check: both populations should have rules from both domains
        pop0_rule_ids = {r.rule_id for r in coevolving_agent.sub_populations[0]}
        pop1_rule_ids = {r.rule_id for r in coevolving_agent.sub_populations[1]}

        has_a_in_pop0 = any(rule_id.startswith("A_") for rule_id in pop0_rule_ids)
        has_b_in_pop0 = any(rule_id.startswith("B_") for rule_id in pop0_rule_ids)
        has_a_in_pop1 = any(rule_id.startswith("A_") for rule_id in pop1_rule_ids)
        has_b_in_pop1 = any(rule_id.startswith("B_") for rule_id in pop1_rule_ids)

        assert has_a_in_pop0 and has_b_in_pop0, "Population 0 should have rules from both domains"
        assert has_a_in_pop1 and has_b_in_pop1, "Population 1 should have rules from both domains"