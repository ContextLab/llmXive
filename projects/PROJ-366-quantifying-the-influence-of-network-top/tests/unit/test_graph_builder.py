"""
Unit tests for graph_builder.py focusing on bond cutoff logic and node-degree statistics.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the functions to test
from ingest.graph_builder import build_graph_from_xyz, calculate_node_degree_stats


def create_test_xyz_file(content: str, tmp_path: Path) -> Path:
    """Helper to create a temporary XYZ file."""
    file_path = tmp_path / "test_structure.xyz"
    file_path.write_text(content)
    return file_path


def test_bond_cutoff_exact_boundary():
    """
    Test that atoms exactly at the cutoff distance (3.0 Å) are connected.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create a simple XYZ with two atoms exactly 3.0 Angstroms apart along x-axis
        # Header: 2 atoms, comment line
        # Atom 1 at (0, 0, 0)
        # Atom 2 at (3.0, 0, 0)
        xyz_content = """2
        Test structure for cutoff
        Si 0.0 0.0 0.0
        Si 3.0 0.0 0.0
        """
        xyz_file = create_test_xyz_file(xyz_content, tmp_path)

        graph = build_graph_from_xyz(xyz_file, cutoff=3.0)

        # Should have 2 nodes
        assert len(graph["nodes"]) == 2
        # Should have exactly 1 edge (0-1)
        assert len(graph["edges"]) == 1
        assert (0, 1) in graph["edges"] or (1, 0) in graph["edges"]


def test_bond_cutoff_just_inside():
    """
    Test that atoms slightly inside the cutoff (2.99 Å) are connected.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Atoms at 0 and 2.99
        xyz_content = """2
        Test structure
        Si 0.0 0.0 0.0
        Si 2.99 0.0 0.0
        """
        xyz_file = create_test_xyz_file(xyz_content, tmp_path)

        graph = build_graph_from_xyz(xyz_file, cutoff=3.0)

        assert len(graph["nodes"]) == 2
        assert len(graph["edges"]) == 1


def test_bond_cutoff_just_outside():
    """
    Test that atoms slightly outside the cutoff (3.01 Å) are NOT connected.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Atoms at 0 and 3.01
        xyz_content = """2
        Test structure
        Si 0.0 0.0 0.0
        Si 3.01 0.0 0.0
        """
        xyz_file = create_test_xyz_file(xyz_content, tmp_path)

        graph = build_graph_from_xyz(xyz_file, cutoff=3.0)

        assert len(graph["nodes"]) == 2
        # No edges should exist
        assert len(graph["edges"]) == 0


def test_bond_cutoff_three_atoms_chain():
    """
    Test a chain of 3 atoms: A-B (2.0), B-C (2.0), A-C (4.0).
    Only A-B and B-C should be edges.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Atom A at 0, B at 2, C at 4
        xyz_content = """3
        Chain test
        Si 0.0 0.0 0.0
        Si 2.0 0.0 0.0
        Si 4.0 0.0 0.0
        """
        xyz_file = create_test_xyz_file(xyz_content, tmp_path)

        graph = build_graph_from_xyz(xyz_file, cutoff=3.0)

        assert len(graph["nodes"]) == 3
        # Edges: (0,1) and (1,2). (0,2) is 4.0 Å apart, so no edge.
        assert len(graph["edges"]) == 2
        assert (0, 1) in graph["edges"] or (1, 0) in graph["edges"]
        assert (1, 2) in graph["edges"] or (2, 1) in graph["edges"]
        assert (0, 2) not in graph["edges"] and (2, 0) not in graph["edges"]


def test_node_degree_stats_single_graph():
    """
    Test node degree statistics calculation for a single graph.
    """
    # Construct a simple graph manually to test the stats function
    # Graph: 0-1, 0-2, 0-3 (Node 0 has degree 3, others have degree 1)
    nodes = [{"id": 0}, {"id": 1}, {"id": 2}, {"id": 3}]
    edges = [(0, 1), (0, 2), (0, 3)]
    graph = {"nodes": nodes, "edges": edges}

    stats = calculate_node_degree_stats(graph)

    assert "degrees" in stats
    assert "mode" in stats
    assert "mean" in stats
    assert "min" in stats
    assert "max" in stats

    # Verify degrees: [3, 1, 1, 1]
    assert stats["degrees"] == [3, 1, 1, 1]
    # Mode should be 1 (appears 3 times)
    assert stats["mode"] == 1
    # Mean should be 1.5
    assert np.isclose(stats["mean"], 1.5)
    assert stats["min"] == 1
    assert stats["max"] == 3


def test_node_degree_stats_empty_graph():
    """
    Test node degree stats for a graph with no edges.
    """
    nodes = [{"id": 0}, {"id": 1}]
    edges = []
    graph = {"nodes": nodes, "edges": edges}

    stats = calculate_node_degree_stats(graph)

    assert stats["degrees"] == [0, 0]
    assert stats["mode"] == 0
    assert stats["mean"] == 0.0
    assert stats["min"] == 0
    assert stats["max"] == 0


def test_node_degree_stats_disconnected_components():
    """
    Test stats for a graph with two disconnected components.
    Component 1: 0-1 (degrees 1, 1)
    Component 2: 2-3-4 (degrees 1, 2, 1)
    Total degrees: [1, 1, 1, 2, 1] -> Mode is 1.
    """
    nodes = [{"id": i} for i in range(5)]
    edges = [(0, 1), (2, 3), (3, 4)]
    graph = {"nodes": nodes, "edges": edges}

    stats = calculate_node_degree_stats(graph)

    assert stats["degrees"] == [1, 1, 1, 2, 1]
    assert stats["mode"] == 1
    assert np.isclose(stats["mean"], 1.2)


def test_node_degree_stats_json_schema_validation():
    """
    Unit test to verify that the output of calculate_node_degree_stats
    conforms to the expected JSON schema structure for node_degree_stats.json.
    This ensures the downstream consumer (T016) can parse the output correctly.
    """
    # Create a mock graph
    nodes = [{"id": i} for i in range(4)]
    edges = [(0, 1), (0, 2), (0, 3)] # Star graph
    graph = {"nodes": nodes, "edges": edges}

    stats = calculate_node_degree_stats(graph)

    # Verify required keys exist
    required_keys = ["degrees", "mode", "mean", "min", "max", "count"]
    for key in required_keys:
        assert key in stats, f"Missing required key '{key}' in node degree stats schema"

    # Verify types
    assert isinstance(stats["degrees"], list), "degrees must be a list"
    assert isinstance(stats["mode"], (int, float)), "mode must be numeric"
    assert isinstance(stats["mean"], (int, float)), "mean must be numeric"
    assert isinstance(stats["min"], (int, float)), "min must be numeric"
    assert isinstance(stats["max"], (int, float)), "max must be numeric"
    assert isinstance(stats["count"], int), "count must be an integer"

    # Verify count matches number of nodes
    assert stats["count"] == len(graph["nodes"])

    # Verify that the stats are serializable to JSON
    try:
        json_str = json.dumps(stats)
        loaded = json.loads(json_str)
        assert loaded["mode"] == stats["mode"]
    except (TypeError, ValueError) as e:
        pytest.fail(f"Stats dictionary is not JSON serializable: {e}")