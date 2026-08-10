"""
Graph data model for molecular representations.

This module defines the Graph class which represents a molecular graph
with nodes, edges, and associated features. It provides methods for
validation and conversion to PyTorch Geometric format.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class Graph:
    """
    Represents a molecular graph with nodes, edges, and features.
    
    Attributes:
        nodes: List of node identifiers (typically atom indices)
        edges: List of edge tuples (source, target)
        node_features: NumPy array of shape (num_nodes, num_node_features)
        edge_features: NumPy array of shape (num_edges, num_edge_features)
        adjacency_matrix: NumPy array of shape (num_nodes, num_nodes)
    """
    nodes: List[int] = field(default_factory=list)
    edges: List[tuple] = field(default_factory=list)
    node_features: Optional[np.ndarray] = None
    edge_features: Optional[np.ndarray] = None
    adjacency_matrix: Optional[np.ndarray] = None
    
    def validate(self) -> bool:
        """
        Validate the graph structure and feature consistency.
        
        Checks:
        - Node count matches node_features rows
        - Edge count matches edge_features rows
        - Adjacency matrix dimensions match node count
        - All required arrays are present
        
        Returns:
            bool: True if valid, raises ValueError otherwise
        """
        if self.node_features is None:
            raise ValueError("node_features must be provided")
        if self.edge_features is None:
            raise ValueError("edge_features must be provided")
        if self.adjacency_matrix is None:
            raise ValueError("adjacency_matrix must be provided")
        
        num_nodes = len(self.nodes)
        num_edges = len(self.edges)
        
        if self.node_features.shape[0] != num_nodes:
            raise ValueError(
                f"Node count mismatch: {num_nodes} nodes but "
                f"{self.node_features.shape[0]} node_features rows"
            )
        
        if self.edge_features.shape[0] != num_edges:
            raise ValueError(
                f"Edge count mismatch: {num_edges} edges but "
                f"{self.edge_features.shape[0]} edge_features rows"
            )
        
        if self.adjacency_matrix.shape != (num_nodes, num_nodes):
            raise ValueError(
                f"Adjacency matrix shape mismatch: expected "
                f"({num_nodes}, {num_nodes}), got {self.adjacency_matrix.shape}"
            )
        
        return True
    
    def to_pyg_format(self):
        """
        Convert the graph to PyTorch Geometric Data format.
        
        Returns:
            torch_geometric.data.Data: Graph object compatible with PyTorch Geometric
        """
        import torch
        from torch_geometric.data import Data
        
        # Convert node features to tensor
        x = torch.tensor(self.node_features, dtype=torch.float)
        
        # Convert edges to edge index format (2, num_edges)
        edge_index = torch.tensor(self.edges, dtype=torch.long).t().contiguous()
        
        # Convert edge features to tensor
        edge_attr = torch.tensor(self.edge_features, dtype=torch.float)
        
        # Create PyG Data object
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
        
        return data
