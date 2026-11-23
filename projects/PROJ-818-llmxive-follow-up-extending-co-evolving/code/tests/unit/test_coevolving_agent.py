import pytest
import sys
import os
from typing import List, Dict, Any, Set, Tuple
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.agents.coevolving_agent import CoevolvingAgent
from src.utils.config import Config

class MockRuleSet:
    """Mock rule set for testing."""
    def __init__(self, name: str, domain: str):
        self.name = name
        self.domain = domain
        self.score = 0.5  # Default score
        
    def __str__(self):
        return f"MockRuleSet({self.name}, {self.domain})"

class TestBidirectionalExchange:
    """Unit tests for bidirectional exchange logic in CoevolvingAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config({
            "exchange_probability": 1.0,  # Ensure exchange happens
            "selection_pressure_threshold": 0.0,
            "seed": 42
        })
        self.domains = ["domain_A", "domain_B", "domain_C"]
        self.agent = CoevolvingAgent(self.config, self.domains)
        
        # Initialize with distinct rule sets
        initial_rule_sets = {
            "domain_A": [MockRuleSet(f"A{i}", "domain_A") for i in range(3)],
            "domain_B": [MockRuleSet(f"B{i}", "domain_B") for i in range(3)],
            "domain_C": [MockRuleSet(f"C{i}", "domain_C") for i in range(3)]
        }
        self.agent.initialize_population(initial_rule_sets)

    def test_initial_population_separation(self):
        """Verify initial populations are distinct and separated by domain."""
        pops = self.agent.get_rule_sets()
        
        assert len(pops["domain_A"]) == 3
        assert len(pops["domain_B"]) == 3
        assert len(pops["domain_C"]) == 3
        
        # Verify no cross-contamination initially
        for rule in pops["domain_A"]:
            assert rule.domain == "domain_A"
        for rule in pops["domain_B"]:
            assert rule.domain == "domain_B"
        for rule in pops["domain_C"]:
            assert rule.domain == "domain_C"

    def test_bidirectional_exchange_occurs(self):
        """Verify that bidirectional exchange modifies populations."""
        initial_pops = {d: len(p) for d, p in self.agent.sub_populations.items()}
        
        # Run a training step which triggers exchange
        training_data = {d: [{"id": "x"}] for d in self.domains}
        test_instances = {d: [{"id": "test"}] for d in self.domains}
        
        self.agent.train_step(0, training_data, test_instances)
        
        final_pops = self.agent.get_rule_sets()
        
        # Populations should have changed due to exchange
        # (Exact counts depend on exchange logic, but content should differ)
        assert final_pops["domain_A"] != self.agent.sub_populations["domain_A"] or \
               final_pops["domain_B"] != self.agent.sub_populations["domain_B"]

    def test_exchange_maintains_population_size(self):
        """Verify that exchange does not drastically alter population sizes."""
        training_data = {d: [{"id": "x"}] for d in self.domains}
        test_instances = {d: [{"id": "test"}] for d in self.domains}
        
        # Run multiple steps
        for gen in range(5):
            self.agent.train_step(gen, training_data, test_instances)
        
        final_pops = self.agent.get_rule_sets()
        
        # Each population should still have some members
        for domain in self.domains:
            assert len(final_pops[domain]) > 0, f"Population for {domain} collapsed"

    def test_single_domain_no_exchange(self):
        """Verify no exchange occurs with only one domain."""
        single_domain_agent = CoevolvingAgent(self.config, ["single_domain"])
        single_domain_agent.initialize_population({
            "single_domain": [MockRuleSet("R1", "single_domain")]
        })
        
        initial_pop = list(single_domain_agent.sub_populations["single_domain"])
        
        training_data = {"single_domain": [{"id": "x"}]}
        test_instances = {"single_domain": [{"id": "test"}]}
        
        single_domain_agent.train_step(0, training_data, test_instances)
        
        # Population should remain unchanged (no exchange possible)
        assert single_domain_agent.sub_populations["single_domain"] == initial_pop

    def test_selection_pressure_discards_low_performers(self):
        """Verify selection pressure removes low-performing rule sets."""
        # Create agent with low threshold to trigger removal
        config = Config({
            "exchange_probability": 0.0,  # Disable exchange to isolate selection
            "selection_pressure_threshold": 0.9,  # High threshold
            "seed": 42
        })
        agent = CoevolvingAgent(config, ["test_domain"])
        
        # Initialize with rule sets
        agent.initialize_population({
            "test_domain": [MockRuleSet(f"R{i}", "test_domain") for i in range(5)]
        })
        
        # Mock evaluation to return low scores for some, high for others
        original_eval = agent._evaluate_rule_set
        
        def mock_eval(rule_set, domain, instances):
            # Return low score for first 3, high for last 2
            if "R0" in rule_set.name or "R1" in rule_set.name or "R2" in rule_set.name:
                return 0.1
            return 0.95
        
        with patch.object(agent, '_evaluate_rule_set', side_effect=mock_eval):
            training_data = {"test_domain": [{"id": "x"}]}
            test_instances = {"test_domain": [{"id": "test"}]}
            
            agent.train_step(0, training_data, test_instances)
        
        final_pop = agent.get_rule_sets()["test_domain"]
        
        # Should have discarded low performers
        assert len(final_pop) < 5
        # Remaining should be the high performers
        for rule in final_pop:
            assert "R3" in rule.name or "R4" in rule.name

    def test_state_serialization(self):
        """Verify agent state can be serialized and deserialized."""
        training_data = {d: [{"id": "x"}] for d in self.domains}
        test_instances = {d: [{"id": "test"}] for d in self.domains}
        
        self.agent.train_step(0, training_data, test_instances)
        
        state = self.agent.get_state()
        
        assert state["type"] == "CoevolvingAgent"
        assert state["domains"] == self.domains
        assert "sub_populations" in state
        assert "domain_eval_counts" in state
        assert "total_evaluations" in state
        assert state["generation"] == 1  # One step executed

if __name__ == "__main__":
    pytest.main([__file__, "-v"])