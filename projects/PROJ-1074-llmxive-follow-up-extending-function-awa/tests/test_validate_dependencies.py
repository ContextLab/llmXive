"""
Tests for dependency validation module.

These tests verify:
1. Cycle detection works correctly
2. Topological sort produces valid orderings
3. Graph validation handles edge cases
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.validate_dependencies import (
    detect_cycle,
    topological_sort,
    validate_graph,
    validate_all_graphs,
)
from utils.common import ValidationError


class TestCycleDetection:
    """Tests for cycle detection functionality."""

    def test_simple_cycle(self):
        """Detect a simple A -> B -> A cycle."""
        graph = {
            "A": ["B"],
            "B": ["A"]
        }
        has_cycle, cycle_path = detect_cycle(graph)
        assert has_cycle is True
        assert cycle_path is not None
        assert "A" in cycle_path
        assert "B" in cycle_path

    def test_self_loop(self):
        """Detect a self-loop A -> A."""
        graph = {
            "A": ["A"]
        }
        has_cycle, cycle_path = detect_cycle(graph)
        assert has_cycle is True
        assert cycle_path == ["A", "A"]

    def test_no_cycle_linear(self):
        """No cycle in linear graph A -> B -> C."""
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": []
        }
        has_cycle, cycle_path = detect_cycle(graph)
        assert has_cycle is False
        assert cycle_path is None

    def test_no_cycle_dag(self):
        """No cycle in complex DAG."""
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": []
        }
        has_cycle, cycle_path = detect_cycle(graph)
        assert has_cycle is False
        assert cycle_path is None

    def test_complex_cycle(self):
        """Detect cycle in complex graph with multiple paths."""
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["D"],
            "D": ["B"]  # Creates cycle B -> C -> D -> B
        }
        has_cycle, cycle_path = detect_cycle(graph)
        assert has_cycle is True
        assert cycle_path is not None
        # Verify the cycle is valid
        cycle_set = set(cycle_path[:-1])  # Exclude duplicate end node
        assert "B" in cycle_set
        assert "C" in cycle_set
        assert "D" in cycle_set

    def test_empty_graph(self):
        """Empty graph has no cycle."""
        graph = {}
        has_cycle, cycle_path = detect_cycle(graph)
        assert has_cycle is False
        assert cycle_path is None

    def test_disconnected_components(self):
        """Graph with disconnected components, no cycles."""
        graph = {
            "A": ["B"],
            "B": [],
            "C": ["D"],
            "D": []
        }
        has_cycle, cycle_path = detect_cycle(graph)
        assert has_cycle is False
        assert cycle_path is None

    def test_disconnected_with_cycle(self):
        """Graph with disconnected components, one has cycle."""
        graph = {
            "A": ["B"],
            "B": [],
            "C": ["D"],
            "D": ["C"]  # Cycle in second component
        }
        has_cycle, cycle_path = detect_cycle(graph)
        assert has_cycle is True


class TestTopologicalSort:
    """Tests for topological sorting."""

    def test_linear_order(self):
        """Topological sort of linear graph."""
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": []
        }
        success, order = topological_sort(graph)
        assert success is True
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_dag_order(self):
        """Topological sort of DAG with branching."""
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": []
        }
        success, order = topological_sort(graph)
        assert success is True
        # A must come before B and C
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        # B and C must come before D
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

    def test_cycle_detection(self):
        """Topological sort fails on cyclic graph."""
        graph = {
            "A": ["B"],
            "B": ["A"]
        }
        success, order = topological_sort(graph)
        assert success is False
        # May return partial order

    def test_single_node(self):
        """Single node graph."""
        graph = {"A": []}
        success, order = topological_sort(graph)
        assert success is True
        assert order == ["A"]

    def test_empty_graph(self):
        """Empty graph."""
        graph = {}
        success, order = topological_sort(graph)
        assert success is True
        assert order == []

    def test_multiple_valid_orders(self):
        """Graph with multiple valid topological orders."""
        graph = {
            "A": [],
            "B": []
        }
        success, order = topological_sort(graph)
        assert success is True
        assert len(order) == 2
        assert set(order) == {"A", "B"}

    def test_complex_dag(self):
        """Complex DAG with multiple dependencies."""
        graph = {
            "A": ["B", "C", "D"],
            "B": ["E"],
            "C": ["E"],
            "D": ["F"],
            "E": ["G"],
            "F": ["G"],
            "G": []
        }
        success, order = topological_sort(graph)
        assert success is True
        # Verify all dependencies are respected
        for node, deps in graph.items():
            node_idx = order.index(node)
            for dep in deps:
                dep_idx = order.index(dep)
                assert node_idx < dep_idx, f"{node} should come before {dep}"

class TestGraphValidation:
    """Tests for graph validation."""

    def test_valid_graph_format(self):
        """Validate a graph with 'graph' key."""
        graph_data = {
            "id": "test1",
            "graph": {
                "A": ["B"],
                "B": []
            }
        }
        result = validate_graph(graph_data)
        assert result["id"] == "test1"
        assert result["valid"] is True
        assert result["has_cycle"] is False

    def test_invalid_graph_format(self):
        """Validate fails with missing keys."""
        graph_data = {
            "id": "test2"
            # Missing 'graph', 'nodes', or 'edges'
        }
        with pytest.raises(ValidationError):
            validate_graph(graph_data)

    def test_cyclic_graph_validation(self):
        """Cyclic graph is marked invalid."""
        graph_data = {
            "id": "test3",
            "graph": {
                "A": ["B"],
                "B": ["A"]
            }
        }
        result = validate_graph(graph_data)
        assert result["valid"] is False
        assert result["has_cycle"] is True

    def test_nodes_edges_format(self):
        """Validate graph with nodes/edges format."""
        graph_data = {
            "id": "test4",
            "nodes": ["A", "B", "C"],
            "edges": [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"}
            ]
        }
        result = validate_graph(graph_data)
        assert result["valid"] is True
        assert result["has_cycle"] is False

    def test_empty_graph_validation(self):
        """Empty graph is valid."""
        graph_data = {
            "id": "test5",
            "graph": {}
        }
        result = validate_graph(graph_data)
        assert result["valid"] is True

class TestValidationIntegration:
    """Integration tests for validate_all_graphs."""

    def test_validate_single_graph(self, tmp_path):
        """Validate a single graph from file."""
        graphs_file = tmp_path / "graphs.json"
        data = {
            "id": "single",
            "graph": {
                "A": ["B"],
                "B": []
            }
        }
        import json
        graphs_file.write_text(json.dumps(data))
        
        results = validate_all_graphs(graphs_file)
        assert results["summary"]["total_graphs"] == 1
        assert results["summary"]["valid_graphs"] == 1
        assert results["summary"]["all_valid"] is True

    def test_validate_multiple_graphs(self, tmp_path):
        """Validate multiple graphs from file."""
        graphs_file = tmp_path / "graphs.json"
        data = [
            {
                "id": "valid1",
                "graph": {"A": ["B"], "B": []}
            },
            {
                "id": "valid2",
                "graph": {"C": [], "D": []}
            }
        ]
        import json
        graphs_file.write_text(json.dumps(data))
        
        results = validate_all_graphs(graphs_file)
        assert results["summary"]["total_graphs"] == 2
        assert results["summary"]["valid_graphs"] == 2
        assert results["summary"]["all_valid"] is True

    def test_validate_with_invalid(self, tmp_path):
        """Validation catches invalid graphs."""
        graphs_file = tmp_path / "graphs.json"
        data = [
            {
                "id": "valid",
                "graph": {"A": ["B"], "B": []}
            },
            {
                "id": "invalid",
                "graph": {"A": ["B"], "B": ["A"]}  # Cycle
            }
        ]
        import json
        graphs_file.write_text(json.dumps(data))
        
        results = validate_all_graphs(graphs_file)
        assert results["summary"]["total_graphs"] == 2
        assert results["summary"]["valid_graphs"] == 1
        assert results["summary"]["invalid_graphs"] == 1
        assert results["summary"]["all_valid"] is False

    def test_missing_file(self, tmp_path):
        """Handle missing file gracefully."""
        graphs_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            validate_all_graphs(graphs_file)

    def test_invalid_json(self, tmp_path):
        """Handle invalid JSON."""
        graphs_file = tmp_path / "invalid.json"
        graphs_file.write_text("{ invalid json }")
        
        with pytest.raises(ValidationError):
            validate_all_graphs(graphs_file)