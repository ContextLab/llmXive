"""
Unit tests for graph_builder.py functionality.
"""
import json
import os
import tempfile
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Import the module under test
# Adjust import path if running from project root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingest.graph_builder import build_graph_from_xyz, calculate_node_degree_stats, process_directory
from code.ingest.node_degree_stats_generator import compute_mode_and_stats, load_graphs
from code.config import get_paths


class TestBondCutoffLogic:
    """Tests for bond cutoff logic (3.0 Å) - T011"""

    def test_edges_within_cutoff(self):
        """Verify edges are created for atoms within 3.0 Å"""
        # Create a temporary XYZ file with two atoms at 2.5 Å distance
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("2\n")
            f.write("Test structure\n")
            f.write("Si 0.0 0.0 0.0\n")
            f.write("Si 2.5 0.0 0.0\n")
            xyz_path = f.name

        try:
            graph = build_graph_from_xyz(xyz_path, cutoff=3.0)
            # Should have exactly one edge
            assert len(graph['edges']) == 1
            # Verify the edge connects the two atoms
            assert (0, 1) in graph['edges'] or (1, 0) in graph['edges']
        finally:
            os.unlink(xyz_path)

    def test_no_edges_beyond_cutoff(self):
        """Verify no edges are created for atoms beyond 3.0 Å"""
        # Create a temporary XYZ file with two atoms at 3.5 Å distance
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("2\n")
            f.write("Test structure\n")
            f.write("Si 0.0 0.0 0.0\n")
            f.write("Si 3.5 0.0 0.0\n")
            xyz_path = f.name

        try:
            graph = build_graph_from_xyz(xyz_path, cutoff=3.0)
            # Should have no edges
            assert len(graph['edges']) == 0
        finally:
            os.unlink(xyz_path)

    def test_mixed_cutoff_behavior(self):
        """Verify correct handling of mixed distances"""
        # Create a temporary XYZ file with 3 atoms
        # Atom 0-1: 2.0 Å (should connect)
        # Atom 0-2: 3.5 Å (should not connect)
        # Atom 1-2: 2.5 Å (should connect)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("3\n")
            f.write("Test structure\n")
            f.write("Si 0.0 0.0 0.0\n")
            f.write("Si 2.0 0.0 0.0\n")
            f.write("Si 0.0 3.5 0.0\n")
            xyz_path = f.name

        try:
            graph = build_graph_from_xyz(xyz_path, cutoff=3.0)
            # Should have exactly 2 edges: (0,1) and (1,2)
            assert len(graph['edges']) == 2
            edge_set = {tuple(sorted(e)) for e in graph['edges']}
            assert (0, 1) in edge_set
            assert (1, 2) in edge_set
            assert (0, 2) not in edge_set
        finally:
            os.unlink(xyz_path)


class TestNodeDegreeStats:
    """Tests for node-degree stats output - T016b"""

    def test_node_degree_stats_schema_exists(self):
        """
        Verify that calculate_node_degree_stats produces output matching the expected schema.
        The output file 'node_degree_stats.json' must contain:
        - mode: integer (most common degree)
        - distribution: dict mapping degree -> count
        - mean: float
        - std: float
        - min: int
        - max: int
        - total_nodes: int
        - total_edges: int
        """
        # Create a temporary directory with a simple graph
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple graph with known degree distribution
            # 4 nodes: degrees [3, 3, 3, 3] (complete graph K4)
            graph_data = {
                'nodes': [0, 1, 2, 3],
                'edges': [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
                'metadata': {'sample_id': 'test_001'}
            }
            
            # Save graph
            graph_path = Path(tmpdir) / "test_graph.pkl"
            with open(graph_path, 'wb') as f:
                pickle.dump(graph_data, f)
            
            # Calculate stats
            stats = calculate_node_degree_stats([str(graph_path)])
            
            # Verify schema structure
            assert isinstance(stats, dict)
            assert 'mode' in stats
            assert 'distribution' in stats
            assert 'mean' in stats
            assert 'std' in stats
            assert 'min' in stats
            assert 'max' in stats
            assert 'total_nodes' in stats
            assert 'total_edges' in stats
            
            # Verify types
            assert isinstance(stats['mode'], int)
            assert isinstance(stats['distribution'], dict)
            assert isinstance(stats['mean'], float)
            assert isinstance(stats['std'], float)
            assert isinstance(stats['min'], int)
            assert isinstance(stats['max'], int)
            assert isinstance(stats['total_nodes'], int)
            assert isinstance(stats['total_edges'], int)
            
            # Verify values for K4 graph
            assert stats['total_nodes'] == 4
            assert stats['total_edges'] == 6
            assert stats['mode'] == 3  # All nodes have degree 3
            assert stats['min'] == 3
            assert stats['max'] == 3
            assert stats['mean'] == 3.0
            assert stats['std'] == 0.0
            assert stats['distribution'] == {3: 4}

    def test_node_degree_stats_output_file(self):
        """
        Verify that process_directory generates the node_degree_stats.json file
        at the expected location with valid content.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory structure
            graphs_dir = Path(tmpdir) / "graphs"
            graphs_dir.mkdir()
            
            # Create a simple graph
            graph_data = {
                'nodes': [0, 1, 2],
                'edges': [(0, 1), (1, 2)],
                'metadata': {'sample_id': 'test_002'}
            }
            
            graph_path = graphs_dir / "test_graph.pkl"
            with open(graph_path, 'wb') as f:
                pickle.dump(graph_data, f)
            
            # Run process_directory
            stats_output_path = process_directory(str(graphs_dir))
            
            # Verify output file exists
            assert stats_output_path.exists()
            assert stats_output_path.name == "node_degree_stats.json"
            
            # Verify JSON content
            with open(stats_output_path, 'r') as f:
                stats = json.load(f)
            
            # Verify schema
            assert 'mode' in stats
            assert 'distribution' in stats
            assert isinstance(stats['mode'], int)
            assert isinstance(stats['distribution'], dict)
            
            # For a path graph 0-1-2: degrees are [1, 2, 1]
            # Mode should be 1 (appears twice)
            assert stats['mode'] == 1
            assert stats['total_nodes'] == 3
            assert stats['total_edges'] == 2

    def test_node_degree_stats_empty_graphs(self):
        """Verify handling of empty graph directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphs_dir = Path(tmpdir) / "graphs"
            graphs_dir.mkdir()
            
            # No graphs in directory
            stats_output_path = process_directory(str(graphs_dir))
            
            # Should still create output file with zero stats
            assert stats_output_path.exists()
            
            with open(stats_output_path, 'r') as f:
                stats = json.load(f)
            
            assert stats['total_nodes'] == 0
            assert stats['total_edges'] == 0
            assert stats['mode'] == 0
            assert stats['distribution'] == {}

    def test_node_degree_stats_range_validation(self):
        """
        Verify that the mode falls within expected range for amorphous silicon.
        Amorphous silicon typically has coordination numbers between 3-5.
        This test dynamically validates the range without hardcoding target values.
        """
        # Create a graph with realistic amorphous silicon-like coordination
        with tempfile.TemporaryDirectory() as tmpdir:
            graphs_dir = Path(tmpdir) / "graphs"
            graphs_dir.mkdir()
            
            # Create multiple graphs with coordination numbers 3-5
            for i in range(3):
                # Create a graph with mixed coordination
                nodes = list(range(10))
                edges = []
                
                # Create a mix of coordination numbers
                # Some atoms with degree 3, some with 4, some with 5
                for j in range(10):
                    if j < 3:
                        # Degree 3
                        for k in range(3):
                            if k != j:
                                edges.append((j, k))
                    elif j < 6:
                        # Degree 4
                        for k in range(4):
                            if k != j and k < 6:
                                edges.append((j, k))
                    else:
                        # Degree 5
                        for k in range(5):
                            if k != j and k < 6:
                                edges.append((j, k))
                
                graph_data = {
                    'nodes': nodes,
                    'edges': list(set(tuple(sorted(e)) for e in edges)),
                    'metadata': {'sample_id': f'test_{i}'}
                }
                
                graph_path = graphs_dir / f"graph_{i}.pkl"
                with open(graph_path, 'wb') as f:
                    pickle.dump(graph_data, f)
            
            stats_output_path = process_directory(str(graphs_dir))
            
            with open(stats_output_path, 'r') as f:
                stats = json.load(f)
            
            # Verify mode is in reasonable range (3-5 for amorphous silicon)
            assert 3 <= stats['mode'] <= 5, f"Mode {stats['mode']} outside expected range for amorphous silicon"


class TestGraphBuilderIntegration:
    """Integration tests for graph builder functionality"""

    def test_process_directory_with_realistic_structure(self):
        """Test processing a directory with realistic amorphous silicon structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphs_dir = Path(tmpdir) / "graphs"
            graphs_dir.mkdir()
            
            # Create a more realistic amorphous silicon graph
            # Based on typical coordination: mostly 4, some 3 and 5
            nodes = list(range(50))
            edges = []
            
            # Simulate realistic coordination distribution
            np.random.seed(42)
            degrees = np.random.choice([3, 4, 5], size=50, p=[0.1, 0.8, 0.1])
            
            # Create edges to match degree distribution
            edge_pool = []
            for i, target_degree in enumerate(degrees):
                # Add edges to reach target degree
                for j in range(i + 1, len(nodes)):
                    if len([e for e in edge_pool if i in e]) >= target_degree:
                        break
                    if len([e for e in edge_pool if j in e]) >= degrees[j]:
                        continue
                    edge_pool.append((i, j))
            
            graph_data = {
                'nodes': nodes,
                'edges': edge_pool,
                'metadata': {'sample_id': 'realistic_amorphous'}
            }
            
            graph_path = graphs_dir / "realistic_graph.pkl"
            with open(graph_path, 'wb') as f:
                pickle.dump(graph_data, f)
            
            # Process directory
            stats_output_path = process_directory(str(graphs_dir))
            
            # Verify output
            assert stats_output_path.exists()
            
            with open(stats_output_path, 'r') as f:
                stats = json.load(f)
            
            # Verify key metrics
            assert stats['total_nodes'] == 50
            assert stats['mode'] >= 3 and stats['mode'] <= 5
            assert stats['mean'] >= 3.0 and stats['mean'] <= 5.0
            assert stats['min'] >= 2  # Minimum reasonable coordination
            assert stats['max'] <= 6  # Maximum reasonable coordination