"""
Lightweight GNN architecture for predicting elastic moduli of 2D materials.

This module defines a CPU-optimized Graph Neural Network (GNN) with 2-3 layers
and hidden dimension <= 64, designed to run efficiently within the 7GB RAM
constraint while maintaining predictive performance for Young's, Shear, and
Poisson ratios.

The model is a structure-only surrogate for DFT calculations, interpolating
from existing Materials Project/AFLOW data rather than solving the
Schrödinger equation from first principles.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
from typing import Tuple, Optional

from utils.config import Config


class LightweightGNN(nn.Module):
    """
    A lightweight Graph Convolutional Network for 2D material property prediction.

    Architecture:
    - 2-3 Graph Convolutional layers (GCNConv)
    - Hidden dimension: 32-64 (configurable, capped at 64)
    - Global mean pooling for graph-level representation
    - 2-layer MLP decoder for multi-output regression

    Targets:
    - Young's Modulus (GPa)
    - Shear Modulus (GPa)
    - Poisson's Ratio (dimensionless)

    Constraints:
    - CPU-only execution (no CUDA)
    - Memory-efficient for 7GB RAM limit
    - 2-3 layers only to prevent overfitting on moderate datasets
    """

    def __init__(self, node_feature_dim: int, hidden_dim: int = 64, num_layers: int = 3, dropout: float = 0.1):
        """
        Initialize the GNN architecture.

        Args:
            node_feature_dim: Dimension of input node features (from MaterialGraph)
            hidden_dim: Hidden layer dimension (must be <= 64 per constraints)
            num_layers: Number of GCN layers (2 or 3)
            dropout: Dropout rate for regularization
        """
        super().__init__()

        # Enforce constraints
        if hidden_dim > 64:
            raise ValueError(f"Hidden dimension must be <= 64, got {hidden_dim}")
        if num_layers not in [2, 3]:
            raise ValueError(f"Number of layers must be 2 or 3, got {num_layers}")

        self.node_feature_dim = node_feature_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout

        # Build GCN layers
        self.convs = nn.ModuleList()

        # First layer: input -> hidden
        self.convs.append(GCNConv(node_feature_dim, hidden_dim))

        # Middle layers: hidden -> hidden
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))

        # Global pooling
        self.pool = global_mean_pool

        # Decoder MLP: graph embedding -> 3 targets (Young's, Shear, Poisson)
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 3),  # 3 output targets
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights with Xavier uniform distribution."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, GCNConv):
                nn.init.xavier_uniform_(module.lin.weight)
                nn.init.zeros_(module.bias)

    def forward(self, data: Data) -> torch.Tensor:
        """
        Forward pass through the GNN.

        Args:
            data: PyTorch Geometric Data object containing:
                  - x: Node features [num_nodes, node_feature_dim]
                  - edge_index: Edge connectivity [2, num_edges]
                  - batch: Batch indices for pooling [num_nodes]

        Returns:
            Tensor of shape [num_graphs, 3] containing predictions for:
            - Young's Modulus
            - Shear Modulus
            - Poisson's Ratio
        """
        x, edge_index, batch = data.x, data.edge_index, data.batch

        # GCN layers with ReLU activation
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

            # Skip connection for deeper networks (optional, improves gradient flow)
            if i > 0 and self.num_layers == 3:
                x = x + data.x  # Simple skip connection

        # Global mean pooling to get graph-level embeddings
        graph_embeddings = self.pool(x, batch)

        # Decode to target properties
        predictions = self.decoder(graph_embeddings)

        return predictions

    def get_num_parameters(self) -> int:
        """Return total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_memory_footprint(self) -> Tuple[int, int]:
        """
        Estimate memory footprint in bytes.

        Returns:
            Tuple of (trainable_params_bytes, total_params_bytes)
        """
        trainable = sum(p.numel() * p.element_size() for p in self.parameters() if p.requires_grad)
        total = sum(p.numel() * p.element_size() for p in self.parameters())
        return trainable, total


def create_model(config: Optional[Config] = None) -> LightweightGNN:
    """
    Factory function to create a LightweightGNN instance with configuration.

    Args:
        config: Optional Config object. If None, uses defaults.

    Returns:
        Initialized LightweightGNN model on CPU.
    """
    # Default configuration
    node_feature_dim = 16  # Assumed from MaterialGraph schema (adjust if different)
    hidden_dim = 64
    num_layers = 3
    dropout = 0.1

    # Override with config if provided
    if config:
        hidden_dim = min(config.get("model.hidden_dim", 64), 64)
        num_layers = config.get("model.num_layers", 3)
        dropout = config.get("model.dropout", 0.1)

    model = LightweightGNN(
        node_feature_dim=node_feature_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout
    )

    # Ensure CPU-only (no CUDA)
    model = model.cpu()

    return model


if __name__ == "__main__":
    # Simple sanity check
    print("Testing LightweightGNN initialization...")

    from torch_geometric.data import Data
    import numpy as np

    # Create a dummy graph
    num_nodes = 10
    num_edges = 20
    node_feature_dim = 16

    x = torch.randn(num_nodes, node_feature_dim)
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    batch = torch.zeros(num_nodes, dtype=torch.long)

    data = Data(x=x, edge_index=edge_index, batch=batch)

    # Create model
    model = create_model()
    print(f"Model created with {model.get_num_parameters()} parameters")

    # Forward pass
    model.eval()
    with torch.no_grad():
        output = model(data)

    print(f"Output shape: {output.shape}")
    print(f"Expected: [1, 3] (1 graph, 3 targets)")
    assert output.shape == (1, 3), f"Unexpected output shape: {output.shape}"

    # Verify CPU execution
    assert next(model.parameters()).device.type == "cpu", "Model must be on CPU"

    print("✓ Sanity check passed: Model runs on CPU and produces correct output shape")

    # Print memory estimate
    trainable, total = model.get_memory_footprint()
    print(f"Memory footprint: {trainable} bytes trainable, {total} bytes total")