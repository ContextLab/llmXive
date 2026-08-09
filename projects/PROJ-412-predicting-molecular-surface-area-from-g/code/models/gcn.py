"""
Graph Convolutional Network (GCN) model for predicting molecular surface area.
Implements a lightweight, CPU-tractable GCN architecture using PyTorch Geometric.
"""
import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class GCNModel(torch.nn.Module):
    """
    Lightweight Graph Convolutional Network for molecular property prediction.

    This model takes graph-structured molecular data (node features, edge indices)
    and predicts a scalar value (surface area) using a series of GCN layers
    followed by a global pooling operation and a readout MLP.

    Architecture:
    - 2 GCN layers with ReLU activation and dropout
    - Global mean pooling to aggregate node features
    - Fully connected readout layer to produce scalar output

    Args:
        input_dim (int): Dimensionality of input node features.
        hidden_dim (int, optional): Dimensionality of hidden layers. Defaults to 64.
        output_dim (int, optional): Dimensionality of output. Defaults to 1 (scalar).
        dropout (float, optional): Dropout probability. Defaults to 0.1.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        output_dim: int = 1,
        dropout: float = 0.1
    ):
        super(GCNModel, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.dropout = dropout

        # GCN Layers
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)

        # Readout layers
        self.lin1 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.lin2 = torch.nn.Linear(hidden_dim, output_dim)

        self._init_weights()
        logger.info(f"Initialized GCNModel: input={input_dim}, hidden={hidden_dim}, output={output_dim}")

    def _init_weights(self):
        """Initialize weights with Xavier/Glorot initialization."""
        for conv in [self.conv1, self.conv2]:
            torch.nn.init.xavier_uniform_(conv.lin.weight)
            if conv.lin.bias is not None:
                torch.nn.init.zeros_(conv.lin.bias)

        for lin in [self.lin1, self.lin2]:
            torch.nn.init.xavier_uniform_(lin.weight)
            if lin.bias is not None:
                torch.nn.init.zeros_(lin.bias)

    def forward(self, input_tensor: torch.Tensor, edge_index: torch.Tensor,
                batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass of the GCN model.

        Args:
            input_tensor (torch.Tensor): Node features of shape [num_nodes, input_dim].
            edge_index (torch.Tensor): Graph connectivity of shape [2, num_edges].
            batch (torch.Tensor, optional): Vector of node-to-graph assignments.
                If None, assumes a single graph. Defaults to None.

        Returns:
            torch.Tensor: Predicted surface area values of shape [num_graphs, 1].
        """
        # Ensure input is float
        x = input_tensor.float()

        # First GCN layer
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Second GCN layer
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Global pooling
        if batch is None:
            # If no batch vector, assume single graph
            x = global_mean_pool(x, torch.zeros(x.size(0), dtype=torch.long, device=x.device))
        else:
            x = global_mean_pool(x, batch)

        # Readout MLP
        x = F.relu(self.lin1(x))
        x = F.dropout(x, p=self.dropout, training=self.training)
        out = self.lin2(x)

        return out

    def get_config(self) -> dict:
        """Return model configuration as a dictionary."""
        return {
            "model_type": "GCNModel",
            "input_dim": self.input_dim,
            "hidden_dim": self.hidden_dim,
            "output_dim": self.output_dim,
            "dropout": self.dropout
        }


def create_model_from_processed_data(
    processed_data_path: str,
    hidden_dim: int = 64,
    dropout: float = 0.1
) -> Tuple[GCNModel, int]:
    """
    Create a GCNModel instance by inspecting the input data to determine feature dimension.

    This function loads a sample of the processed data to infer the number of input
    features, then instantiates the model with the correct input dimension.

    Args:
        processed_data_path (str): Path to the processed parquet file containing
            molecular graphs.
        hidden_dim (int, optional): Hidden layer dimension. Defaults to 64.
        dropout (float, optional): Dropout probability. Defaults to 0.1.

    Returns:
        Tuple[GCNModel, int]: The instantiated GCNModel and the inferred input dimension.
    """
    import pandas as pd

    logger.info(f"Inspecting data at {processed_data_path} to determine input dimension...")

    # Load just the first row to infer dimensions
    df = pd.read_parquet(processed_data_path)
    first_row = df.iloc[0]

    # Determine input dimension from node_features
    if 'node_features' in first_row.index:
        node_features = first_row['node_features']
        if isinstance(node_features, list):
            input_dim = len(node_features)
        elif hasattr(node_features, 'shape'):
            input_dim = node_features.shape[1] if len(node_features.shape) > 1 else node_features.shape[0]
        else:
            raise ValueError(f"Unable to determine input dimension from node_features type: {type(node_features)}")
    else:
        # Fallback: try to infer from the schema or raise error
        raise ValueError("Column 'node_features' not found in processed data. Cannot determine input dimension.")

    logger.info(f"Inferred input dimension: {input_dim}")

    model = GCNModel(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        dropout=dropout
    )

    return model, input_dim