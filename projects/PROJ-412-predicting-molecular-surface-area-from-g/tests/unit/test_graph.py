"""
Unit tests for the Graph data model.
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data_models.graph import Graph


class TestGraphValidation:
    """Tests for Graph validation method."""
    
    def test_valid_graph(self):
        """Test validation of a correctly formed graph."""
        nodes = [0, 1, 2]
        edges = [(0, 1), (1, 2)]
        node_features = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        edge_features = np.array([[0.5, 0.3], [0.7, 0.2]])
        adjacency_matrix = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        
        graph = Graph(
            nodes=nodes,
            edges=edges,
            node_features=node_features,
            edge_features=edge_features,
            adjacency_matrix=adjacency_matrix
        )
        
        assert graph.validate() is True
    
    def test_missing_node_features(self):
        """Test that missing node_features raises ValueError."""
        graph = Graph(
            nodes=[0, 1],
            edges=[(0, 1)],
            node_features=None,
            edge_features=np.array([[0.5]]),
            adjacency_matrix=np.array([[0, 1], [1, 0]])
        )
        
        with pytest.raises(ValueError, match="node_features must be provided"):
            graph.validate()
    
    def test_missing_edge_features(self):
        """Test that missing edge_features raises ValueError."""
        graph = Graph(
            nodes=[0, 1],
            edges=[(0, 1)],
            node_features=np.array([[1.0], [2.0]]),
            edge_features=None,
            adjacency_matrix=np.array([[0, 1], [1, 0]])
        )
        
        with pytest.raises(ValueError, match="edge_features must be provided"):
            graph.validate()
    
    def test_missing_adjacency_matrix(self):
        """Test that missing adjacency_matrix raises ValueError."""
        graph = Graph(
            nodes=[0, 1],
            edges=[(0, 1)],
            node_features=np.array([[1.0], [2.0]]),
            edge_features=np.array([[0.5]]),
            adjacency_matrix=None
        )
        
        with pytest.raises(ValueError, match="adjacency_matrix must be provided"):
            graph.validate()
    
    def test_node_feature_count_mismatch(self):
        """Test that node count mismatch raises ValueError."""
        graph = Graph(
            nodes=[0, 1, 2],
            edges=[(0, 1)],
            node_features=np.array([[1.0], [2.0]]),  # Only 2 rows for 3 nodes
            edge_features=np.array([[0.5]]),
            adjacency_matrix=np.array([
                [0, 1, 0],
                [1, 0, 1],
                [0, 1, 0]
            ])
        )
        
        with pytest.raises(ValueError, match="Node count mismatch"):
            graph.validate()
    
    def test_edge_feature_count_mismatch(self):
        """Test that edge count mismatch raises ValueError."""
        graph = Graph(
            nodes=[0, 1],
            edges=[(0, 1), (1, 0)],
            node_features=np.array([[1.0], [2.0]]),
            edge_features=np.array([[0.5]]),  # Only 1 row for 2 edges
            adjacency_matrix=np.array([
                [0, 1],
                [1, 0]
            ])
        )
        
        with pytest.raises(ValueError, match="Edge count mismatch"):
            graph.validate()
    
    def test_adjacency_matrix_shape_mismatch(self):
        """Test that adjacency matrix shape mismatch raises ValueError."""
        graph = Graph(
            nodes=[0, 1, 2],
            edges=[(0, 1)],
            node_features=np.array([[1.0], [2.0], [3.0]]),
            edge_features=np.array([[0.5]]),
            adjacency_matrix=np.array([
                [0, 1],
                [1, 0]
            ])  # 2x2 instead of 3x3
        )
        
        with pytest.raises(ValueError, match="Adjacency matrix shape mismatch"):
            graph.validate()


class TestGraphToPyG:
    """Tests for Graph.to_pyg_format method."""
    
    def test_to_pyg_format(self):
        """Test conversion to PyTorch Geometric format."""
        try:
            import torch
            from torch_geometric.data import Data
        except ImportError:
            pytest.skip("PyTorch Geometric not installed")
        
        nodes = [0, 1, 2]
        edges = [(0, 1), (1, 2)]
        node_features = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        edge_features = np.array([[0.5, 0.3], [0.7, 0.2]])
        adjacency_matrix = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        
        graph = Graph(
            nodes=nodes,
            edges=edges,
            node_features=node_features,
            edge_features=edge_features,
            adjacency_matrix=adjacency_matrix
        )
        
        pyg_data = graph.to_pyg_format()
        
        assert isinstance(pyg_data, Data)
        assert pyg_data.x.shape == (3, 2)  # 3 nodes, 2 features
        assert pyg_data.edge_index.shape == (2, 2)  # 2 edges
        assert pyg_data.edge_attr.shape == (2, 2)  # 2 edges, 2 features
        
        # Verify edge_index values
        expected_edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)
        assert torch.equal(pyg_data.edge_index, expected_edge_index)
        
        # Verify node features
        expected_x = torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], dtype=torch.float)
        assert torch.allclose(pyg_data.x, expected_x)
        
        # Verify edge features
        expected_edge_attr = torch.tensor([[0.5, 0.3], [0.7, 0.2]], dtype=torch.float)
        assert torch.allclose(pyg_data.edge_attr, expected_edge_attr)
    
    def test_to_pyg_format_with_single_node(self):
        """Test conversion with a single node graph."""
        try:
            import torch
            from torch_geometric.data import Data
        except ImportError:
            pytest.skip("PyTorch Geometric not installed")
        
        nodes = [0]
        edges = []
        node_features = np.array([[1.0, 2.0]])
        edge_features = np.array([]).reshape(0, 2)
        adjacency_matrix = np.array([[0]])
        
        graph = Graph(
            nodes=nodes,
            edges=edges,
            node_features=node_features,
            edge_features=edge_features,
            adjacency_matrix=adjacency_matrix
        )
        
        pyg_data = graph.to_pyg_format()
        
        assert isinstance(pyg_data, Data)
        assert pyg_data.x.shape == (1, 2)
        assert pyg_data.edge_index.shape == (2, 0)
        assert pyg_data.edge_attr.shape == (0, 2)