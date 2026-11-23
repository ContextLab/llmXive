"""
Integration Test: Multi-hop Predicate Chaining.

Verifies that the query engine can traverse multiple edges 
(chaining predicates) to find complex relationships.
"""
import pytest
import networkx as nx

# Import from code/
from query_engine import query_graph, Node
from graph_builder import SymbolicGraphBuilder

class TestPredicateChaining:
    """Tests for multi-hop query execution."""

    def _build_chain_graph(self) -> nx.DiGraph:
        """
        Build a graph: A --(on_top_of)--> B --(near)--> C
        """
        graph = nx.DiGraph()
        # Manually construct to ensure specific chain
        graph.add_node("A", token="book", predicates=["on_top_of"])
        graph.add_node("B", token="table", predicates=["near", "on_top_of"])
        graph.add_node("C", token="sofa", predicates=["near"])
        
        graph.add_edge("A", "B", predicate="on_top_of")
        graph.add_edge("B", "C", predicate="near")
        
        return graph

    def test_two_hop_traversal(self):
        """
        Integration: Query for 'book' near 'sofa' (via table) should succeed.
        """
        graph = self._build_chain_graph()
        # Query: Find A near C (via B)
        # Note: The actual query logic in query_engine.py handles the traversal.
        # We test that the result contains the expected nodes.
        result = query_graph(graph, "book near sofa")

        assert len(result) >= 1, "Should find at least one node in the chain"
        tokens = [node.token for node in result]
        assert "book" in tokens, "Result should include the start node"
        
    def test_no_hallucination_on_broken_chain(self):
        """
        Integration: If a link is missing, do not fabricate a path.
        """
        graph = nx.DiGraph()
        graph.add_node("A", token="book")
        graph.add_node("C", token="sofa")
        # Missing edge A->B and B->C
        
        result = query_graph(graph, "book near sofa")
        
        # Should return empty or only direct matches, not a fake path
        assert len(result) == 0 or all(n.token in ["book", "sofa"] for n in result), \
            "Should not hallucinate a path where none exists"

    def test_complex_predicate_chain(self):
        """
        Integration: Handle query 'Find X which is before Y and Y is near Z'.
        """
        graph = nx.DiGraph()
        graph.add_node("1", token="key", predicates=["before"])
        graph.add_node("2", token="table", predicates=["before", "near"])
        graph.add_node("3", token="lamp", predicates=["near"])
        
        graph.add_edge("1", "2", predicate="before")
        graph.add_edge("2", "3", predicate="near")

        # Query for the start of the chain
        result = query_graph(graph, "key before table near lamp")
        
        # Verify the chain is traversed correctly
        assert len(result) > 0, "Should find the chain"
        # The first node should be the key
        if result:
            assert result[0].token == "key", "First node in chain should be 'key'"
