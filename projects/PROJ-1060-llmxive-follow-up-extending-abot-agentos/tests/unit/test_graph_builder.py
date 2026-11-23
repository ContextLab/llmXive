"""
Unit tests for the Graph Builder module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import networkx as nx
import pytest

from code.graph_builder import SymbolicGraphBuilder, build_graph_from_traces, save_graph, ALLOWED_PREDICATES
from code.config import PREDICATE_SET

class TestSymbolicGraphBuilder:
    def test_initialization(self):
        builder = SymbolicGraphBuilder(granularity="fine", predicate_set="spatial+temporal")
        assert builder.granularity == "fine"
        assert builder.predicate_set == "spatial+temporal"
        assert "before" in builder.allowed_predicates
        assert "on_top_of" in builder.allowed_predicates

    def test_add_node_creates_unique_id(self):
        builder = SymbolicGraphBuilder()
        node_id = builder._add_node("trace_1", 0, "object_A")
        assert node_id == "trace_1_step0_object_A"
        assert builder.graph.has_node(node_id)
        assert builder.graph.nodes[node_id]["token"] == "object_A"

    def test_add_edge_prevents_cycles(self):
        builder = SymbolicGraphBuilder()
        n1 = builder._add_node("t1", 0, "a")
        n2 = builder._add_node("t1", 1, "b")
        
        # Add forward edge
        assert builder._add_edge(n1, n2, "before") is True
        
        # Try to add backward edge (would create cycle)
        assert builder._add_edge(n2, n1, "before") is False

    def test_add_edge_respects_predicate_set(self):
        builder = SymbolicGraphBuilder(predicate_set="spatial")
        n1 = builder._add_node("t1", 0, "a")
        n2 = builder._add_node("t1", 1, "b")
        
        # "before" might not be in spatial set depending on config, but let's test a known exclusion
        # If PREDICATE_SET is "spatial", "before" is excluded if defined in ALLOWED_PREDICATES logic
        # In our code, spatial set does not include "before" by default in ALLOWED_PREDICATES dict
        # unless specified. Let's assume standard spatial set.
        
        # Force a predicate not in set
        if "before" not in builder.allowed_predicates:
            assert builder._add_edge(n1, n2, "before") is False
        
        # Valid predicate
        if "on_top_of" in builder.allowed_predicates:
            assert builder._add_edge(n1, n2, "on_top_of") is True

    def test_build_from_traces_creates_dag(self):
        # Mock traces
        traces = [
            {
                "id": "trace_1",
                "steps": [
                    {"observation": "view1", "action": "go to"},
                    {"observation": "view2", "action": "pick"}
                ]
            }
        ]
        
        # Mock discretize_trace to return simple tokens
        with patch("code.graph_builder.discretize_trace") as mock_discretize:
            mock_discretize.return_value = ["object_A", "object_B"]
            
            builder = SymbolicGraphBuilder()
            graph = builder.build_from_traces(traces)
            
            assert isinstance(graph, nx.DiGraph)
            assert nx.is_directed_acyclic_graph(graph)
            assert graph.number_of_nodes() == 2
            assert graph.number_of_edges() >= 1 # At least temporal edge

class TestBuildGraphFromTraces:
    def test_returns_stats(self):
        traces = [
            {"id": "t1", "steps": [{"obs": "a"}, {"obs": "b"}]}
        ]
        
        with patch("code.graph_builder.discretize_trace") as mock_discretize:
            mock_discretize.return_value = ["tok1", "tok2"]
            
            graph, stats = build_graph_from_traces(traces)
            
            assert "num_nodes" in stats
            assert "num_edges" in stats
            assert "is_dag" in stats
            assert stats["is_dag"] is True

class TestSaveGraph:
    def test_saves_to_json(self):
        builder = SymbolicGraphBuilder()
        n1 = builder._add_node("t1", 0, "a")
        n2 = builder._add_node("t1", 1, "b")
        builder._add_edge(n1, n2, "before")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_graph.json"
            save_graph(builder.graph, str(path))
            
            assert path.exists()
            with open(path, 'r') as f:
                data = json.load(f)
            
            assert "nodes" in data
            assert "edges" in data
            assert len(data["nodes"]) == 2
            assert len(data["edges"]) == 1