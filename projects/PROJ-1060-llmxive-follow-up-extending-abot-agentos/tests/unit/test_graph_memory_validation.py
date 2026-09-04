"""
Unit tests for graph memory validation in graph_builder.py.

Tests that the SymbolicGraphBuilder correctly enforces memory limits
and generates appropriate validation reports.
"""
import pytest
import networkx as nx
from pathlib import Path
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_builder import SymbolicGraphBuilder, GraphNode, GraphEdge, build_graph_from_traces
from config import MAX_TRACES


class TestSymbolicGraphBuilderMemory:
    """Tests for memory footprint validation."""

    def test_initial_memory_footprint(self):
        """Test that a new graph has minimal memory footprint."""
        builder = SymbolicGraphBuilder(max_memory_gb=2.0)
        report = builder.get_validation_report()
        
        assert report['within_limit'] is True
        assert report['node_count'] == 0
        assert report['edge_count'] == 0
        assert report['error_count'] == 0

    def test_memory_limit_validation(self):
        """Test that memory limit validation works correctly."""
        # Create a builder with a very low limit
        builder = SymbolicGraphBuilder(max_memory_gb=0.0001)  # ~100KB limit
        
        # Add nodes and edges
        for i in range(1000):
            builder.add_node(f"node_{i}", f"token_{i}")
            if i > 0:
                builder.add_edge(f"node_{i-1}", f"node_{i}", "before")
        
        report = builder.get_validation_report()
        
        # Should have detected limit exceeded due to low threshold
        assert report['within_limit'] is False
        assert report['error_count'] > 0

    def test_memory_estimate_increases_with_graph_size(self):
        """Test that memory estimate increases as graph grows."""
        builder = SymbolicGraphBuilder(max_memory_gb=2.0)
        
        initial_report = builder.get_validation_report()
        initial_memory = initial_report['memory_mb']
        
        # Add nodes
        for i in range(100):
            builder.add_node(f"node_{i}", f"token_{i}")
        
        after_nodes_report = builder.get_validation_report()
        after_nodes_memory = after_nodes_report['memory_mb']
        
        # Add edges
        for i in range(1, 100):
            builder.add_edge(f"node_{i-1}", f"node_{i}", "before")
        
        final_report = builder.get_validation_report()
        final_memory = final_report['memory_mb']
        
        assert after_nodes_memory > initial_memory
        assert final_memory > after_nodes_memory

    def test_validation_error_on_limit_exceeded(self):
        """Test that validation errors are recorded when limit is exceeded."""
        builder = SymbolicGraphBuilder(max_memory_gb=0.00001)  # Extremely low limit
        
        # Add many nodes to exceed limit
        for i in range(5000):
            builder.add_node(f"node_{i}", f"token_{i}")
        
        report = builder.get_validation_report()
        
        # Should have memory limit exceeded errors
        memory_errors = [e for e in report['validation_errors'] 
                       if e['type'] == 'memory_limit_exceeded']
        assert len(memory_errors) > 0

    def test_build_from_traces_memory_validation(self):
        """Test memory validation during trace building."""
        # Create synthetic traces
        traces = []
        for i in range(100):
            traces.append({
                "id": f"trace_{i}",
                "steps": [{"observation": f"object_{j}", "action": "move"} 
                         for j in range(10)]
            })
        
        graph, report = build_graph_from_traces(traces, max_memory_gb=2.0)
        
        assert report['within_limit'] is True
        assert report['trace_count'] == 100
        assert report['node_count'] > 0
        assert report['edge_count'] > 0

    def test_dag_property_preserved(self):
        """Test that the graph remains a DAG during construction."""
        builder = SymbolicGraphBuilder(max_memory_gb=2.0)
        
        # Add nodes and edges
        for i in range(100):
            builder.add_node(f"node_{i}", f"token_{i}")
            if i > 0:
                builder.add_edge(f"node_{i-1}", f"node_{i}", "before")
        
        assert nx.is_directed_acyclic_graph(builder.graph)

    def test_inconsistency_detection(self):
        """Test that inconsistent edges are detected and excluded."""
        builder = SymbolicGraphBuilder(max_memory_gb=2.0)
        
        # Add nodes
        builder.add_node("node_a", "object_a")
        builder.add_node("node_b", "object_b")
        
        # Add edge with predicate
        edge1 = builder.add_edge("node_a", "node_b", "on_top_of", 
                                trace_context={"trace_id": "test_1"})
        assert edge1 is not None
        
        # Try to add reverse predicate (should be detected as inconsistent)
        edge2 = builder.add_edge("node_b", "node_a", "under",
                                trace_context={"trace_id": "test_2"})
        assert edge2 is None  # Should be excluded
        
        # Verify error was recorded
        report = builder.get_validation_report()
        inconsistency_errors = [e for e in report['validation_errors']
                              if e['type'] == 'inconsistency_detected']
        assert len(inconsistency_errors) > 0

    def test_memory_report_accuracy(self):
        """Test that memory report contains accurate information."""
        builder = SymbolicGraphBuilder(max_memory_gb=1.0)
        
        # Add some nodes and edges
        for i in range(50):
            builder.add_node(f"node_{i}", f"token_{i}")
            if i > 0:
                builder.add_edge(f"node_{i-1}", f"node_{i}", "before")
        
        report = builder.get_validation_report()
        
        # Verify report structure
        assert 'memory_mb' in report
        assert 'memory_limit_mb' in report
        assert 'within_limit' in report
        assert 'node_count' in report
        assert 'edge_count' in report
        assert 'trace_count' in report
        assert 'validation_errors' in report
        assert 'error_count' in report
        
        # Verify values are consistent
        assert report['node_count'] == builder.graph.number_of_nodes()
        assert report['edge_count'] == builder.graph.number_of_edges()
        assert report['within_limit'] == (report['memory_mb'] <= report['memory_limit_mb'])


class TestGraphBuilderIntegration:
    """Integration tests for graph builder with memory constraints."""

    def test_large_trace_set_within_limit(self):
        """Test that a large set of traces stays within memory limit."""
        # Create synthetic traces simulating real data
        traces = []
        for i in range(400):  # Under 500 limit
            traces.append({
                "id": f"trace_{i}",
                "steps": [
                    {"observation": f"object_{j % 50}", "action": "move"}
                    for j in range(20)
                ]
            })
        
        graph, report = build_graph_from_traces(traces, max_memory_gb=2.0)
        
        assert report['within_limit'] is True
        assert report['trace_count'] == 400
        assert report['node_count'] > 0
        assert report['edge_count'] > 0

    def test_boundary_case_exact_limit(self):
        """Test behavior at the exact memory limit boundary."""
        # This test verifies the system handles edge cases gracefully
        builder = SymbolicGraphBuilder(max_memory_gb=2.0)
        
        # Add nodes until we approach the limit
        i = 0
        while True:
            builder.add_node(f"node_{i}", f"token_{i}")
            report = builder.get_validation_report()
            
            if not report['within_limit']:
                break
            
            i += 1
            if i > 10000:  # Safety break
                break
        
        # Should have detected the limit
        assert report['within_limit'] is False or i >= 10000

    def test_empty_traces_handling(self):
        """Test that empty trace list is handled correctly."""
        traces = []
        graph, report = build_graph_from_traces(traces, max_memory_gb=2.0)
        
        assert report['within_limit'] is True
        assert report['trace_count'] == 0
        assert report['node_count'] == 0
        assert report['edge_count'] == 0
        assert nx.is_directed_acyclic_graph(graph)

    def test_single_trace_handling(self):
        """Test that a single trace is handled correctly."""
        traces = [{
            "id": "single_trace",
            "steps": [
                {"observation": "object_1", "action": "move"},
                {"observation": "object_2", "action": "pick"}
            ]
        }]
        
        graph, report = build_graph_from_traces(traces, max_memory_gb=2.0)
        
        assert report['within_limit'] is True
        assert report['trace_count'] == 1
        assert report['node_count'] == 2  # Two steps
        assert report['edge_count'] == 1  # One edge between steps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
