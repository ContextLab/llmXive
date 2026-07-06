"""
Unit tests for graph construction module.
"""
import numpy as np
import pytest

from src.data.graph_construction import (
    calculate_coordination_number,
    build_adjacency_matrix,
    extract_edge_attributes,
    construct_transition_state_graph,
    filter_outliers
)


class TestCalculateCoordinationNumber:
    def test_empty_input(self):
        positions = np.zeros((0, 3))
        atomic_numbers = np.array([])
        result = calculate_coordination_number(positions, atomic_numbers)
        assert result == []

    def test_single_atom(self):
        positions = np.array([[0.0, 0.0, 0.0]])
        atomic_numbers = np.array([1])
        result = calculate_coordination_number(positions, atomic_numbers)
        assert result == [0]

    def test_two_atoms_within_cutoff(self):
        positions = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
        atomic_numbers = np.array([1, 1])
        result = calculate_coordination_number(positions, atomic_numbers)
        assert result == [1, 1]

    def test_two_atoms_outside_cutoff(self):
        positions = np.array([[0.0, 0.0, 0.0], [5.0, 0.0, 0.0]])
        atomic_numbers = np.array([1, 1])
        result = calculate_coordination_number(positions, atomic_numbers)
        assert result == [0, 0]

    def test_triple_coordination(self):
        # Central atom with 3 neighbors
        positions = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [-2.0, 0.0, 0.0],
            [0.0, 2.0, 0.0]
        ])
        atomic_numbers = np.array([6, 1, 1, 1])
        result = calculate_coordination_number(positions, atomic_numbers)
        assert result[0] == 3  # Central atom has 3 neighbors
        assert all(r == 1 for r in result[1:])  # Hydrogens have 1 neighbor


class TestBuildAdjacencyMatrix:
    def test_empty_input(self):
        positions = np.zeros((0, 3))
        adj = build_adjacency_matrix(positions)
        assert adj.shape == (0, 0)

    def test_single_atom(self):
        positions = np.array([[0.0, 0.0, 0.0]])
        adj = build_adjacency_matrix(positions)
        assert adj.shape == (1, 1)
        assert adj[0, 0] == False

    def test_symmetric(self):
        positions = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
        adj = build_adjacency_matrix(positions)
        assert adj[0, 1] == adj[1, 0]

    def test_no_self_loops(self):
        positions = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
        adj = build_adjacency_matrix(positions)
        assert not np.any(np.diag(adj))


class TestConstructTransitionStateGraph:
    def test_valid_reaction(self):
        row = {
            "atomic_numbers": [6, 1, 1, 1],
            "positions": [
                [0.0, 0.0, 0.0],
                [2.0, 0.0, 0.0],
                [-2.0, 0.0, 0.0],
                [0.0, 2.0, 0.0]
            ],
            "energy_dft": -100.5,
            "barrier_height": 15.2,
            "reaction_id": "test_001",
            "ligand_class": "Group 13"
        }
        graph = construct_transition_state_graph(row)

        assert graph is not None
        assert graph["reaction_id"] == "test_001"
        assert graph["energy_dft"] == -100.5
        assert graph["barrier_height"] == 15.2
        assert graph["ligand_class"] == "Group 13"
        assert graph["num_atoms"] == 4
        assert len(graph["nodes"]) == 4
        assert len(graph["edges"]) > 0

    def test_empty_atomic_numbers(self):
        row = {
            "atomic_numbers": [],
            "positions": [],
            "energy_dft": 0.0,
            "barrier_height": 0.0,
            "reaction_id": "empty_001"
        }
        graph = construct_transition_state_graph(row)
        assert graph is None

    def test_invalid_position_dimensions(self):
        row = {
            "atomic_numbers": [6, 1],
            "positions": [[0.0, 0.0], [1.0, 1.0]],  # 2D instead of 3D
            "energy_dft": 0.0,
            "barrier_height": 0.0,
            "reaction_id": "bad_dim_001"
        }
        graph = construct_transition_state_graph(row)
        assert graph is None


class TestFilterOutliers:
    def test_no_outliers(self):
        graphs = [
            {"max_coordination": 3},
            {"max_coordination": 4},
            {"max_coordination": 5}
        ]
        training, test = filter_outliers(graphs)
        assert len(training) == 3
        assert len(test) == 0

    def test_with_outliers(self):
        graphs = [
            {"max_coordination": 3},
            {"max_coordination": 7},
            {"max_coordination": 5},
            {"max_coordination": 8}
        ]
        training, test = filter_outliers(graphs)
        assert len(training) == 2
        assert len(test) == 2
        assert all(g["max_coordination"] <= 6 for g in training)
        assert all(g["max_coordination"] > 6 for g in test)