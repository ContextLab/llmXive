"""
Unit tests for the serialization module (T014).

These tests verify that:
1. Networks are correctly saved to GraphML.
2. Metrics are correctly saved to JSON.
3. Checksums are generated and match the file contents.
4. The serialization process handles disconnected graphs gracefully.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path

import pytest
import networkx as nx

# Import the module under test
from serialize_networks import (
    serialize_network_to_graphml,
    serialize_metrics_to_json,
    process_and_serialize_networks,
    calculate_sha256
)


def test_serialize_network_to_graphml():
    """Test that a network is correctly serialized to GraphML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = nx.erdos_renyi_graph(10, 0.5)
        output_path = Path(tmpdir) / "test.graphml"

        serialize_network_to_graphml(graph, output_path)

        assert output_path.exists()
        # Try to read it back to ensure validity
        loaded_graph = nx.read_graphml(str(output_path))
        assert nx.is_isomorphic(graph, loaded_graph)


def test_serialize_metrics_to_json():
    """Test that metrics are correctly serialized to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics = {
            "assortativity": 0.5,
            "path_length": 2.3,
            "clustering": 0.4
        }
        output_path = Path(tmpdir) / "metrics.json"

        serialize_metrics_to_json(metrics, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_metrics = json.load(f)
        assert loaded_metrics == metrics


def test_process_and_serialize_networks():
    """Test the full serialization pipeline for multiple networks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create a few dummy networks
        g1 = nx.erdos_renyi_graph(50, 0.1, seed=42)
        g2 = nx.barabasi_albert_graph(50, 3, seed=43)

        networks = [g1, g2]
        seeds = [42, 43]
        types = ['erdos_renyi', 'barabasi_albert']

        manifest = process_and_serialize_networks(
            networks=networks,
            seeds=seeds,
            topology_types=types,
            base_output_dir=base_dir
        )

        # Check manifest length
        assert len(manifest) == 2

        # Check that files exist and checksums match
        for entry in manifest:
            seed = entry['seed']
            graph_path = Path(entry['files']['graph']['path'])
            metrics_path = Path(entry['files']['metrics']['path'])

            assert graph_path.exists(), f"Graph file missing for seed {seed}"
            assert metrics_path.exists(), f"Metrics file missing for seed {seed}"

            # Verify checksums
            actual_graph_hash = calculate_sha256(graph_path)
            actual_metrics_hash = calculate_sha256(metrics_path)

            assert entry['files']['graph']['checksum'] == actual_graph_hash
            assert entry['files']['metrics']['checksum'] == actual_metrics_hash


def test_disconnected_graph_handling():
    """Test that disconnected graphs are handled (largest component used)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a disconnected graph
        g = nx.Graph()
        g.add_nodes_from(range(10))
        g.add_edges_from([(0, 1), (1, 2)]) # Component 1
        g.add_edges_from([(5, 6), (6, 7)]) # Component 2
        # Nodes 3, 4, 8, 9 are isolated

        networks = [g]
        seeds = [99]
        types = ['disconnected_test']

        manifest = process_and_serialize_networks(
            networks=networks,
            seeds=seeds,
            topology_types=types,
            base_output_dir=Path(tmpdir)
        )

        assert len(manifest) == 1
        metrics = manifest[0] # The manifest entry contains file paths, but we need to check the content
        
        # Find the metrics file path from the manifest
        # Note: process_and_serialize_networks returns the manifest list which contains checksums
        # We need to re-read the metrics file to check the 'is_connected' flag
        # The manifest entry structure:
        # { 'seed': ..., 'topology': ..., 'files': { 'graph': {...}, 'metrics': {...} } }
        # We need to load the metrics file content to verify the flag
        
        # Re-run logic to get the path or just check the file system
        # Since we know the naming convention: metrics_{seed}.json in metrics_dir
        metrics_path = Path(tmpdir) / "metrics" / "metrics_99.json"
        assert metrics_path.exists()

        with open(metrics_path, 'r') as f:
            saved_metrics = json.load(f)

        assert saved_metrics['is_connected'] is False
        assert saved_metrics['largest_component_size'] == 3 # Component (0,1,2) or (5,6,7)
        assert saved_metrics['total_nodes'] == 10

def test_checksum_consistency():
    """Test that checksums are deterministic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = nx.erdos_renyi_graph(20, 0.2, seed=123)
        path = Path(tmpdir) / "test.graphml"
        
        serialize_network_to_graphml(graph, path)
        hash1 = calculate_sha256(path)
        
        # Write again
        serialize_network_to_graphml(graph, path)
        hash2 = calculate_sha256(path)
        
        assert hash1 == hash2