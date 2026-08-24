"""
Connectivity-only GNN (2D) Baseline Architecture.

This module implements a baseline Geometric GNN that ignores 3D spatial
coordinates (`pos` attribute) and relies solely on graph connectivity
(atomic numbers and bond topology) to predict molecular surface charges.
"""
from typing import Optional

import torch
import torch.nn as nn
from torch_geometric.nn import MessagePassing
from torch_geometric.nn import global_mean_pool
from torch_geometric.utils import add_self_loops

from data.dataset import MoleculeData
from utils import get_logger

logger = get_logger(__name__)


class EdgeEncoder(nn.Module):
    """
    Encodes edge features based on atomic types of connected nodes.

    In a pure 2D connectivity model without explicit edge features,
    we derive edge context from the pair of atomic numbers at the ends.
    """

    def __init__(self, num_atom_types: int = 128, edge_dim: int = 64):
        super().__init__()
        self.num_atom_types = num_atom_types
        self.edge_dim = edge_dim

        # Embedding for atom types to create initial node features if needed,
        # but here we focus on edge context.
        self.atom_embed = nn.Embedding(num_atom_types, edge_dim)

        # MLP to combine source and target embeddings into an edge vector
        self.edge_mlp = nn.Sequential(
            nn.Linear(edge_dim * 2, edge_dim),
            nn.SiLU(),
            nn.Linear(edge_dim, edge_dim)
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Node features of shape [N, D] (atomic numbers embedded).
            edge_index: Graph connectivity of shape [2, E].
        Returns:
            edge_attr: Edge features of shape [E, edge_dim].
        """
        src = edge_index[0]
        dst = edge_index[1]

        src_emb = self.atom_embed(x[src])
        dst_emb = self.atom_embed(x[dst])

        combined = torch.cat([src_emb, dst_emb], dim=-1)
        edge_attr = self.edge_mlp(combined)
        return edge_attr


class ConnectivityGNNLayer(MessagePassing):
    """
    A message passing layer that uses only connectivity and node features.
    Ignores `pos` (coordinates) completely.
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__(aggr="add")  # Sum aggregation
        self.in_channels = in_channels
        self.out_channels = out_channels

        # Message MLP: combines source node, target node, and edge features
        self.message_mlp = nn.Sequential(
            nn.Linear(in_channels * 2 + out_channels, out_channels),
            nn.SiLU(),
            nn.Linear(out_channels, out_channels)
        )

        # Update MLP: combines old node state and aggregated message
        self.update_mlp = nn.Sequential(
            nn.Linear(in_channels + out_channels, out_channels),
            nn.SiLU(),
            nn.Linear(out_channels, out_channels)
        )

        # Linear projection for edge features if not provided
        self.edge_linear = nn.Linear(out_channels, out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: Node features [N, in_channels].
            edge_index: Connectivity [2, E].
            edge_attr: Edge features [E, out_channels] (or compatible dim).
        Returns:
            x_out: Updated node features [N, out_channels].
        """
        # Ensure edge_attr exists and is projected to correct dim
        if edge_attr is None:
            # Fallback if edge_attr not passed (should be handled upstream)
            # Create dummy zero edges or handle error.
            # For robustness, we assume edge_attr is passed from EdgeEncoder.
            raise ValueError("edge_attr must be provided for 2D GNN")

        # Propagate messages
        x_out = self.propagate(edge_index, x=x, edge_attr=edge_attr)
        return x_out

    def message(self, x_i: torch.Tensor, x_j: torch.Tensor,
                edge_attr: torch.Tensor) -> torch.Tensor:
        """
        Construct message from source node (j), target node (i), and edge.
        """
        # x_j: source node features
        # x_i: target node features
        # edge_attr: edge features
        msg_input = torch.cat([x_i, x_j, edge_attr], dim=-1)
        return self.message_mlp(msg_input)

    def update(self, aggr_out: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        """
        Update node state with aggregated messages.
        """
        update_input = torch.cat([x, aggr_out], dim=-1)
        return self.update_mlp(update_input)


class Baseline2DModel(nn.Module):
    """
    Connectivity-only GNN Baseline.

    Architecture:
    1. Atom Embedding: Maps atomic numbers to dense vectors.
    2. Edge Encoding: Derives edge features from connected atom types.
    3. GNN Layers: Message passing using only connectivity (no `pos`).
    4. Readout: Global mean pooling to get graph-level representation.
    5. Regression Head: MLP to predict charges per atom.

    Note: This model strictly ignores the `pos` attribute of `MoleculeData`.
    """

    def __init__(
        self,
        num_atom_types: int = 128,
        hidden_channels: int = 128,
        num_layers: int = 3,
        out_channels: int = 1
    ):
        super().__init__()
        self.num_atom_types = num_atom_types
        self.hidden_channels = hidden_channels
        self.num_layers = num_layers

        # Logger for initialization info
        logger.info(f"Initializing Baseline2DModel with {num_layers} layers")

        # Atom Embedding
        self.atom_embed = nn.Embedding(num_atom_types, hidden_channels)

        # Edge Encoder (creates edge features from atom types)
        self.edge_encoder = EdgeEncoder(num_atom_types, hidden_channels)

        # GNN Layers
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            in_ch = hidden_channels
            out_ch = hidden_channels
            self.convs.append(
                ConnectivityGNNLayer(in_ch, out_ch)
            )

        # Readout Layer: Global Mean Pooling
        self.pool = global_mean_pool

        # Regression Head: Graph-level to Atom-level charge
        # Since we want per-atom charges, we can either:
        # a) Output a single graph property (not useful for surface charge distribution)
        # b) Use the final node embeddings directly for per-atom prediction.
        # We choose (b) to match the task of predicting surface charge distribution.
        self.head = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels // 2),
            nn.SiLU(),
            nn.Linear(hidden_channels // 2, out_channels)
        )

    def forward(self, data: MoleculeData) -> torch.Tensor:
        """
        Forward pass.

        Args:
            data: MoleculeData object containing x (atomic numbers), edge_index,
                  and optionally pos (ignored).
        Returns:
            charges: Predicted charges [N, 1] for each atom.
        """
        # Extract inputs
        x = data.x  # [N, 1] usually atomic numbers
        edge_index = data.edge_index
        # pos = data.pos  # Explicitly ignored as per task requirement

        # Handle atomic numbers: typically x is [N, 1] with integer atomic numbers
        # We assume x contains the atomic number directly or we map it.
        # If x is already embedded, we skip embedding. Assuming raw atomic numbers.
        if x.dim() == 2 and x.size(1) == 1:
            # Flatten to [N] for embedding lookup
            atomic_numbers = x.squeeze(-1).long()
        else:
            atomic_numbers = x.long()

        # Ensure atomic numbers are within embedding range
        atomic_numbers = atomic_numbers.clamp(0, self.num_atom_types - 1)

        # 1. Atom Embedding
        h = self.atom_embed(atomic_numbers)  # [N, hidden]

        # 2. Edge Encoding
        edge_attr = self.edge_encoder(h, edge_index)  # [E, hidden]

        # 3. GNN Layers
        for conv in self.convs:
            h = conv(h, edge_index, edge_attr)

        # 4. Head: Predict per-atom charge from final node embeddings
        charges = self.head(h)  # [N, 1]

        return charges


def create_baseline_2d_model(
    num_atom_types: int = 128,
    hidden_channels: int = 128,
    num_layers: int = 3
) -> Baseline2DModel:
    """
    Factory function to instantiate the 2D baseline model.

    Args:
        num_atom_types: Maximum atomic number to support.
        hidden_channels: Dimension of hidden layers.
        num_layers: Number of GNN layers.

    Returns:
        Initialized Baseline2DModel.
    """
    model = Baseline2DModel(
        num_atom_types=num_atom_types,
        hidden_channels=hidden_channels,
        num_layers=num_layers
    )
    logger.info(f"Created Baseline2DModel with {sum(p.numel() for p in model.parameters())} parameters")
    return model
