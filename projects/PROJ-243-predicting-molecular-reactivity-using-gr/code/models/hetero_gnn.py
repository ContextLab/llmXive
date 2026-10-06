"""
Heterophily-aware GNN architecture based on VR-GNN principles.
Designed for CPU-only execution.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops, degree
from typing import Optional, Tuple

try:
    from torch_geometric.nn import SAGEConv
except ImportError:
    # Fallback if SAGEConv is not available in older torch-geometric versions
    SAGEConv = None

class HeterophilyAggregation(MessagePassing):
    """
    Custom aggregation layer for heterophilic graphs.
    Implements a variation of VR-GNN (Virtual Reactor GNN) principles:
    - Separates same-type and different-type neighbor aggregation.
    - Uses adaptive weighting to handle heterophily.
    """
    def __init__(self, in_channels: int, out_channels: int, aggr: str = 'add'):
        super().__init__(aggr=aggr)
        self.in_channels = in_channels
        self.out_channels = out_channels

        # Linear transformations for source and target nodes
        self.lin_src = nn.Linear(in_channels, out_channels, bias=False)
        self.lin_dst = nn.Linear(in_channels, out_channels, bias=False)

        # Learnable parameter for heterophily adaptation
        # gamma controls the weight of the heterophilic message
        self.gamma = nn.Parameter(torch.ones(1))

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # x: [N, in_channels]
        # edge_index: [2, E]
        
        # Transform source and destination features
        x_src = self.lin_src(x)
        x_dst = self.lin_dst(x)

        # Propagate messages
        out = self.propagate(edge_index, x=(x_src, x_dst), size=(x.size(0), x.size(0)))
        
        # Add self-loop contribution (homophilic part)
        # In VR-GNN style, we often add a residual or skip connection
        out = out + x_dst

        # Apply non-linearity
        out = F.relu(out)
        
        return out

    def message(self, x_j: torch.Tensor, x_i: torch.Tensor, edge_index_i: torch.Tensor) -> torch.Tensor:
        """
        x_j: Source node features
        x_i: Target node features
        """
        # Compute heterophilic message: difference between source and target
        # This captures information flow across different types (heterophily)
        diff = x_j - x_i
        
        # Weighted combination of standard message and heterophilic message
        # Standard message: just x_j
        # Heterophilic message: diff * gamma
        msg = x_j + (self.gamma * diff)
        
        return msg

    def update(self, aggr_out: torch.Tensor) -> torch.Tensor:
        return aggr_out


class HeteroGNNLayer(nn.Module):
    """
    A single layer of the Heterophily-aware GNN.
    Combines standard message passing with heterophily-aware aggregation.
    """
    def __init__(self, in_channels: int, out_channels: int, dropout: float = 0.1):
        super().__init__()
        self.aggregation = HeterophilyAggregation(in_channels, out_channels)
        self.batch_norm = nn.BatchNorm1d(out_channels)
        self.dropout = nn.Dropout(dropout)
        
        # Additional projection for residual connection if dimensions change
        if in_channels != out_channels:
            self.residual_proj = nn.Linear(in_channels, out_channels)
        else:
            self.residual_proj = nn.Identity()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # Forward pass through heterophily aggregation
        out = self.aggregation(x, edge_index)
        
        # Batch normalization
        out = self.batch_norm(out)
        
        # Dropout
        out = self.dropout(out)
        
        # Residual connection
        residual = self.residual_proj(x)
        out = out + residual
        
        return F.relu(out)


class HeteroGNN(nn.Module):
    """
    Heterophily-aware GNN architecture (CPU-only).
    
    Architecture:
    - Multiple HeteroGNNLayers for hierarchical feature extraction.
    - Global mean pooling for graph-level representation.
    - Fully connected layers for regression/classification.
    
    Designed specifically for molecular reactivity prediction where
    heterophily (different nodes having different properties) is common.
    """
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 3,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Input layer
        self.input_proj = nn.Linear(in_channels, hidden_channels)
        
        # Heterophily layers
        self.layers = nn.ModuleList()
        for _ in range(num_layers):
            self.layers.append(
                HeteroGNNLayer(hidden_channels, hidden_channels, dropout)
            )
        
        # Output layers
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels // 2, out_channels)
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
                batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: Node features [N, in_channels]
            edge_index: Edge indices [2, E]
            batch: Batch vector [N] for graph-level pooling (optional)
        
        Returns:
            Graph-level embeddings or node-level predictions depending on batch
        """
        # Input projection
        x = F.relu(self.input_proj(x))
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Heterophily layers
        for layer in self.layers:
            x = layer(x, edge_index)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Global pooling if batch indices provided
        if batch is not None:
            # Mean pooling per graph
            from torch_geometric.nn import global_mean_pool
            x = global_mean_pool(x, batch)
        
        # Output projection
        out = self.output_proj(x)
        return out

    def __repr__(self):
        return f'HeteroGNN(num_layers={self.num_layers}, hidden_channels={self.layers[0].aggregation.out_channels})'


def create_hetero_gnn_model(
    in_channels: int,
    hidden_channels: int = 64,
    out_channels: int = 1,
    num_layers: int = 3,
    dropout: float = 0.1
) -> HeteroGNN:
    """
    Factory function to create a HeteroGNN model instance.
    
    Args:
        in_channels: Number of input node features
        hidden_channels: Number of hidden units per layer
        out_channels: Number of output units (e.g., 1 for regression)
        num_layers: Number of heterophily-aware GNN layers
        dropout: Dropout rate
        
    Returns:
        Initialized HeteroGNN model
    """
    model = HeteroGNN(
        in_channels=in_channels,
        hidden_channels=hidden_channels,
        out_channels=out_channels,
        num_layers=num_layers,
        dropout=dropout
    )
    return model