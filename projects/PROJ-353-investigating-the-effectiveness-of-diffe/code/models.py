"""
Graph Convolutional Network (GCN) implementations for node classification.
Implements a 2-layer GCN architecture, CPU-only as per project constraints.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric import sparse
from typing import Optional
import math

# Import constants from utils to ensure consistency with project specs
# Note: Convergence threshold and max epochs are defined in utils.py
# We import them here for reference if needed in training logic
from utils import seed_all, hash_artifact, CONVERGENCE_THRESHOLD, MAX_EPOCHS, SAMPLE_SIZE


class GCNLayer(nn.Module):
    """
    A single Graph Convolutional Network layer.
    Performs: H' = D^{-1/2} R D^{-1/2} X W
    """
    def __init__(self, in_features: int, out_features: int, bias: bool = False):
        super(GCNLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.linear = nn.Linear(in_features, out_features, bias=bias)

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        """
        Forward pass:
        Args:
            x: Node feature matrix [N, in_features]
            adj_norm: Normalized adjacency matrix (D^{-1/2} R D^{-1/2}) [N, N]
        Returns:
            Feature matrix after GCN operation [N, out_features]
        """
        # Graph convolution: H' = R_norm * X * W
        h = torch.matmul(adj_norm, x)
        h = self.linear(h)
        return h


class GCN2Layer(nn.Module):
    """
    A 2-layer Graph Convolutional Network for node classification.
    Architecture: Input -> GCN1 -> ReLU -> GCN2 -> (Softmax)
    Designed for CPU-only training as per project constraints.
    """
    def __init__(self, in_features: int, hidden_features: int, out_features: int, dropout: float = 0.1):
        super(GCN2Layer, self).__init__()
        
        self.gcn1 = GCNLayer(in_features, hidden_features, bias=True)
        self.gcn2 = GCNLayer(hidden_features, out_features, bias=True)
        
        self.dropout = nn.Dropout(dropout)
        
        # Initialize weights using Xavier initialization
        self._init_weights()

    def _init_weights(self):
        """Initialize weights with Xavier initialization."""
        for param in self.parameters():
            if param.dim() > 1:
                nn.init.xavier_uniform_(param, std=0.1)

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the 2-layer GCN.
        
        Args:
            x: Node feature matrix [N, in_features]
            adj_norm: Normalized adjacency matrix [N, N]
        
        Returns:
            Logits for node classification [N, out_features]
        """
        # First GCN layer with ReLU activation
        h = self.gcn1(x, adj_norm)
        h = F.relu(h)
        h = self.dropout(h)
        
        # Second GCN layer (output layer, no activation here - caller applies Softmax/CrossEntropy)
        out = self.gcn2(h, adj_norm)
        return out

    def get_params(self):
        """Return model parameters for optimizer."""
        return self.parameters()


def create_normalized_adjacency(edge_index: torch.Tensor, num_nodes: int) -> torch.Tensor:
    """
    Create the normalized adjacency matrix D^{-1/2} R D^{-1/2}.
    
    Args:
        edge_index: Edge list in COO format [2, num_edges]
        num_nodes: Number of nodes in the graph
    
    Returns:
        Normalized adjacency matrix [num_nodes, num_nodes]
    """
    # Create sparse adjacency matrix
    row, col = edge_index
    adj = torch.sparse_coo_tensor(
        torch.stack([row, col]),
        torch.ones(edge_index.size(1)),
        size=(num_nodes, num_nodes)
    )
    
    # Add self-loops
    loop_index = torch.arange(num_nodes, dtype=torch.long)
    adj = adj + torch.sparse_coo_tensor(
        torch.stack([loop_index, loop_index]),
        torch.ones(num_nodes),
        size=(num_nodes, num_nodes)
    )
    
    # Compute degree matrix
    degrees = adj.sum(dim=1).to_dense()
    degrees_inv_sqrt = torch.pow(degrees, -0.5)
    degrees_inv_sqrt[torch.isinf(degrees_inv_sqrt)] = 0.0
    
    # Create diagonal matrix of inverse sqrt degrees
    deg_inv_sqrt_diag = torch.diag(degrees_inv_sqrt)
    
    # Normalize: D^{-1/2} R D^{-1/2}
    adj_norm = deg_inv_sqrt_diag @ adj.to_dense() @ deg_inv_sqrt_diag
    
    return adj_norm


def build_gcn_model(graph_features: int, num_classes: int, hidden_dim: int = 16) -> GCN2Layer:
    """
    Factory function to build a GCN2Layer model with appropriate dimensions.
    
    Args:
        graph_features: Number of input features per node
        num_classes: Number of output classes
        hidden_dim: Hidden layer dimension (default 16 for small graphs)
    
    Returns:
        Initialized GCN2Layer model
    """
    model = GCN2Layer(
        in_features=graph_features,
        hidden_features=hidden_dim,
        out_features=num_classes
    )
    return model