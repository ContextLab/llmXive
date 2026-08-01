"""
Unit tests for graph_construction.py
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
    def test_simple_molecule(self):
        # Methane: C at center, 4 H at ~1.09 A
        positions = np.array([
            [0.0, 0.0, 0.0],
            [1.09, 0.0, 0.0],
            [-0.36, 1.03, 0.0],
            [-0.36, -0.52, 0.94],
            [-0.36, -0.52, -0.94]
        ])
        atomic_numbers = [6, 1, 1, 1, 1]
        cutoff = 1.5  # Sufficient to catch bonds in methane

        coords = calculate_coordination_number(positions, atomic_numbers, cutoff)

        # Carbon should have 4 neighbors, H should have 1
        assert coords[0] == 4
        assert all(c == 1 for c in coords[1:])

    def test_no_bonds(self):
        # Atoms far apart
        positions = np.array([
            [0.0, 0.0, 0.0],
            [10.0, 10.0, 10.0]
        ])
        atomic_numbers = [6, 1]
        cutoff = 2.0

        coords = calculate_coordination_number(positions, atomic_numbers, cutoff)
        assert coords == [0, 0]

    def test_self_exclusion(self):
        # Atom should not count itself
        positions = np.array([[0.0, 0.0, 0.0]])
        atomic_numbers = [6]
        cutoff = 5.0

        coords = calculate_coordination_number(positions, atomic_numbers, cutoff)
        assert coords[0] == 0


class TestBuildAdjacencyMatrix:
    def test_symmetric(self):
        positions = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [5.0, 5.0, 5.0]
        ])
        adj = build_adjacency_matrix(positions, cutoff=2.0)

        assert adj[0, 1] == True
        assert adj[1, 0] == True
        assert adj[0, 2] == False
        assert adj[2, 0] == False
        assert adj[1, 2] == False
        assert adj[2, 1] == False
        assert np.all(np.diag(adj) == False)

    def test_cutoff_precision(self):
        positions = np.array([
            [0.0, 0.0, 0.0],
            [2.5, 0.0, 0.0],
            [2.51, 0.0, 0.0]
        ])
        adj = build_adjacency_matrix(positions, cutoff=2.5)

        assert adj[0, 1] == True
        assert adj[0, 2] == False


class TestConstructTransitionStateGraph:
    def test_basic_structure(self):
        positions = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0]
        ])
        graph = construct_transition_state_graph(
            atom_symbols=['C', 'H'],
            positions=positions,
            formal_charges=[0, 0],
            energy_dft=-100.0,
            barrier_height=15.0,
            ligand_class='Group 13',
            reaction_id='rxn_001'
        )

        assert 'nodes' in graph
        assert 'edges' in graph
        assert 'metadata' in graph

        assert len(graph['nodes']) == 2
        assert graph['nodes'][0]['atomic_number'] == 6
        assert graph['nodes'][0]['formal_charge'] == 0
        assert 'coordination_number' in graph['nodes'][0]

        assert graph['metadata']['energy_dft'] == -100.0
        assert graph['metadata']['barrier_height'] == 15.0
        assert graph['metadata']['ligand_class'] == 'Group 13'
        assert graph['metadata']['reaction_id'] == 'rxn_001'

    def test_default_formal_charges(self):
        positions = np.array([[0.0, 0.0, 0.0]])
        graph = construct_transition_state_graph(
            atom_symbols=['C'],
            positions=positions
        )
        assert graph['nodes'][0]['formal_charge'] == 0


class TestFilterOutliers:
    def test_no_outliers(self):
        graphs = [
            {'nodes': [{'coordination_number': 4}, {'coordination_number': 1}], 'metadata': {}},
            {'nodes': [{'coordination_number': 3}, {'coordination_number': 3}], 'metadata': {}}
        ]
        valid, outliers = filter_outliers(graphs, max_coordination=6)
        assert len(valid) == 2
        assert len(outliers) == 0

    def test_has_outliers(self):
        graphs = [
            {'nodes': [{'coordination_number': 4}, {'coordination_number': 1}], 'metadata': {}},
            {'nodes': [{'coordination_number': 7}, {'coordination_number': 1}], 'metadata': {}},
            {'nodes': [{'coordination_number': 6}, {'coordination_number': 6}], 'metadata': {}}
        ]
        valid, outliers = filter_outliers(graphs, max_coordination=6)
        assert len(valid) == 2
        assert len(outliers) == 1
        assert outliers[0]['nodes'][0]['coordination_number'] == 7

    def test_empty_list(self):
        valid, outliers = filter_outliers([], max_coordination=6)
        assert len(valid) == 0
        assert len(outliers) == 0


class TestSaveGraphsToParquet:
    def test_save_and_load(self):
        graphs = [
            {
                'nodes': [{'atomic_number': 6, 'formal_charge': 0, 'coordination_number': 4, 'symbol': 'C'}],
                'edges': [],
                'metadata': {'energy_dft': -100.0, 'reaction_id': 'rxn_001'}
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_graphs.parquet"
            save_graphs_to_parquet(graphs, path)

            assert path.exists()

            import pandas as pd
            df = pd.read_parquet(path)
            assert len(df) == 1
            assert df.iloc[0]['metadata']['energy_dft'] == -100.0

class TestSaveMetadata:
    def test_save_outlier_metadata(self):
        outliers = [
            {'metadata': {'reaction_id': 'rxn_bad'}},
            {'metadata': {'reaction_id': 'rxn_bad2'}}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "outliers.json"
            save_metadata(outliers, path)

            assert path.exists()
            with open(path) as f:
                data = json.load(f)

            assert data['n_outliers'] == 2
            assert 'sample_reaction_ids' in data