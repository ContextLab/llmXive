"""
Unit tests for src.data.graph_construction module.
"""

import numpy as np
import pytest
from pathlib import Path
import tempfile
import json

from src.data.graph_construction import (
    calculate_coordination_number,
    build_adjacency_matrix,
    extract_edge_attributes,
    construct_transition_state_graph,
    filter_outliers,
    save_graphs_to_parquet,
    save_metadata
)


class TestCalculateCoordinationNumber:
    def test_simple_triangle(self):
        """Three atoms forming an equilateral triangle with side < cutoff."""
        positions = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [1.0, 1.732, 0.0]  # approx equilateral triangle side 2.0
        ])
        atomic_numbers = [6, 6, 6]
        cutoff = 3.5

        cn = calculate_coordination_number(positions, atomic_numbers, cutoff)

        # Each atom should have 2 neighbors
        assert len(cn) == 3
        assert all(c == 2 for c in cn)

    def test_isolated_atom(self):
        """Single atom should have 0 coordination."""
        positions = np.array([[0.0, 0.0, 0.0]])
        atomic_numbers = [6]
        cutoff = 3.5

        cn = calculate_coordination_number(positions, atomic_numbers, cutoff)
        assert len(cn) == 1
        assert cn[0] == 0

    def test_large_cutoff(self):
        """Atoms far apart with large cutoff should connect."""
        positions = np.array([
            [0.0, 0.0, 0.0],
            [10.0, 0.0, 0.0]
        ])
        atomic_numbers = [6, 6]
        cutoff = 15.0

        cn = calculate_coordination_number(positions, atomic_numbers, cutoff)
        assert all(c == 1 for c in cn)

    def test_small_cutoff(self):
        """Atoms close but cutoff too small should not connect."""
        positions = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0]
        ])
        atomic_numbers = [6, 6]
        cutoff = 1.0

        cn = calculate_coordination_number(positions, atomic_numbers, cutoff)
        assert all(c == 0 for c in cn)


class TestBuildAdjacencyMatrix:
    def test_symmetric(self):
        """Adjacency matrix should be symmetric."""
        positions = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [5.0, 0.0, 0.0]
        ])
        adj = build_adjacency_matrix(positions, cutoff=3.5)

        assert adj.shape == (3, 3)
        assert np.allclose(adj, adj.T)
        # (0,1) and (1,0) should be True
        assert adj[0, 1] and adj[1, 0]
        # (0,2) and (2,0) should be False (dist 5.0 > 3.5)
        assert not adj[0, 2] and not adj[2, 0]
        # Diagonal should be False
        assert not np.any(np.diag(adj))


class TestExtractEdgeAttributes:
    def test_edge_extraction(self):
        """Verify edge indices and distances are correct."""
        positions = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [2.0, 2.0, 0.0]
        ])
        adj = np.array([
            [False, True, True],
            [True, False, True],
            [True, True, False]
        ])

        indices, distances = extract_edge_attributes(positions, adj)

        # Should have 6 edges (undirected, 3 pairs)
        assert indices.shape[1] == 6
        # Distances should match geometry
        # (0,1) -> 2.0, (0,2) -> sqrt(8) ~ 2.828, (1,2) -> 2.0
        expected_distances = [2.0, 2.8284271247461903, 2.0, 2.8284271247461903, 2.0, 2.0]
        # Sort both to compare order-independently
        assert np.allclose(sorted(distances), sorted(expected_distances))


class TestConstructTransitionStateGraph:
    def test_full_construction(self):
        """Test complete graph construction with metadata."""
        atomic_numbers = [6, 6, 7]
        formal_charges = [0, 0, 0]
        positions = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],
            [0.0, 1.5, 0.0]
        ])
        energy_dft = -100.5
        barrier_height = 15.2
        ligand_class = "Group 13"
        reaction_id = "rxn_001"

        graph = construct_transition_state_graph(
            atomic_numbers=atomic_numbers,
            formal_charges=formal_charges,
            positions=positions,
            energy_dft=energy_dft,
            barrier_height=barrier_height,
            ligand_class=ligand_class,
            reaction_id=reaction_id
        )

        assert "nodes" in graph
        assert "edges" in graph
        assert "metadata" in graph

        assert len(graph["nodes"]) == 3
        assert graph["metadata"]["energy_dft"] == energy_dft
        assert graph["metadata"]["barrier_height"] == barrier_height
        assert graph["metadata"]["ligand_class"] == ligand_class
        assert graph["metadata"]["reaction_id"] == reaction_id

        # Check node structure
        for node in graph["nodes"]:
            assert "atomic_number" in node
            assert "formal_charge" in node
            assert "coordination_number" in node
            assert "position" in node

    def test_mismatched_lengths(self):
        """Should raise ValueError if lengths don't match."""
        with pytest.raises(ValueError):
            construct_transition_state_graph(
                atomic_numbers=[6, 6],
                formal_charges=[0],
                positions=np.array([[0,0,0], [1,1,1]])
            )


class TestFilterOutliers:
    def test_no_outliers(self):
        """Graphs with low coordination should pass."""
        graphs = [
            {
                "nodes": [
                    {"coordination_number": 2},
                    {"coordination_number": 3}
                ],
                "metadata": {"reaction_id": "rxn_1"}
            }
        ]
        train, outliers = filter_outliers(graphs, max_coordination=6)
        assert len(train) == 1
        assert len(outliers) == 0
        assert train[0]["metadata"]["is_outlier"] is False

    def test_with_outliers(self):
        """Graphs with high coordination should be filtered."""
        graphs = [
            {
                "nodes": [
                    {"coordination_number": 2},
                    {"coordination_number": 7}  # Outlier
                ],
                "metadata": {"reaction_id": "rxn_2"}
            },
            {
                "nodes": [
                    {"coordination_number": 3}
                ],
                "metadata": {"reaction_id": "rxn_3"}
            }
        ]
        train, outliers = filter_outliers(graphs, max_coordination=6)
        assert len(train) == 1
        assert len(outliers) == 1
        assert train[0]["metadata"]["reaction_id"] == "rxn_3"
        assert outliers[0]["metadata"]["reaction_id"] == "rxn_2"
        assert outliers[0]["metadata"]["is_outlier"] is True
        assert outliers[0]["metadata"]["max_coordination"] == 7


class TestSaveGraphsToParquet:
    def test_save_and_load(self):
        """Test saving graphs to parquet and reading back."""
        graphs = [
            {
                "nodes": [{"atomic_number": 6, "formal_charge": 0, "coordination_number": 2, "position": [0,0,0]}],
                "edges": [],
                "metadata": {"reaction_id": "rxn_1", "energy_dft": -100.0}
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_graphs.parquet"
            save_graphs_to_parquet(graphs, output_path)

            assert output_path.exists()

            import pandas as pd
            df = pd.read_parquet(output_path)
            assert len(df) == 1
            assert df.iloc[0]["reaction_id"] == "rxn_1"
            assert df.iloc[0]["energy_dft"] == -100.0


class TestSaveMetadata:
    def test_save_metadata_file(self):
        """Test saving metadata JSON."""
        training = [{"metadata": {"reaction_id": "t1"}}]
        outliers = [{"metadata": {"reaction_id": "o1"}}]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            save_metadata(training, outliers, output_dir)

            meta_path = output_dir / "graph_construction_metadata.json"
            assert meta_path.exists()

            with open(meta_path, "r") as f:
                data = json.load(f)

            assert data["total_graphs"] == 2
            assert data["training_graphs"] == 1
            assert data["outlier_graphs"] == 1