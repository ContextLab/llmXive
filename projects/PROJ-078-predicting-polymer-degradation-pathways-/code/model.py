"""
Lightweight Graph Neural Network (GNN) for Polymer Degradation Pathway Prediction.

Implements a CPU-only architecture constrained to:
- Maximum 3 GNN layers
- Hidden dimension <= 128
- Integrated Gradients support for feature attribution
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Batch
from typing import Optional, Tuple, List, Dict, Any

import logging
from utils import get_logger

logger = get_logger(__name__)


class PolymerGNN(nn.Module):
    """
    Lightweight GNN for predicting polymer degradation pathways.

    Architecture Constraints (FR-003):
    - Maximum 3 message passing layers
    - Hidden dimension <= 128
    - CPU-only optimization (no CUDA-specific ops)

    Args:
        input_dim (int): Dimension of input node features
        hidden_dim (int): Hidden dimension (must be <= 128)
        num_layers (int): Number of GNN layers (must be <= 3)
        num_classes (int): Number of degradation pathway classes
        dropout (float): Dropout probability
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        num_layers: int = 3,
        num_classes: int = 4,
        dropout: float = 0.2
    ):
        super().__init__()

        # Enforce constraints
        if hidden_dim > 128:
            raise ValueError(f"hidden_dim must be <= 128, got {hidden_dim}")
        if num_layers > 3:
            raise ValueError(f"num_layers must be <= 3, got {num_layers}")
        if num_layers < 1:
            raise ValueError(f"num_layers must be >= 1, got {num_layers}")

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_classes = num_classes
        self.dropout = dropout

        # Logger for architecture details
        self.logger = get_logger(__name__)

        # Build GNN layers
        self.convs = nn.ModuleList()
        
        # First layer: input_dim -> hidden_dim
        self.convs.append(GCNConv(input_dim, hidden_dim))
        
        # Middle layers: hidden_dim -> hidden_dim
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))

        # Readout layer: hidden_dim -> num_classes
        self.fc = nn.Linear(hidden_dim, num_classes)

        # Activation
        self.act = F.relu

        # Log architecture
        self.logger.info(
            f"Initialized PolymerGNN: input_dim={input_dim}, "
            f"hidden_dim={hidden_dim}, num_layers={num_layers}, "
            f"num_classes={num_classes}"
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
                batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through the GNN.

        Args:
            x: Node features tensor [num_nodes, input_dim]
            edge_index: Edge index tensor [2, num_edges]
            batch: Batch vector for pooling [num_nodes] (optional)

        Returns:
            logits: Class logits [num_graphs, num_classes] or [num_nodes, num_classes]
                    if batch is None
        """
        # Ensure on CPU (FR-003)
        x = x.cpu()
        edge_index = edge_index.cpu()
        if batch is not None:
            batch = batch.cpu()

        # Message passing
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            x = self.act(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # Graph-level pooling if batch vector provided
        if batch is not None:
            x = global_mean_pool(x, batch)

        # Final classification layer
        logits = self.fc(x)

        return logits

    def get_embeddings(self, x: torch.Tensor, edge_index: torch.Tensor,
                       batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Get graph embeddings before the final classification layer.

        Useful for visualization or downstream tasks.
        """
        x = x.cpu()
        edge_index = edge_index.cpu()
        if batch is not None:
            batch = batch.cpu()

        for conv in self.convs:
            x = conv(x, edge_index)
            x = self.act(x)
            x = F.dropout(x, p=self.dropout, training=False)

        if batch is not None:
            x = global_mean_pool(x, batch)

        return x


class IntegratedGradients:
    """
    Integrated Gradients implementation for feature attribution.

    Computes the importance of each node/feature in the input graph
    with respect to the model's prediction.

    Reference: Sundararajan et al., "Axiomatic Attribution for Deep Networks", 2017
    """

    def __init__(self, model: PolymerGNN, target_class: int, 
                 n_steps: int = 50):
        """
        Args:
            model: The PolymerGNN model
            target_class: The class index to compute attributions for
            n_steps: Number of integration steps
        """
        self.model = model
        self.target_class = target_class
        self.n_steps = n_steps
        self.logger = get_logger(__name__)

    def compute(self, x: torch.Tensor, edge_index: torch.Tensor,
                batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Compute Integrated Gradients for the input graph.

        Args:
            x: Input node features [num_nodes, input_dim]
            edge_index: Edge index [2, num_edges]
            batch: Batch vector [num_nodes] (optional)

        Returns:
            attributions: Node-feature attributions [num_nodes, input_dim]
        """
        self.model.eval()
        x = x.cpu()
        edge_index = edge_index.cpu()
        if batch is not None:
            batch = batch.cpu()

        # Baseline: zero vector
        baseline = torch.zeros_like(x)

        # Generate interpolated inputs
        alphas = torch.linspace(0, 1, steps=self.n_steps)
        attributions = torch.zeros_like(x)

        with torch.no_grad():
            for alpha in alphas:
                # Interpolate between baseline and input
                interpolated_x = baseline + alpha * (x - baseline)
                interpolated_x.requires_grad_(True)

                # Forward pass
                output = self.model(interpolated_x, edge_index, batch)
                
                # Select target class logit
                if batch is not None:
                    # Graph-level prediction
                    target_logits = output[:, self.target_class]
                    # Sum over batch if multiple graphs
                    target_logit = target_logits.sum()
                else:
                    # Node-level prediction
                    target_logits = output[:, self.target_class]
                    target_logit = target_logits.mean()

                # Backward pass
                target_logit.backward()

                # Accumulate gradients
                attributions += interpolated_x.grad.detach()

                # Reset gradients
                if interpolated_x.grad is not None:
                    interpolated_x.grad.zero_()

        # Scale by (input - baseline)
        attributions = attributions / self.n_steps
        attributions = attributions * (x - baseline)

        return attributions


def create_model_from_config(config: Dict[str, Any]) -> PolymerGNN:
    """
    Create a PolymerGNN model from a configuration dictionary.

    Args:
        config: Dictionary containing model hyperparameters

    Returns:
        Initialized PolymerGNN model

    Raises:
        ValueError: If config violates architecture constraints
    """
    input_dim = config.get('input_dim', 64)  # Default based on typical molecular features
    hidden_dim = config.get('hidden_dim', 128)
    num_layers = config.get('num_layers', 3)
    num_classes = config.get('num_classes', 4)
    dropout = config.get('dropout', 0.2)

    # Validate constraints
    if hidden_dim > 128:
        raise ValueError(f"Configuration error: hidden_dim ({hidden_dim}) exceeds max 128")
    if num_layers > 3:
        raise ValueError(f"Configuration error: num_layers ({num_layers}) exceeds max 3")

    logger = get_logger(__name__)
    logger.info(f"Creating PolymerGNN with config: {config}")

    return PolymerGNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        num_classes=num_classes,
        dropout=dropout
    )


def validate_model_constraints(model: PolymerGNN) -> Tuple[bool, List[str]]:
    """
    Validate that a model meets the architecture constraints.

    Args:
        model: The PolymerGNN model to validate

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations = []

    if model.hidden_dim > 128:
        violations.append(f"hidden_dim ({model.hidden_dim}) > 128")

    if model.num_layers > 3:
        violations.append(f"num_layers ({model.num_layers}) > 3")

    if model.num_layers < 1:
        violations.append(f"num_layers ({model.num_layers}) < 1")

    is_valid = len(violations) == 0
    return is_valid, violations