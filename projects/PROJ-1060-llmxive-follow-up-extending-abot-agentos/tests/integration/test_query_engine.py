"""
Integration tests for the query engine (T020).
Tests the deterministic depth-first traversal algorithm on the symbolic graph.
"""
import pytest
import networkx as nx
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from query_engine import query_graph, Node

class TestQueryEngineBasic:
    """Basic functionality tests for query_graph."""

    def test_empty_graph_returns_empty_list(self):
        """Test that querying an empty graph returns an empty list."""
        G = nx.DiGraph()
        results = query_graph(G, "Find anything")
        assert results == []

    def test_query_nonexistent_token_returns_empty(self):
        """Test that querying for a token that doesn't exist returns empty list."""
        G = nx.DiGraph()
        G.add_node("n1", token="kitchen")
        results = query_graph(G, "Find garage")
        assert results == []

    def test_query_exact_token_match(self):
        """Test querying for an exact token match."""
        G = nx.DiGraph()
        G.add_node("n1", token="kitchen")
        G.add_node("n2", token="bedroom")
        
        results = query_graph(G, "Find kitchen")
        assert len(results) == 1
        assert results[0].token == "kitchen"

    def test_case_insensitive_query(self):
        """Test that queries are case-insensitive."""
        G = nx.DiGraph()
        G.add_node("n1", token="Kitchen")
        
        results = query_graph(G, "find kitchen")
        assert len(results) == 1
        assert results[0].token == "Kitchen"

    def test_query_returns_node_dataclass(self):
        """Test that results are Node dataclass instances."""
        G = nx.DiGraph()
        G.add_node("n1", token="table", predicates=["furniture"])
        
        results = query_graph(G, "Find table")
        assert len(results) == 1
        assert isinstance(results[0], Node)
        assert results[0].id == "n1"
        assert results[0].token == "table"
        assert results[0].predicates == ["furniture"]

class TestQueryEngineTraversal:
    """Tests for depth-first traversal behavior."""

    def test_traversal_follows_edges(self):
        """Test that traversal follows graph edges."""
        G = nx.DiGraph()
        G.add_node("n1", token="start")
        G.add_node("n2", token="middle")
        G.add_node("n3", token="end")
        G.add_edge("n1", "n2", predicate="before")
        G.add_edge("n2", "n3", predicate="before")
        
        # Query for 'end' which is reachable via traversal
        results = query_graph(G, "Find end")
        assert len(results) == 1
        assert results[0].token == "end"

    def test_deterministic_ordering(self):
        """Test that results are returned in deterministic order."""
        G = nx.DiGraph()
        G.add_node("n1", token="item")
        G.add_node("n2", token="item")
        G.add_node("n3", token="item")
        
        results1 = query_graph(G, "Find item")
        results2 = query_graph(G, "Find item")
        
        # Should be same order
        assert len(results1) == len(results2)
        for i in range(len(results1)):
            assert results1[i].id == results2[i].id

    def test_no_infinite_loop_on_cycles(self):
        """Test that the algorithm handles cycles without infinite loops."""
        G = nx.DiGraph()
        G.add_node("n1", token="a")
        G.add_node("n2", token="b")
        G.add_edge("n1", "n2", predicate="link")
        G.add_edge("n2", "n1", predicate="link")
        
        # Should not hang, should return results
        results = query_graph(G, "Find a")
        assert len(results) == 1
        assert results[0].token == "a"

class TestQueryEngineComplex:
    """Tests for complex query patterns."""

    def test_query_with_multiple_matches(self):
        """Test query that matches multiple nodes."""
        G = nx.DiGraph()
        G.add_node("n1", token="cup")
        G.add_node("n2", token="cup")
        G.add_node("n3", token="plate")
        
        results = query_graph(G, "Find cup")
        assert len(results) == 2
        tokens = {r.token for r in results}
        assert tokens == {"cup"}

    def test_partial_token_match(self):
        """Test partial token matching."""
        G = nx.DiGraph()
        G.add_node("n1", token="microwave")
        G.add_node("n2", token="microwave_oven")
        G.add_node("n3", token="oven")
        
        results = query_graph(G, "Find microwave")
        # Should match 'microwave' and 'microwave_oven'
        assert len(results) >= 1
        assert any(r.token == "microwave" for r in results)

    def test_query_with_predicates(self):
        """Test query that includes predicate requirements."""
        G = nx.DiGraph()
        G.add_node("n1", token="counter")
        G.add_node("n2", token="kitchen")
        G.add_edge("n1", "n2", predicate="near")
        
        results = query_graph(G, "Find counter near kitchen")
        assert len(results) >= 1
        assert any(r.token == "counter" for r in results)

class TestQueryEngineEdgeCases:
    """Edge case tests."""

    def test_none_graph(self):
        """Test querying with None graph."""
        results = query_graph(None, "Find anything")
        assert results == []

    def test_special_characters_in_token(self):
        """Test tokens with special characters."""
        G = nx.DiGraph()
        G.add_node("n1", token="object-123")
        
        results = query_graph(G, "Find object-123")
        assert len(results) == 1

    def test_unicode_in_token(self):
        """Test tokens with unicode characters."""
        G = nx.DiGraph()
        G.add_node("n1", token="café")
        
        results = query_graph(G, "Find café")
        assert len(results) == 1

    def test_empty_query_string(self):
        """Test with empty query string."""
        G = nx.DiGraph()
        G.add_node("n1", token="test")
        
        results = query_graph(G, "")
        # Should return all nodes (limited)
        assert len(results) <= 100
        assert any(r.token == "test" for r in results)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])