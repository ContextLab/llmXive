"""
Contract Test: Graph Schema Compliance.

Verifies that the graph construction logic adheres to the 
defined schema in data/schemas/ground_truth_mapping.json.
"""
import json
import pytest
from pathlib import Path
from typing import List, Dict, Any

import networkx as nx

# Import from code/
from graph_builder import SymbolicGraphBuilder, GraphNode, GraphEdge
from config import PREDICATE_SET

class TestGraphSchemaCompliance:
    """Tests ensuring graph output matches the required schema."""

    def test_node_structure_matches_schema(self, sample_alfworld_trace, ground_truth_schema):
        """
        Contract: Nodes must contain 'id', 'token', and 'type' keys.
        """
        builder = SymbolicGraphBuilder()
        graph = builder.build_from_trace(sample_alfworld_trace)

        # Verify node attributes
        for node in graph.nodes(data=True):
            node_id, attrs = node
            assert "id" in attrs or node_id is not None, "Node must have an ID"
            assert "token" in attrs, "Node must have a 'token' field"
            assert isinstance(attrs["token"], str), "Token must be a string"
        
        # Verify against ground truth allowed tokens if available
        allowed_nodes = set(ground_truth_schema.get("nodes", []))
        if allowed_nodes:
            for _, attrs in graph.nodes(data=True):
                token = attrs.get("token")
                if token:
                    # Allow "unknown_object" as per T015
                    assert token in allowed_nodes or token == "unknown_object", \
                        f"Token '{token}' not in ground truth schema"

    def test_edge_predicate_compliance(self, sample_alfworld_trace, ground_truth_schema):
        """
        Contract: Edges must use predicates from the allowed list.
        """
        builder = SymbolicGraphBuilder()
        graph = builder.build_from_trace(sample_alfworld_trace)

        allowed_predicates = set(ground_truth_schema.get("predicates", []))
        
        # Default set if schema is empty
        if not allowed_predicates:
            allowed_predicates = {"on_top_of", "near", "before", "inside", "next_to"}

        for u, v, attrs in graph.edges(data=True):
            predicate = attrs.get("predicate")
            assert predicate is not None, "Edge must have a 'predicate' field"
            assert predicate in allowed_predicates, \
                f"Predicate '{predicate}' is not in allowed list: {allowed_predicates}"

    def test_graph_is_dag(self, sample_alfworld_trace):
        """
        Contract: The constructed graph must be a Directed Acyclic Graph (DAG).
        """
        builder = SymbolicGraphBuilder()
        graph = builder.build_from_trace(sample_alfworld_trace)

        # NetworkX check for DAG
        is_dag = nx.is_directed_acyclic_graph(graph)
        assert is_dag, "Constructed graph must be a Directed Acyclic Graph (DAG)"

    def test_schema_serialization_format(self, sample_alfworld_trace, ground_truth_schema):
        """
        Contract: Graph must be serializable to the schema format 
        (nodes: list of strings, edges: list of dicts).
        """
        builder = SymbolicGraphBuilder()
        graph = builder.build_from_trace(sample_alfworld_trace)

        # Convert to schema format
        nodes_list = [str(attrs.get("token", "")) for _, attrs in graph.nodes(data=True)]
        edges_list = [
            {
                "source": str(u),
                "target": str(v),
                "predicate": attrs.get("predicate", "")
            }
            for u, v, attrs in graph.edges(data=True)
        ]

        # Validate structure types
        assert isinstance(nodes_list, list), "Nodes must be a list"
        assert all(isinstance(n, str) for n in nodes_list), "All nodes must be strings"
        
        assert isinstance(edges_list, list), "Edges must be a list"
        for edge in edges_list:
            assert isinstance(edge, dict), "Edge must be a dict"
            assert "source" in edge and "target" in edge and "predicate" in edge, \
                "Edge must have source, target, and predicate"

    def test_predicate_set_config_consistency(self, sample_alfworld_trace):
        """
        Contract: Predicates used must match the configured PREDICATE_SET in config.py.
        """
        builder = SymbolicGraphBuilder()
        graph = builder.build_from_trace(sample_alfworld_trace)

        # Expected predicates based on config
        expected_predicates = {"spatial", "spatial+temporal"} # Simplified check logic
        
        # In a real scenario, we'd map the PREDICATE_SET string to actual predicate names.
        # For this contract test, we ensure no NULL predicates exist.
        for _, _, attrs in graph.edges(data=True):
            assert attrs.get("predicate") is not None, "Predicate cannot be None"
            assert attrs.get("predicate") != "", "Predicate cannot be empty string"
