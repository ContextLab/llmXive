"""
Graph Convolutional Network (GCN) implementation for anomaly detection.
CPU-only implementation as per project constraints.
"""
import os
import logging
from typing import Optional, Tuple, Dict, Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv

logger = logging.getLogger(__name__)


class GCNAnomalyDetector(nn.Module):
    """
    2-layer GCN for node-level anomaly detection.
    Designed to run on CPU with early stopping.
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 1,
        dropout: float = 0.5
    ):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return x

    def predict_proba(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Returns anomaly probabilities via sigmoid activation."""
        logits = self.forward(x, edge_index)
        return torch.sigmoid(logits).squeeze(-1)


def train_gcn(
    model: GCNAnomalyDetector,
    data: Data,
    train_mask: torch.Tensor,
    val_mask: torch.Tensor,
    epochs: int = 30,
    patience: int = 5,
    lr: float = 0.01,
    weight_decay: float = 5e-4
) -> Tuple[Dict[str, Any], int]:
    """
    Train the GCN model with early stopping.

    Args:
        model: The GCN model to train.
        data: PyTorch Geometric Data object.
        train_mask: Boolean mask for training nodes.
        val_mask: Boolean mask for validation nodes.
        epochs: Maximum number of training epochs.
        patience: Early stopping patience.
        lr: Learning rate.
        weight_decay: L2 regularization.

    Returns:
        Tuple of (training history dict, best epoch).
    """
    device = torch.device('cpu')
    model = model.to(device)
    data = data.to(device)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=lr,
        weight_decay=weight_decay
    )
    criterion = nn.BCELoss()

    history = {'loss': [], 'val_loss': []}
    best_val_loss = float('inf')
    best_epoch = 0
    patience_counter = 0

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        out = model(data.x, data.edge_index)
        # Ensure labels are float for BCELoss
        y_train = data.y[train_mask].float()
        out_train = out[train_mask].squeeze(-1)
        
        loss = criterion(out_train, y_train)
        loss.backward()
        optimizer.step()

        history['loss'].append(loss.item())

        # Validation
        model.eval()
        with torch.no_grad():
            val_out = model(data.x, data.edge_index)
            y_val = data.y[val_mask].float()
            out_val = val_out[val_mask].squeeze(-1)
            
            val_loss = criterion(out_val, y_val)
            history['val_loss'].append(val_loss.item())

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch
                patience_counter = 0
            else:
                patience_counter += 1

        if patience_counter >= patience:
            logger.info(f"Early stopping at epoch {epoch}")
            break

        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}: train_loss={loss.item():.4f}, val_loss={val_loss.item():.4f}")

    return history, best_epoch


def load_graph_data(
    graphml_path: str,
    feature_type: str = 'structural'
) -> Data:
    """
    Load graph from GraphML and convert to PyTorch Geometric Data.

    Args:
        graphml_path: Path to the .graphml file.
        feature_type: Type of features to use ('structural' or 'raw').

    Returns:
        PyTorch Geometric Data object.
    """
    import networkx as nx
    import numpy as np

    G = nx.read_graphml(graphml_path)

    # Convert to edge index
    edge_index = np.array(G.edges()).T
    edge_index = torch.tensor(edge_index, dtype=torch.long)

    # Prepare node features
    if feature_type == 'structural':
        # Compute structural features
        degrees = np.array([d for _, d in G.degree()])
        in_degrees = np.array([d for _, d in G.in_degree()])
        out_degrees = np.array([d for _, d in G.out_degree()])

        # Normalize features
        x = np.column_stack([degrees, in_degrees, out_degrees])
        x = x / (np.max(x, axis=0) + 1e-8)
    else:
        # Placeholder for raw features if available
        x = np.zeros((G.number_of_nodes(), 1))

    x = torch.tensor(x, dtype=torch.float)

    # Prepare labels (assuming 'label' attribute exists in nodes)
    y = np.array([G.nodes[n].get('label', 0) for n in G.nodes()])
    y = torch.tensor(y, dtype=torch.long)

    return Data(x=x, edge_index=edge_index, y=y)


def main():
    """Example usage of GCN module."""
    logging.basicConfig(level=logging.INFO)

    # This would typically be called from main.py
    logger.info("GCN module loaded successfully")

    # Example: Create a simple model
    model = GCNAnomalyDetector(in_channels=3, hidden_channels=64, out_channels=1)
    logger.info(f"Model created: {model}")


if __name__ == "__main__":
    main()