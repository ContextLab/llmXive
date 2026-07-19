"""
Graph Neural Network implementation for Polymer Permeability Prediction.

Implements a Message-Passing GNN with 3 layers and 64 hidden dimensions.
Uses CPU-compatible PyTorch with float32 precision as per constraints.
Consumes input features defined in FR-001: atom type, hybridization, bond type.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops

# Import existing project utilities
from models.polymer_graph import PolymerGraph
from data.utils import set_seed, get_seed

logger = logging.getLogger(__name__)


class PolymerMessagePassingLayer(MessagePassing):
    """
    Custom Message Passing Layer for Polymer graphs.

    Processes node features (atom type, hybridization) and edge features (bond type).
    Uses float32 precision throughout.
    """

    def __init__(self, in_channels: int, out_channels: int, edge_channels: int = 4):
        """
        Initialize the message passing layer.

        Args:
            in_channels: Number of input node features
            out_channels: Number of output node features
            edge_channels: Number of edge features (bond types)
        """
        super().__init__(aggr='add')  # Sum aggregation
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.edge_channels = edge_channels

        # Node feature transformation
        self.lin = nn.Linear(in_channels, out_channels)

        # Edge feature transformation
        self.edge_lin = nn.Linear(edge_channels, out_channels)

        # Output transformation
        self.out_lin = nn.Linear(out_channels * 2, out_channels)

        # Initialize weights
        self._reset_parameters()

    def _reset_parameters(self):
        """Reset layer parameters."""
        nn.init.xavier_uniform_(self.lin.weight)
        nn.init.xavier_uniform_(self.edge_lin.weight)
        nn.init.xavier_uniform_(self.out_lin.weight)
        nn.init.zeros_(self.lin.bias)
        nn.init.zeros_(self.edge_lin.bias)
        nn.init.zeros_(self.out_lin.bias)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass for the message passing layer.

        Args:
            x: Node features tensor [N, in_channels]
            edge_index: Edge indices tensor [2, E]
            edge_attr: Edge features tensor [E, edge_channels]

        Returns:
            Updated node features tensor [N, out_channels]
        """
        # Ensure float32 precision
        x = x.float()
        if edge_attr is not None:
            edge_attr = edge_attr.float()

        # Transform node features
        x = self.lin(x)

        # Propagate messages
        out = self.propagate(edge_index, x=x, edge_attr=edge_attr)

        # Combine original and propagated features
        out = torch.cat([x, out], dim=1)
        out = self.out_lin(out)

        return out

    def message(self, x_j: torch.Tensor, edge_attr: Optional[torch.Tensor]) -> torch.Tensor:
        """
        Compute messages for edge j.

        Args:
            x_j: Source node features
            edge_attr: Edge features

        Returns:
            Messages tensor
        """
        if edge_attr is not None:
            edge_msg = self.edge_lin(edge_attr)
            return x_j + edge_msg
        return x_j

    def update(self, aggr_out: torch.Tensor) -> torch.Tensor:
        """
        Update node features with aggregated messages.

        Args:
            aggr_out: Aggregated messages

        Returns:
            Updated node features
        """
        return aggr_out


class PolymerGNN(nn.Module):
    """
    Message-Passing GNN for Polymer Permeability Prediction.

    Architecture:
    - 3 Message Passing Layers
    - 64 hidden dimensions
    - Global readout for graph-level prediction
    - Float32 precision only
    """

    def __init__(self, input_dim: int = 10, hidden_dim: int = 64,
                 output_dim: int = 1, num_layers: int = 3,
                 edge_dim: int = 4):
        """
        Initialize the Polymer GNN.

        Args:
            input_dim: Dimension of input node features (FR-001 features)
            hidden_dim: Hidden layer dimension (default: 64)
            output_dim: Output dimension (default: 1 for log-permeability)
            num_layers: Number of message passing layers (default: 3)
            edge_dim: Dimension of edge features (bond types)
        """
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)

        # Message passing layers
        self.mp_layers = nn.ModuleList()
        for i in range(num_layers):
            in_channels = hidden_dim if i > 0 else hidden_dim
            self.mp_layers.append(
                PolymerMessagePassingLayer(
                    in_channels=in_channels,
                    out_channels=hidden_dim,
                    edge_channels=edge_dim
                )
            )

        # Global readout (sum pooling)
        self.readout = nn.Linear(hidden_dim, hidden_dim)

        # Final prediction layer
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(p=0.1),
            nn.Linear(hidden_dim // 2, output_dim)
        )

        # Initialize weights
        self._reset_parameters()

        logger.info(f"Initialized PolymerGNN with {num_layers} layers, {hidden_dim} hidden dim")

    def _reset_parameters(self):
        """Reset all layer parameters."""
        nn.init.xavier_uniform_(self.input_proj.weight)
        nn.init.zeros_(self.input_proj.bias)

        for layer in self.mp_layers:
            layer._reset_parameters()

        nn.init.xavier_uniform_(self.readout.weight)
        nn.init.zeros_(self.readout.bias)

        for layer in self.predictor:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)

    def forward(self, batch: Data) -> torch.Tensor:
        """
        Forward pass for the entire graph.

        Args:
            batch: PyTorch Geometric Data object containing:
                - x: Node features [N, input_dim]
                - edge_index: Edge indices [2, E]
                - edge_attr: Edge features [E, edge_dim]
                - batch: Batch indices [N]

        Returns:
            Predicted log-permeability values [num_graphs]
        """
        # Ensure float32 precision
        x = batch.x.float()
        edge_index = batch.edge_index
        edge_attr = batch.edge_attr.float() if batch.edge_attr is not None else None

        # Input projection
        x = self.input_proj(x)
        x = F.relu(x)

        # Message passing layers
        for layer in self.mp_layers:
            x = layer(x, edge_index, edge_attr)
            x = F.relu(x)

        # Global readout (sum pooling per graph)
        from torch_geometric.nn import global_add_pool
        graph_features = global_add_pool(x, batch.batch)

        # Readout transformation
        graph_features = self.readout(graph_features)
        graph_features = F.relu(graph_features)

        # Final prediction
        predictions = self.predictor(graph_features)

        return predictions


def polymer_graph_to_pyg_data(polymer_graph: PolymerGraph) -> Data:
    """
    Convert a PolymerGraph object to PyTorch Geometric Data format.

    Args:
        polymer_graph: PolymerGraph object with node/edge features

    Returns:
        PyTorch Geometric Data object
    """
    # Extract node features
    # Expected features: [atom_type, hybridization, ...]
    # FR-001: atom type, hybridization, bond type (edge)
    node_features = polymer_graph.get_node_features()
    edge_index = polymer_graph.get_edge_index()
    edge_features = polymer_graph.get_edge_features()

    # Convert to tensors with float32 precision
    x = torch.tensor(node_features, dtype=torch.float32)
    edge_index = torch.tensor(edge_index, dtype=torch.long)

    if edge_features is not None and len(edge_features) > 0:
        edge_attr = torch.tensor(edge_features, dtype=torch.float32)
    else:
        # Create dummy edge attributes if none provided
        num_edges = edge_index.shape[1]
        edge_attr = torch.zeros((num_edges, 4), dtype=torch.float32)

    # Create Data object
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

    return data


def create_gnn_model(input_dim: int = 10, hidden_dim: int = 64,
                     num_layers: int = 3, edge_dim: int = 4) -> PolymerGNN:
    """
    Factory function to create a PolymerGNN model.

    Args:
        input_dim: Dimension of input node features
        hidden_dim: Hidden layer dimension (default: 64)
        num_layers: Number of message passing layers (default: 3)
        edge_dim: Dimension of edge features

    Returns:
        Initialized PolymerGNN model
    """
    model = PolymerGNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        edge_dim=edge_dim
    )
    return model


def main():
    """
    Main function to demonstrate GNN model creation and basic functionality.
    """
    # Setup logging
    from data.utils import setup_logging
    setup_logging(level=logging.INFO)

    logger.info("Starting GNN model demonstration...")

    # Set seed for reproducibility
    set_seed(42)

    # Create model with FR-001 compliant dimensions
    # Assuming: atom_type (4) + hybridization (3) + other features = ~10 input dim
    model = create_gnn_model(
        input_dim=10,
        hidden_dim=64,
        num_layers=3,
        edge_dim=4
    )

    logger.info(f"Model created: {model}")
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())}")

    # Verify float32 precision
    for param in model.parameters():
        assert param.dtype == torch.float32, "Model must use float32 precision"

    logger.info("✓ All parameters are float32 as required")

    # Create a dummy batch for testing
    dummy_data = Data(
        x=torch.randn(10, 10, dtype=torch.float32),
        edge_index=torch.randint(0, 10, (2, 20), dtype=torch.long),
        edge_attr=torch.randn(20, 4, dtype=torch.float32),
        batch=torch.zeros(10, dtype=torch.long)
    )

    # Test forward pass
    model.eval()
    with torch.no_grad():
        output = model(dummy_data)

    logger.info(f"Dummy forward pass output shape: {output.shape}")
    logger.info("✓ GNN model is functional and CPU-compatible")

    logger.info("GNN model demonstration completed successfully.")


if __name__ == "__main__":
    main()