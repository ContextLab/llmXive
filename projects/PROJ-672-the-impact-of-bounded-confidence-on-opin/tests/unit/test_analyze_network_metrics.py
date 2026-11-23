"""
Unit tests for T013: analyze_network_metrics.py

Tests verify that:
1. Metrics are correctly calculated for known network structures
2. Output JSON files are created with correct structure
3. Edge cases (disconnected graphs) are handled appropriately
"""
import json
import tempfile
from pathlib import Path

import networkx as nx
import pytest

from analyze_network_metrics import (
    load_network_from_file,
    calculate_metrics_for_network,
    process_networks_directory,
)


@pytest.fixture
def sample_network():
    """Create a simple connected graph for testing."""
    G = nx.karate_club_graph()
    return G


@pytest.fixture
def sample_network_file(tmp_path, sample_network):
    """Save a sample network to a temporary file."""
    network_file = tmp_path / 'network_123.json'

    data = {
        'nodes': list(sample_network.nodes()),
        'edges': list(sample_network.edges())
    }

    with open(network_file, 'w') as f:
        json.dump(data, f)

    return network_file


class TestLoadNetworkFromFile:
    def test_load_valid_network(self, sample_network_file, sample_network):
        """Test loading a valid network from JSON file."""
        G = load_network_from_file(sample_network_file)

        assert G.number_of_nodes() == sample_network.number_of_nodes()
        assert G.number_of_edges() == sample_network.number_of_edges()
        assert set(G.nodes()) == set(sample_network.nodes())
        assert set(G.edges()) == set(sample_network.edges())

    def test_load_empty_network(self, tmp_path):
        """Test loading an empty network."""
        network_file = tmp_path / 'network_0.json'
        with open(network_file, 'w') as f:
            json.dump({'nodes': [], 'edges': []}, f)

        G = load_network_from_file(network_file)
        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0


class TestCalculateMetricsForNetwork:
    def test_metrics_structure(self, sample_network):
        """Test that metrics output has expected structure."""
        result = calculate_metrics_for_network(sample_network, seed=42)

        assert 'seed' in result
        assert 'num_nodes' in result
        assert 'num_edges' in result
        assert 'is_connected' in result
        assert 'assortativity' in result
        assert 'average_path_length' in result
        assert 'clustering_coefficient' in result
        assert 'density' in result
        assert 'diameter' in result

    def test_known_graph_properties(self):
        """Test metrics on a graph with known properties."""
        # Complete graph K5: diameter=1, clustering=1.0, density=1.0
        G = nx.complete_graph(5)
        result = calculate_metrics_for_network(G, seed=1)

        assert result['num_nodes'] == 5
        assert result['num_edges'] == 10
        assert result['is_connected'] is True
        assert result['diameter'] == 1
        assert result['clustering_coefficient'] == pytest.approx(1.0, rel=1e-6)
        assert result['density'] == pytest.approx(1.0, rel=1e-6)

    def test_disconnected_graph(self):
        """Test handling of disconnected graphs."""
        # Create two separate triangles
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])

        result = calculate_metrics_for_network(G, seed=2)

        assert result['is_connected'] is False
        assert result['diameter'] is None  # Undefined for disconnected graphs
        # Average path length should be finite (only within components)
        assert result['average_path_length'] is not None


class TestProcessNetworksDirectory:
    def test_process_multiple_networks(self, tmp_path):
        """Test processing multiple network files."""
        # Create sample network files
        for seed in [1, 2, 3]:
            G = nx.erdos_renyi_graph(20, 0.3, seed=seed)
            network_file = tmp_path / f'network_{seed}.json'
            with open(network_file, 'w') as f:
                json.dump({
                    'nodes': list(G.nodes()),
                    'edges': list(G.edges())
                }, f)

        output_dir = tmp_path / 'metrics_output'
        results = process_networks_directory(tmp_path, output_dir)

        assert len(results) == 3
        assert output_dir.exists()

        # Check that metrics files were created
        for seed in [1, 2, 3]:
            metrics_file = output_dir / f'metrics_{seed}.json'
            assert metrics_file.exists()

            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
                assert metrics['seed'] == seed

    def test_ignore_metrics_files(self, tmp_path):
        """Test that existing metrics files are not reprocessed as networks."""
        # Create a network file and a metrics file
        G = nx.erdos_renyi_graph(20, 0.3, seed=1)
        network_file = tmp_path / 'network_1.json'
        with open(network_file, 'w') as f:
            json.dump({'nodes': list(G.nodes()), 'edges': list(G.edges())}, f)

        # Create a metrics file that should be ignored
        metrics_file = tmp_path / 'metrics_1.json'
        with open(metrics_file, 'w') as f:
            json.dump({'seed': 1, 'assortativity': 0.5}, f)

        output_dir = tmp_path / 'metrics_output'
        results = process_networks_directory(tmp_path, output_dir)

        # Should only process the network file, not the metrics file
        assert len(results) == 1
        assert results[0]['seed'] == 1