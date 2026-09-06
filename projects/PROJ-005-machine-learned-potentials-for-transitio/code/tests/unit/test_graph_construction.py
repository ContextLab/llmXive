"""
Unit tests for the graph construction module.
"""
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import pyarrow.parquet as pq

from src.data.graph_construction import (
    calculate_coordination_number,
    build_adjacency_matrix,
    extract_edge_attributes,
    construct_transition_state_graph,
    filter_outliers,
    save_graphs_to_parquet,
    save_metadata,
    run_graph_construction,
    COORDINATION_CUTOFF_ANGSTROM,
    OUTLIER_COORDINATION_THRESHOLD
)

class TestCalculateCoordinationNumber:
    def test_simple_triangle(self):
        """Test coordination number for a simple triangle."""
        # 3 atoms in a triangle, all within 2.0 A
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],
            [0.75, 1.3, 0.0]
        ])
        atomic_numbers = np.array([1, 1, 1])
        cutoff = 2.0

        cn = calculate_coordination_number(atomic_numbers, coords, cutoff)
        # Each atom should have 2 neighbors
        assert np.all(cn == 2)

    def test_linear_chain(self):
        """Test coordination number for a linear chain."""
        # 4 atoms in a line, 1.5 A apart
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],
            [3.0, 0.0, 0.0],
            [4.5, 0.0, 0.0]
        ])
        atomic_numbers = np.array([1, 1, 1, 1])
        cutoff = 2.0

        cn = calculate_coordination_number(atomic_numbers, coords, cutoff)
        # Ends have 1 neighbor, middle have 2
        assert cn[0] == 1
        assert cn[1] == 2
        assert cn[2] == 2
        assert cn[3] == 1

    def test_empty_input(self):
        """Test with empty input."""
        coords = np.array([]).reshape(0, 3)
        atomic_numbers = np.array([])
        cn = calculate_coordination_number(atomic_numbers, coords)
        assert len(cn) == 0

    def test_isolated_atom(self):
        """Test with isolated atoms (no neighbors within cutoff)."""
        coords = np.array([
            [0.0, 0.0, 0.0],
            [10.0, 10.0, 10.0]
        ])
        atomic_numbers = np.array([1, 1])
        cutoff = 2.0

        cn = calculate_coordination_number(atomic_numbers, coords, cutoff)
        assert np.all(cn == 0)

class TestBuildAdjacencyMatrix:
    def test_symmetric(self):
        """Test that adjacency matrix is symmetric."""
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],
            [0.0, 1.5, 0.0]
        ])
        atomic_numbers = np.array([1, 1, 1])
        cutoff = 2.0

        adj = build_adjacency_matrix(atomic_numbers, coords, cutoff)
        assert np.all(adj == adj.T)

    def test_no_self_loops(self):
        """Test that diagonal is False."""
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0]
        ])
        atomic_numbers = np.array([1, 1])
        cutoff = 2.0

        adj = build_adjacency_matrix(atomic_numbers, coords, cutoff)
        assert not np.any(np.diag(adj))

    def test_empty_input(self):
        """Test with empty input."""
        coords = np.array([]).reshape(0, 3)
        atomic_numbers = np.array([])
        adj = build_adjacency_matrix(atomic_numbers, coords)
        assert adj.shape == (0, 0)

class TestExtractEdgeAttributes:
    def test_edge_count(self):
        """Test that edge count matches adjacency matrix."""
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],
            [0.0, 1.5, 0.0]
        ])
        atomic_numbers = np.array([1, 1, 1])
        cutoff = 2.0

        src, tgt, dist = extract_edge_attributes(atomic_numbers, coords, cutoff)
        adj = build_adjacency_matrix(atomic_numbers, coords, cutoff)
        expected_edges = np.sum(adj)

        assert len(src) == expected_edges
        assert len(tgt) == expected_edges
        assert len(dist) == expected_edges

    def test_distances_positive(self):
        """Test that all distances are positive."""
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0]
        ])
        atomic_numbers = np.array([1, 1])
        cutoff = 2.0

        src, tgt, dist = extract_edge_attributes(atomic_numbers, coords, cutoff)
        assert np.all(dist > 0)

class TestConstructTransitionStateGraph:
    def test_basic_construction(self):
        """Test basic graph construction from a row."""
        row = pd.Series({
            'atomic_numbers': [6, 6, 1, 1],
            'coordinates': [
                [0.0, 0.0, 0.0],
                [1.5, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [1.5, 1.0, 0.0]
            ],
            'formal_charges': [0, 0, 0, 0],
            'energy_dft': -100.5,
            'barrier_height': 15.2,
            'reaction_id': 'test_001'
        })

        graph = construct_transition_state_graph(row)

        assert 'nodes' in graph
        assert 'edges' in graph
        assert 'metadata' in graph

        assert len(graph['nodes']['atomic_numbers']) == 4
        assert 'coordination_numbers' in graph['nodes']
        assert graph['metadata']['reaction_id'] == 'test_001'
        assert graph['metadata']['energy_dft'] == -100.5

    def test_default_formal_charges(self):
        """Test that missing formal charges default to zero."""
        row = pd.Series({
            'atomic_numbers': [1, 1],
            'coordinates': [[0.0, 0.0, 0.0], [1.5, 0.0, 0.0]],
            'energy_dft': -50.0,
            'barrier_height': 10.0,
            'reaction_id': 'test_002'
        })

        graph = construct_transition_state_graph(row)
        assert graph['nodes']['formal_charges'] == [0, 0]

    def test_transition_metal_detection(self):
        """Test detection of transition metals (Pd=46, Ni=28, Cu=29)."""
        # Test with Palladium (46)
        row = pd.Series({
            'atomic_numbers': [46, 1, 1],
            'coordinates': [[0.0, 0.0, 0.0], [1.5, 0.0, 0.0], [0.0, 1.5, 0.0]],
            'energy_dft': -200.0,
            'barrier_height': 20.0,
            'reaction_id': 'test_pd'
        })
        graph = construct_transition_state_graph(row)
        assert graph['metadata']['has_transition_metal'] is True

        # Test without transition metal
        row['atomic_numbers'] = [6, 1, 1]  # Carbon
        graph = construct_transition_state_graph(row)
        assert graph['metadata']['has_transition_metal'] is False

class TestFilterOutliers:
    def test_no_outliers(self):
        """Test filtering when no outliers exist."""
        graphs = [
            {
                'nodes': {'coordination_numbers': [2, 2, 3]},
                'metadata': {'reaction_id': 'test_1'}
            },
            {
                'nodes': {'coordination_numbers': [1, 2]},
                'metadata': {'reaction_id': 'test_2'}
            }
        ]

        clean, outliers = filter_outliers(graphs, threshold=6)
        assert len(clean) == 2
        assert len(outliers) == 0
        assert all(not g['metadata']['is_outlier'] for g in clean)

    def test_with_outliers(self):
        """Test filtering with outliers."""
        graphs = [
            {
                'nodes': {'coordination_numbers': [2, 2, 3]},
                'metadata': {'reaction_id': 'test_1'}
            },
            {
                'nodes': {'coordination_numbers': [7, 2]},  # 7 > 6
                'metadata': {'reaction_id': 'test_2'}
            }
        ]

        clean, outliers = filter_outliers(graphs, threshold=6)
        assert len(clean) == 1
        assert len(outliers) == 1
        assert outliers[0]['metadata']['reaction_id'] == 'test_2'
        assert outliers[0]['metadata']['is_outlier'] is True

    def test_boundary_condition(self):
        """Test that exactly threshold is not an outlier."""
        graphs = [
            {
                'nodes': {'coordination_numbers': [6, 6]},
                'metadata': {'reaction_id': 'test_boundary'}
            }
        ]

        clean, outliers = filter_outliers(graphs, threshold=6)
        assert len(clean) == 1
        assert len(outliers) == 0

class TestSaveGraphsToParquet:
    def test_save_and_load(self):
        """Test saving and reloading graphs from Parquet."""
        graphs = [
            {
                'nodes': {
                    'atomic_numbers': [1, 6],
                    'formal_charges': [0, 0],
                    'coordination_numbers': [1, 2]
                },
                'edges': {
                    'source': [0],
                    'target': [1],
                    'distances': [1.09]
                },
                'metadata': {
                    'reaction_id': 'test_save',
                    'n_atoms': 2,
                    'energy_dft': -50.0,
                    'barrier_height': 10.0,
                    'is_outlier': False,
                    'has_transition_metal': False
                }
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_graphs.parquet"
            save_graphs_to_parquet(graphs, output_path)

            assert output_path.exists()
            df = pq.read_table(output_path).to_pandas()
            assert len(df) == 1
            assert df['reaction_id'].iloc[0] == 'test_save'

    def test_empty_graphs(self):
        """Test saving empty list of graphs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_graphs.parquet"
            save_graphs_to_parquet([], output_path)
            assert output_path.exists()
            df = pq.read_table(output_path).to_pandas()
            assert len(df) == 0

class TestSaveMetadata:
    def test_save_metadata_file(self):
        """Test saving metadata to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metadata.json"
            save_metadata(
                clean_count=100,
                outlier_count=5,
                total_count=105,
                cutoff=3.5,
                output_path=output_path
            )

            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)

            assert data['total_graphs'] == 105
            assert data['clean_graphs'] == 100
            assert data['outlier_graphs'] == 5
            assert data['coordination_cutoff'] == 3.5