import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
from typing import Tuple, Optional

class LightweightGNN(nn.Module):
    """Lightweight GNN for elastic moduli prediction.
    
    This model is a SURROGATE for DFT calculations, interpolating pre-computed
    elastic tensor data. It does NOT solve the Schrödinger equation or perform
    first-principles calculations.
    
    Architecture:
    - 2-3 GCN layers
    - Hidden dimension ≤ 64 (CPU-optimized)
    - Global mean pooling for graph-level representation
    - Output: 6-component elastic tensor (Voigt notation)
    """
    
    def __init__(self, node_dim: int, hidden_dim: int = 64, num_layers: int = 2):
        """Initialize the lightweight GNN.
        
        Args:
            node_dim: Dimension of node features
            hidden_dim: Hidden layer dimension (default 64, CPU-optimized)
            num_layers: Number of GCN layers (default 2, range 2-3)
        """
        if num_layers < 2 or num_layers > 3:
            raise ValueError("num_layers must be 2 or 3 for lightweight architecture")
        if hidden_dim > 64:
            raise ValueError("hidden_dim must be ≤ 64 for CPU-optimized model")
            
        super().__init__()
        
        # First convolution layer
        self.conv1 = GCNConv(node_dim, hidden_dim)
        
        # Additional convolution layers (0 or 1 based on num_layers)
        self.convs = nn.ModuleList([
            GCNConv(hidden_dim, hidden_dim) for _ in range(num_layers - 1)
        ])
        
        # Output layer: 6 elastic tensor components (Voigt notation)
        self.lin = nn.Linear(hidden_dim, 6)
        
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        """Forward pass through the GNN.
        
        Args:
            x: Node feature tensor [num_nodes, node_dim]
            edge_index: Edge index tensor [2, num_edges]
            batch: Batch assignment tensor [num_nodes]
            
        Returns:
            Predicted elastic tensor components [num_graphs, 6]
        """
        # First convolution with ReLU activation
        x = F.relu(self.conv1(x, edge_index))
        
        # Additional convolution layers
        for conv in self.convs:
            x = F.relu(conv(x, edge_index))
        
        # Global mean pooling to get graph-level representation
        x = global_mean_pool(x, batch)
        
        # Output layer for 6 elastic tensor components
        return self.lin(x)

def create_model(node_dim: int, hidden_dim: int = 64, num_layers: int = 2) -> LightweightGNN:
    """Create a lightweight GNN model for elastic moduli prediction.
    
    This factory function ensures the model adheres to CPU-optimized constraints
    (hidden_dim ≤ 64, 2-3 layers) as specified in the project requirements.
    
    Args:
        node_dim: Dimension of input node features
        hidden_dim: Hidden layer dimension (must be ≤ 64)
        num_layers: Number of GCN layers (must be 2 or 3)
        
    Returns:
        Configured LightweightGNN model instance
        
    Raises:
        ValueError: If hidden_dim > 64 or num_layers not in [2, 3]
    """
    return LightweightGNN(node_dim, hidden_dim, num_layers)