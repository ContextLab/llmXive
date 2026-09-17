import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import networkx as nx
import numpy as np
import pytest

from graph_saver import save_graph_to_graphml, save_graph_to_json, save_graphs
from models.atomic_config import AtomicConfiguration

class TestGraphSaver:
    @pytest.fixture
    def sample_graph(self):
        """Create a simple connected graph with attributes."""
        G = nx.Graph()
        G.add_node(0, x=1.0, y=2.0, z=3.0, type="Si")
        G.add_node(1, x=1.5, y=2.5, z=3.5, type="Si")
        G.add_edge(0, 1, distance=0.866, weight=1.0)
        G.add_edge(0, 0, distance=0.0) # Self loop edge case? No, simple graph usually. 
        # Let's add a triangle for connectivity check
        G.add_node(2, x=0.5, y=1.5, z=2.5, type="Si")
        G.add_edge(1, 2, distance=0.866, weight=1.0)
        G.add_edge(2, 0, distance=0.866, weight=1.0)
        
        # Add a set attribute to test serialization
        G.nodes[0]["neighbors"] = {1, 2}
        return G

    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_save_graphml(self, sample_graph, temp_output_dir):
        output_path = temp_output_dir / "test.graphml"
        save_graph_to_graphml(sample_graph, output_path)
        
        assert output_path.exists()
        
        # Verify it can be reloaded
        loaded_graph = nx.read_graphml(str(output_path))
        assert loaded_graph.number_of_nodes() == sample_graph.number_of_nodes()
        assert loaded_graph.number_of_edges() == sample_graph.number_of_edges()
        assert nx.is_connected(loaded_graph)

    def test_save_json(self, sample_graph, temp_output_dir):
        output_path = temp_output_dir / "test.json"
        save_graph_to_json(sample_graph, "config_001", output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["config_id"] == "config_001"
        assert data["num_nodes"] == 3
        assert data["num_edges"] == 3
        assert data["is_connected"] is True
        
        # Check serialization of set
        node_0 = next(n for n in data["nodes"] if n["id"] == 0)
        assert "neighbors" in node_0["attributes"]
        assert isinstance(node_0["attributes"]["neighbors"], list)

    def test_save_graphs_both_formats(self, sample_graph, temp_output_dir):
        graphs = {"config_001": sample_graph}
        
        with patch("graph_saver.get_processed_dir") as mock_get_dir:
            mock_get_dir.return_value = temp_output_dir
            
            saved_paths = save_graphs(graphs, output_dir=temp_output_dir, format_type="both")
            
            assert len(saved_paths) == 2
            assert any(p.suffix == ".graphml" for p in saved_paths)
            assert any(p.suffix == ".json" for p in saved_paths)
            
            # Verify files exist
            for p in saved_paths:
                assert p.exists()

    def test_save_graphs_np_array_serialization(self, temp_output_dir):
        G = nx.Graph()
        G.add_node(0, coords=np.array([1.0, 2.0, 3.0]))
        G.add_edge(0, 1, dist=np.array([0.5]))
        G.add_node(1)
        G.add_edge(0, 1)
        
        output_path_json = temp_output_dir / "test_np.json"
        save_graph_to_json(G, "config_np", output_path_json)
        
        assert output_path_json.exists()
        with open(output_path_json, 'r') as f:
            data = json.load(f)
        
        # Verify list conversion
        node_0 = next(n for n in data["nodes"] if n["id"] == 0)
        assert isinstance(node_0["attributes"]["coords"], list)
        assert node_0["attributes"]["coords"] == [1.0, 2.0, 3.0]