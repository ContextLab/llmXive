"""
Graph Attention Network (GAT) implementation for predicting molecular interactions.

Implements a 3-layer GAT as per Plan override of Spec FR-003.
Architecture: 3 GATConv layers, hidden=64, dropout=0.5.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from typing import Optional, Tuple

class GATModel(nn.Module):
    """
    3-layer Graph Attention Network for molecular property prediction.

    Args:
        in_channels (int): Number of input node features.
        hidden_channels (int): Number of hidden channels (default: 64).
        out_channels (int): Number of output channels (default: 1 for regression).
        num_heads (int): Number of attention heads (default: 1).
        dropout (float): Dropout probability (default: 0.5).

    Architecture:
        Layer 1: GATConv -> ReLU -> Dropout
        Layer 2: GATConv -> ReLU -> Dropout
        Layer 3: GATConv -> Linear (out_channels)
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 1,
        num_heads: int = 1,
        dropout: float = 0.5
    ):
        super().__init__()

        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.num_heads = num_heads
        self.dropout = dropout

        # Layer 1: Input -> Hidden
        self.conv1 = GATConv(
            in_channels=in_channels,
            out_channels=hidden_channels,
            heads=num_heads,
            dropout=dropout,
            concat=True
        )

        # Layer 2: Hidden -> Hidden
        # Input dimension is hidden_channels * num_heads because concat=True in conv1
        self.conv2 = GATConv(
            in_channels=hidden_channels * num_heads,
            out_channels=hidden_channels,
            heads=num_heads,
            dropout=dropout,
            concat=True
        )

        # Layer 3: Hidden -> Output
        # Input dimension is hidden_channels * num_heads because concat=True in conv2
        self.conv3 = GATConv(
            in_channels=hidden_channels * num_heads,
            out_channels=hidden_channels,
            heads=num_heads,
            dropout=dropout,
            concat=False  # Single output channel for regression
        )

        # Final linear layer to map to output dimension
        self.out_proj = nn.Linear(hidden_channels, out_channels)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass through the GAT network.

        Args:
            x (torch.Tensor): Node feature matrix of shape [num_nodes, in_channels].
            edge_index (torch.Tensor): Graph connectivity in COO format.
            edge_attr (Optional[torch.Tensor]): Edge features (not used in standard GATConv).

        Returns:
            torch.Tensor: Output predictions of shape [num_graphs, out_channels] or [num_nodes, out_channels].
        """
        # Layer 1
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Layer 2
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Layer 3
        x = self.conv3(x, edge_index)

        # Project to output dimension
        x = self.out_proj(x)

        return x


def create_gat_model(
    in_channels: int,
    hidden_channels: int = 64,
    out_channels: int = 1,
    num_heads: int = 1,
    dropout: float = 0.5
) -> GATModel:
    """
    Factory function to create a GATModel instance with specified parameters.

    Args:
        in_channels (int): Number of input features per node.
        hidden_channels (int): Number of hidden units per head (default: 64).
        out_channels (int): Output dimension (default: 1 for scalar adhesion energy).
        num_heads (int): Number of attention heads (default: 1).
        dropout (float): Dropout rate (default: 0.5).

    Returns:
        GATModel: Initialized 3-layer GAT model.
    """
    return GATModel(
        in_channels=in_channels,
        hidden_channels=hidden_channels,
        out_channels=out_channels,
        num_heads=num_heads,
        dropout=dropout
    )