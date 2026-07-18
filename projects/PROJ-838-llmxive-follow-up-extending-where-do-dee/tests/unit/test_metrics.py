import pytest
import networkx as nx
import json
import tempfile
import os
from pathlib import Path

from metrics import (
    calculate_global_connectivity,
    calculate_avg_branching_factor,
    load_graph_from_json
)


class TestCalculateGlobalConnectivity:
    def test_empty_graph(self):
        G = nx.DiGraph()
        assert calculate_global_connectivity(G) == 0.0

    def test_single_node(self):
        G = nx.DiGraph()
        G.add_node(1)
        assert calculate_global_connectivity(G) == 0.0

    def test_two_nodes_no_edge(self):
        G = nx.DiGraph()
        G.add_nodes_from([1, 2])
        assert calculate_global_connectivity(G) == 0.0

    def test_two_nodes_one_edge(self):
        G = nx.DiGraph()
        G.add_nodes_from([1, 2])
        G.add_edge(1, 2)
        # N=2, E=1, Max=2*1=2 -> 1/2 = 0.5
        assert calculate_global_connectivity(G) == 0.5

    def test_three_nodes_two_edges(self):
        G = nx.DiGraph()
        G.add_nodes_from([1, 2, 3])
        G.add_edges_from([(1, 2), (2, 3)])
        # N=3, E=2, Max=3*2=6 -> 2/6 = 0.333...
        expected = 2.0 / 6.0
        assert abs(calculate_global_connectivity(G) - expected) < 1e-6

    def test_complete_graph(self):
        G = nx.complete_graph(4, create_using=nx.DiGraph)
        # N=4, E=12, Max=4*3=12 -> 12/12 = 1.0
        assert calculate_global_connectivity(G) == 1.0


class TestCalculateAvgBranchingFactor:
    def test_empty_graph(self):
        G = nx.DiGraph()
        assert calculate_avg_branching_factor(G) == 0.0

    def test_single_node_no_edges(self):
        G = nx.DiGraph()
        G.add_node(1)
        # E=0, N=1 -> 0/1 = 0.0
        assert calculate_avg_branching_factor(G) == 0.0

    def test_two_nodes_one_edge(self):
        G = nx.DiGraph()
        G.add_nodes_from([1, 2])
        G.add_edge(1, 2)
        # E=1, N=2 -> 1/2 = 0.5
        assert calculate_avg_branching_factor(G) == 0.5

    def test_three_nodes_two_edges(self):
        G = nx.DiGraph()
        G.add_nodes_from([1, 2, 3])
        G.add_edges_from([(1, 2), (2, 3)])
        # E=2, N=3 -> 2/3 = 0.666...
        expected = 2.0 / 3.0
        assert abs(calculate_avg_branching_factor(G) - expected) < 1e-6

    def test_star_graph_center_out(self):
        G = nx.DiGraph()
        G.add_nodes_from([0, 1, 2, 3])
        G.add_edges_from([(0, 1), (0, 2), (0, 3)])
        # E=3, N=4 -> 3/4 = 0.75
        assert calculate_avg_branching_factor(G) == 0.75

    def test_star_graph_center_in(self):
        G = nx.DiGraph()
        G.add_nodes_from([0, 1, 2, 3])
        G.add_edges_from([(1, 0), (2, 0), (3, 0)])
        # E=3, N=4 -> 3/4 = 0.75
        assert calculate_avg_branching_factor(G) == 0.75


class TestLoadGraphFromJson:
    def test_load_custom_format(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "nodes": [1, 2, 3],
                "edges": [[1, 2], [2, 3]]
            }, f)
            temp_path = f.name

        try:
            G = load_graph_from_json(Path(temp_path))
            assert G.number_of_nodes() == 3
            assert G.number_of_edges() == 2
            assert G.has_edge(1, 2)
            assert G.has_edge(2, 3)
        finally:
            os.unlink(temp_path)

    def test_load_node_link_format(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
                "links": [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}]
            }, f)
            temp_path = f.name

        try:
            G = load_graph_from_json(Path(temp_path))
            assert G.number_of_nodes() == 3
            assert G.number_of_edges() == 2
            assert G.has_edge("A", "B")
            assert G.has_edge("B", "C")
        finally:
            os.unlink(temp_path)

    def test_load_edge_list_format(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([[1, 2], [2, 3]], f)
            temp_path = f.name

        try:
            G = load_graph_from_json(Path(temp_path))
            assert G.number_of_nodes() == 3
            assert G.number_of_edges() == 2
        finally:
            os.unlink(temp_path)