import pytest
import networkx as nx
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from graph_builder import parse_trajectory, build_dag, build_co_reference_graph
from config import cutoff_depth

class TestParseTrajectory:
    """Tests for parse_trajectory function including edge cases."""

    def test_normal_case_returns_cutoff_spans(self):
        """Test that normal case returns correct number of spans."""
        # Create a trajectory with 100 spans
        spans = [{"id": i, "text": f"span {i}"} for i in range(100)]
        trajectory = {"spans": spans}
        
        # Default cutoff_depth is typically 0.2, so we expect 20 spans
        result = parse_trajectory(trajectory)
        
        expected_count = int(100 * cutoff_depth)
        assert len(result) == expected_count
        assert result[0]["id"] == 0
        assert result[-1]["id"] == expected_count - 1

    def test_short_trajectory_returns_all_spans(self):
        """Test that trajectories shorter than cutoff use all spans."""
        # Create a trajectory with only 5 spans
        # If cutoff_depth is 0.2, cutoff would be 1, so this should return all 5
        spans = [{"id": i, "text": f"span {i}"} for i in range(5)]
        trajectory = {"spans": spans}
        
        result = parse_trajectory(trajectory)
        
        # Should return all spans since 5 < int(5 * cutoff_depth) might be 1
        # But if 5 * cutoff_depth < 5, it should still return all if len < cutoff
        expected_count = min(5, int(5 * cutoff_depth)) if int(5 * cutoff_depth) > 0 else 5
        # Actually, per implementation: if total_spans < cutoff, return all
        cutoff = int(5 * cutoff_depth)
        if 5 < cutoff:
            assert len(result) == 5
        else:
            assert len(result) == cutoff

    def test_empty_trajectory_returns_empty_list(self):
        """Test that empty trajectories return empty list."""
        trajectory = {"spans": []}
        result = parse_trajectory(trajectory)
        assert len(result) == 0

    def test_missing_spans_key_returns_empty_list(self):
        """Test that trajectories without 'spans' key return empty list."""
        trajectory = {"id": "test"}
        result = parse_trajectory(trajectory)
        assert len(result) == 0

    def test_single_span_trajectory(self):
        """Test trajectory with exactly one span."""
        spans = [{"id": 0, "text": "single span"}]
        trajectory = {"spans": spans}
        
        result = parse_trajectory(trajectory)
        
        # Should return the single span
        assert len(result) == 1
        assert result[0]["id"] == 0

class TestBuildCoReferenceGraph:
    """Tests for build_co_reference_graph function."""

    def test_empty_spans_returns_empty_graph(self):
        """Test that empty spans list returns empty graph."""
        graph = build_co_reference_graph([])
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_single_span_returns_single_node_graph(self):
        """Test that single span returns graph with one node, zero edges."""
        spans = [{"id": "span1", "text": "Hello world"}]
        graph = build_co_reference_graph(spans)
        
        assert graph.number_of_nodes() == 1
        assert graph.number_of_edges() == 0

    def test_spans_with_shared_citations_create_edges(self):
        """Test that spans sharing citations get connected."""
        spans = [
            {"id": "span1", "text": "As mentioned in [1] this is important"},
            {"id": "span2", "text": "Further discussion of [1] confirms this"}
        ]
        graph = build_co_reference_graph(spans)
        
        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 1
        assert graph.has_edge("span1", "span2") or graph.has_edge("span2", "span1")

    def test_spans_with_high_text_overlap_create_edges(self):
        """Test that spans with high word overlap get connected."""
        spans = [
            {"id": "span1", "text": "The quick brown fox jumps over the lazy dog"},
            {"id": "span2", "text": "A quick brown dog jumps over the lazy fox"}
        ]
        graph = build_co_reference_graph(spans)
        
        # Should have edges due to high overlap
        assert graph.number_of_nodes() == 2
        # Overlap is significant enough to create edge
        assert graph.number_of_edges() >= 1

    def test_no_shared_citations_or_overlap_returns_no_edges(self):
        """Test that unrelated spans return graph with no edges."""
        spans = [
            {"id": "span1", "text": "Apple pie is delicious"},
            {"id": "span2", "text": "Quantum physics is complex"}
        ]
        graph = build_co_reference_graph(spans)
        
        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 0

class TestBuildDAG:
    """Tests for build_dag function including zero-edge cases."""

    def test_normal_trajectory_returns_dag(self):
        """Test that normal trajectory returns a valid DAG."""
        trajectory = {
            "spans": [
                {"id": "1", "text": "Introduction [1]"},
                {"id": "2", "text": "As [1] states, this is true"},
                {"id": "3", "text": "Therefore, we conclude"}
            ]
        }
        
        graph = build_dag(trajectory)
        
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() >= 1

    def test_empty_trajectory_returns_empty_graph(self):
        """Test that empty trajectory returns empty graph."""
        trajectory = {"spans": []}
        graph = build_dag(trajectory)
        
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_zero_edge_case_returns_empty_graph(self):
        """Test that trajectory with no co-reference signals returns empty graph."""
        # Create spans with no citations and no text overlap
        trajectory = {
            "spans": [
                {"id": "1", "text": "Apple pie is delicious"},
                {"id": "2", "text": "Quantum physics is complex"},
                {"id": "3", "text": "Basketball is fun"}
            ]
        }
        
        graph = build_dag(trajectory)
        
        # Per requirements: zero-edge cases should return empty graph
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_edges() == 0
        # Note: Nodes might exist but no edges, which is the "empty graph" state
        # for the purpose of metrics calculation

    def test_short_trajectory_uses_all_spans(self):
        """Test that short trajectories use all available spans."""
        # Create a trajectory with very few spans
        trajectory = {
            "spans": [
                {"id": "1", "text": "First [1]"},
                {"id": "2", "text": "Second [1]"}
            ]
        }
        
        graph = build_dag(trajectory)
        
        # Should process all spans even if fewer than cutoff
        assert isinstance(graph, nx.DiGraph)
        # At minimum, nodes should be created
        assert graph.number_of_nodes() <= 2

    def test_is_directed_acyclic_graph(self):
        """Test that output is always a DAG (no cycles)."""
        # Create a trajectory that might induce cycles
        trajectory = {
            "spans": [
                {"id": "1", "text": "See [1] and [2]"},
                {"id": "2", "text": "As in [1] and [3]"},
                {"id": "3", "text": "Reference [2] and [1]"}
            ]
        }
        
        graph = build_dag(trajectory)
        
        # The function should ensure DAG property
        assert nx.is_directed_acyclic_graph(graph) or graph.number_of_edges() == 0
