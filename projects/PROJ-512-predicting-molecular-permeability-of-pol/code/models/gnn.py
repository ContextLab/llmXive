"""
Message-Passing Graph Neural Network for Polymer Permeability Prediction.

Implements a CPU-compatible GNN using PyTorch with float32 precision.
No mixed precision or 8-bit quantization is used.
"""
import logging
from typing import Optional, Dict, Any, Tuple, List

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops

from models.polymer_graph import PolymerGraph

logger = logging.getLogger(__name__)

# Ensure float32 precision globally for this module
torch.set_default_dtype(torch.float32)


class PolymerMessagePassingLayer(MessagePassing):
    """
    Custom Message Passing Layer for Polymer Graphs.
    
    Aggregates node features from neighbors and updates node embeddings
    using learned transformations.
    """
    def __init__(self, in_channels: int, out_channels: int, edge_dim: int = 1):
        super().__init__(aggr='add')  # Sum aggregation
        
        # Node transformation
        self.lin = nn.Linear(in_channels, out_channels)
        
        # Edge transformation
        self.edge_mlp = nn.Sequential(
            nn.Linear(edge_dim, out_channels),
            nn.ReLU(),
            nn.Linear(out_channels, out_channels)
        )
        
        # Update MLP
        self.update_mlp = nn.Sequential(
            nn.Linear(out_channels * 2, out_channels),
            nn.ReLU(),
            nn.Linear(out_channels, out_channels)
        )
        
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.xavier_uniform_(self.lin.weight)
        nn.init.zeros_(self.lin.bias)
        for layer in self.edge_mlp:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)
        for layer in self.update_mlp:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
                edge_attr: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass for message passing.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Graph connectivity [2, num_edges]
            edge_attr: Edge features [num_edges, edge_dim] (optional)
        
        Returns:
            Updated node embeddings [num_nodes, out_channels]
        """
        # Add self-loops for message passing
        edge_index, _ = add_self_loops(edge_index, num_nodes=x.size(0))
        
        # Propagate messages
        out = self.propagate(
            edge_index=edge_index,
            x=x,
            edge_attr=edge_attr,
            size=(x.size(0), x.size(0))
        )
        
        return out

    def message(self, x_j: torch.Tensor, edge_attr: Optional[torch.Tensor]) -> torch.Tensor:
        """
        Compute messages from neighbor nodes.
        
        Args:
            x_j: Node features of source nodes
            edge_attr: Edge features (if available)
        
        Returns:
            Messages to be aggregated
        """
        if edge_attr is not None:
            edge_transform = self.edge_mlp(edge_attr)
            return x_j + edge_transform
        return x_j

    def update(self, aggr_out: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        """
        Update node embeddings with aggregated messages.
        
        Args:
            aggr_out: Aggregated messages
            x: Original node features
        
        Returns:
            Updated node embeddings
        """
        # Concatenate original features with aggregated messages
        concat_out = torch.cat([aggr_out, x], dim=-1)
        return self.update_mlp(concat_out)


class PolymerGNN(nn.Module):
    """
    Message-Passing Graph Neural Network for Polymer Permeability Prediction.
    
    Architecture:
    - Multiple message-passing layers with residual connections
    - Global readout via mean pooling
    - Feed-forward regression head
    
    Constraints:
    - CPU-compatible (no CUDA-specific operations)
    - Float32 precision only (no mixed precision)
    - No 8-bit quantization
    """
    def __init__(
        self,
        input_dim: int = 64,
        hidden_dim: int = 128,
        output_dim: int = 1,
        num_layers: int = 4,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.num_layers = num_layers
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # Message passing layers
        self.conv_layers = nn.ModuleList()
        self.norm_layers = nn.ModuleList()
        
        for i in range(num_layers):
            in_channels = hidden_dim if i > 0 else hidden_dim
            conv = PolymerMessagePassingLayer(in_channels, hidden_dim)
            self.conv_layers.append(conv)
            self.norm_layers.append(nn.BatchNorm1d(hidden_dim))
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Readout MLP
        self.readout_mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim)
        )
        
        self.reset_parameters()

    def reset_parameters(self):
        """Initialize all learnable parameters."""
        nn.init.xavier_uniform_(self.input_proj.weight)
        nn.init.zeros_(self.input_proj.bias)
        
        for layer in self.conv_layers:
            layer.reset_parameters()
        
        for layer in self.norm_layers:
            layer.reset_parameters()
        
        nn.init.xavier_uniform_(self.readout_mlp[0].weight)
        nn.init.zeros_(self.readout_mlp[0].bias)
        nn.init.xavier_uniform_(self.readout_mlp[3].weight)
        nn.init.zeros_(self.readout_mlp[3].bias)

    def forward(self, data: Data) -> torch.Tensor:
        """
        Forward pass through the GNN.
        
        Args:
            data: PyTorch Geometric Data object with x, edge_index, edge_attr
        
        Returns:
            Predicted permeability values [batch_size, 1]
        """
        x = data.x
        edge_index = data.edge_index
        edge_attr = data.edge_attr if hasattr(data, 'edge_attr') else None
        
        # Input projection
        x = self.input_proj(x)
        
        # Message passing layers with residual connections and normalization
        for i in range(self.num_layers):
            x_prev = x
            x = self.conv_layers[i](x, edge_index, edge_attr)
            x = self.norm_layers[i](x)
            x = F.relu(x)
            x = self.dropout(x)
            
            # Residual connection
            if x.size(1) == x_prev.size(1):
                x = x + x_prev
        
        # Global readout (mean pooling over nodes)
        # Assuming single graph per batch for now
        if hasattr(data, 'batch'):
            # Batched graphs - use batch index for pooling
            row, col = edge_index
            out = torch.zeros(data.batch.max() + 1, x.size(1), device=x.device)
            out.index_add_(0, data.batch, x)
            out = out / torch.bincount(data.batch).unsqueeze(1)
        else:
            # Single graph - simple mean
            out = x.mean(dim=0, keepdim=True)
        
        # Regression head
        pred = self.readout_mlp(out)
        
        return pred

    def get_graph_representation(self, data: Data) -> torch.Tensor:
        """
        Extract graph-level representation without final prediction head.
        
        Args:
            data: PyTorch Geometric Data object
        
        Returns:
            Graph embedding [1, hidden_dim]
        """
        x = data.x
        edge_index = data.edge_index
        edge_attr = data.edge_attr if hasattr(data, 'edge_attr') else None
        
        x = self.input_proj(x)
        
        for i in range(self.num_layers):
            x = self.conv_layers[i](x, edge_index, edge_attr)
            x = self.norm_layers[i](x)
            x = F.relu(x)
            x = self.dropout(x)
        
        # Global readout
        if hasattr(data, 'batch'):
            row, col = edge_index
            out = torch.zeros(data.batch.max() + 1, x.size(1), device=x.device)
            out.index_add_(0, data.batch, x)
            out = out / torch.bincount(data.batch).unsqueeze(1)
        else:
            out = x.mean(dim=0, keepdim=True)
        
        return out


def polymer_graph_to_pyg_data(graph: PolymerGraph) -> Data:
    """
    Convert a PolymerGraph object to a PyTorch Geometric Data object.
    
    Args:
        graph: PolymerGraph instance with node/edge features
    
    Returns:
        PyTorch Geometric Data object
    """
    # Extract node features
    x = torch.tensor(graph.node_features, dtype=torch.float32)
    
    # Extract edge index
    edge_index = torch.tensor(graph.edge_index, dtype=torch.long).t().contiguous()
    
    # Extract edge features if available
    edge_attr = None
    if hasattr(graph, 'edge_features') and graph.edge_features is not None:
        edge_attr = torch.tensor(graph.edge_features, dtype=torch.float32)
    
    # Create PyG Data object
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    
    return data


def create_gnn_model(
    input_dim: int = 64,
    hidden_dim: int = 128,
    num_layers: int = 4,
    dropout: float = 0.1
) -> PolymerGNN:
    """
    Factory function to create a PolymerGNN model.
    
    Args:
        input_dim: Dimension of input node features
        hidden_dim: Dimension of hidden layers
        num_layers: Number of message-passing layers
        dropout: Dropout rate for regularization
    
    Returns:
        Initialized PolymerGNN model
    """
    model = PolymerGNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout
    )
    
    logger.info(f"Created PolymerGNN with {num_layers} layers, hidden_dim={hidden_dim}")
    logger.info(f"Total parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    return model


def main():
    """
    Simple test of the GNN model instantiation and forward pass.
    """
    import numpy as np
    
    logging.basicConfig(level=logging.INFO)
    
    # Create a dummy PolymerGraph for testing
    num_nodes = 10
    num_edges = 20
    
    dummy_graph = PolymerGraph(
        smiles="C1=CC=CC=C1",  # Benzene
        node_features=np.random.rand(num_nodes, 64).astype(np.float32),
        edge_index=np.random.randint(0, num_nodes, (2, num_edges)).tolist(),
        edge_features=np.random.rand(num_edges, 1).astype(np.float32)
    )
    
    # Convert to PyG Data
    data = polymer_graph_to_pyg_data(dummy_graph)
    
    # Create model
    model = create_gnn_model(input_dim=64, hidden_dim=128, num_layers=4)
    
    # Forward pass
    model.eval()
    with torch.no_grad():
        output = model(data)
    
    logger.info(f"Forward pass successful. Output shape: {output.shape}")
    logger.info(f"Sample prediction: {output[0, 0].item():.4f}")
    
    # Verify float32 precision
    for param in model.parameters():
        assert param.dtype == torch.float32, "Model must use float32 precision"
    
    logger.info("All checks passed. Model is CPU-compatible and uses float32 precision.")


if __name__ == "__main__":
    main()