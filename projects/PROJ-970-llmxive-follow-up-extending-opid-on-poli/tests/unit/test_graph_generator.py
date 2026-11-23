import pytest
import os
import sys
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from environment.graph_generator import GraphGenerator
from config import set_seed, get_seed

class TestGraphGenerator:
    """
    Independent tests for GraphGenerator tier methods.
    """

    @pytest.fixture
    def generator(self):
        """Create a GraphGenerator instance with a fixed seed."""
        set_seed(42)
        return GraphGenerator()

    def test_tier_1_nodes(self, generator):
        """
        Test that Tier 1 generates a graph with 5 to 10 nodes.
        """
        graph = generator.generate_tier_1()
        
        assert graph.tier == 1
        assert 5 <= len(graph.nodes) <= 10, f"Tier 1 should have 5-10 nodes, got {len(graph.nodes)}"
        
        # Verify path exists (is_valid checks this)
        assert graph.is_valid(), "Tier 1 graph must be valid (path exists)"
        
        # Verify deterministic nature (single path, no branching)
        # In Tier 1, each node (except goal) should have exactly one outgoing edge
        for node in graph.nodes[:-1]:  # Exclude goal
            outgoing_edges = [e for e in graph.edges if e.source == node.id]
            assert len(outgoing_edges) == 1, f"Tier 1 node {node.id} should have exactly 1 outgoing edge"

    def test_tier_2_branching(self, generator):
        """
        Test that Tier 2 generates a graph with 20 to 50 nodes and branching paths.
        """
        graph = generator.generate_tier_2()
        
        assert graph.tier == 2
        assert 20 <= len(graph.nodes) <= 50, f"Tier 2 should have 20-50 nodes, got {len(graph.nodes)}"
        
        # Verify path exists
        assert graph.is_valid(), "Tier 2 graph must be valid (path exists)"
        
        # Verify branching: at least one node should have >1 outgoing edge
        has_branching = False
        for node in graph.nodes:
            outgoing_edges = [e for e in graph.edges if e.source == node.id]
            if len(outgoing_edges) > 1:
                has_branching = True
                break
        
        assert has_branching, "Tier 2 graph must have branching paths"
        
        # Verify stochastic transitions (probability < 1.0)
        has_stochastic = False
        for edge in graph.edges:
            if edge.probability < 1.0:
                has_stochastic = True
                break
        assert has_stochastic, "Tier 2 graph must have stochastic transitions"

    def test_tier_3_sparsity(self, generator):
        """
        Test that Tier 3 generates a graph with multiple nodes and sparse rewards.
        """
        graph = generator.generate_tier_3()
        
        assert graph.tier == 3
        assert len(graph.nodes) >= 50, f"Tier 3 should have at least 50 nodes, got {len(graph.nodes)}"
        
        # Verify path exists
        assert graph.is_valid(), "Tier 3 graph must be valid (path exists)"
        
        # Verify sparse rewards: count nodes with reward edges
        reward_edges = [e for e in graph.edges if e.reward > 0]
        # Should have approximately one reward per 10 nodes
        expected_min_rewards = max(1, len(graph.nodes) // 10)
        # Allow some variance, but should be in the ballpark
        assert len(reward_edges) >= expected_min_rewards * 0.5, \
            f"Tier 3 should have sparse rewards (~1 per 10 nodes), got {len(reward_edges)} for {len(graph.nodes)} nodes"
        
        # Verify high-entropy transitions (lower probabilities)
        avg_probability = np.mean([e.probability for e in graph.edges])
        # Tier 3 should have lower average probability than Tier 1 or 2
        assert avg_probability < 0.9, f"Tier 3 should have high-entropy transitions, avg prob: {avg_probability}"

    def test_tier_2_retry_logic(self):
        """
        Test that Tier 2 generation includes retry logic.
        This is implicitly tested by ensuring it doesn't hang or fail on normal runs,
        but we can't easily test the retry loop without mocking is_valid.
        However, the implementation ensures max_retries=100.
        """
        set_seed(42)
        gen = GraphGenerator()
        # This should complete without raising RuntimeError under normal circumstances
        graph = gen.generate_tier_2()
        assert graph is not None
        assert graph.is_valid()

    def test_deterministic_regeneration_tier_2(self):
        """
        Test that generating Tier 2 with the same seed produces the same graph.
        """
        seed = 12345
        
        set_seed(seed)
        gen1 = GraphGenerator()
        graph1 = gen1.generate_tier_2()
        
        set_seed(seed)
        gen2 = GraphGenerator()
        graph2 = gen2.generate_tier_2()
        
        # Compare node counts and edge counts
        assert len(graph1.nodes) == len(graph2.nodes), "Same seed should produce same number of nodes"
        assert len(graph1.edges) == len(graph2.edges), "Same seed should produce same number of edges"
        
        # Compare node IDs (order should be deterministic)
        node_ids_1 = [n.id for n in graph1.nodes]
        node_ids_2 = [n.id for n in graph2.nodes]
        assert node_ids_1 == node_ids_2, "Same seed should produce same node IDs in same order"
        
        # Compare edge properties
        edges_1 = sorted([(e.source, e.target, e.probability, e.reward) for e in graph1.edges])
        edges_2 = sorted([(e.source, e.target, e.probability, e.reward) for e in graph2.edges])
        assert edges_1 == edges_2, "Same seed should produce identical edges"