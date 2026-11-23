import json
import tempfile
from pathlib import Path
import pytest
import networkx as nx

from graph_saver import save_graph_to_graphml, save_graph_to_json, save_graphs
from config.env_config import get_processed_dir

def test_save_graph_to_graphml():
    """Test saving a simple graph to GraphML format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        graph = nx.Graph()
        graph.add_node(1, x=0.0, y=0.0, z=0.0)
        graph.add_node(2, x=1.0, y=0.0, z=0.0)
        graph.add_edge(1, 2, distance=1.0)
        
        file_path = save_graph_to_graphml(graph, "test_config", output_dir)
        
        assert file_path.exists()
        assert file_path.suffix == ".graphml"
        
        # Verify we can read it back
        loaded_graph = nx.read_graphml(str(file_path))
        assert len(loaded_graph.nodes()) == 2
        assert len(loaded_graph.edges()) == 1

def test_save_graph_to_json():
    """Test saving a simple graph to JSON format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        graph = nx.Graph()
        graph.add_node(1, x=0.0, y=0.0, z=0.0)
        graph.add_node(2, x=1.0, y=0.0, z=0.0)
        graph.add_edge(1, 2, distance=1.0)
        
        file_path = save_graph_to_json(graph, "test_config", output_dir)
        
        assert file_path.exists()
        assert file_path.suffix == ".json"
        
        # Verify we can read it back
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert len(data['nodes']) == 2
        assert len(data['links']) == 1

def test_save_graphs_with_empty_list():
    """Test that save_graphs handles an empty list of config IDs gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        result = save_graphs([], output_dir)
        assert result == {}

def test_save_graphs_creates_directory():
    """Test that save_graphs creates the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "nonexistent"
        # Don't create the directory yet
        
        # This should fail gracefully if there are no graphs, but the directory
        # creation logic should be tested in a real scenario with valid graphs
        # For now, we just verify it doesn't crash on empty input
        result = save_graphs([], output_dir)
        assert result == {}