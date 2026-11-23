from __future__ import annotations

import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Batch, Data
from torch_geometric.utils import dropout_adj

from utils import get_logger, get_project_paths

# Constants for architecture constraints
MAX_LAYERS = 3
MAX_HIDDEN_DIM = 128
ACTIVATION = F.relu
POOLING = global_mean_pool

logger = get_logger(__name__)


class PolymerGNN(nn.Module):
    """
    Lightweight Graph Neural Network for polymer degradation pathway prediction.

    Architecture Constraints:
      - Layers: <= 3 (GCNConv)
      - Hidden Dim: <= 128
      - Activation: ReLU
      - Pooling: Mean (global_mean_pool)
      - CPU-only compatible (no CUDA specific ops forced)

    Input Shape: [num_nodes, num_features] (node_features)
    Output Shape: [num_nodes, num_classes] (if node-level) or [num_graphs, num_classes] (if graph-level)
    This implementation assumes graph-level classification based on the task context
    of predicting degradation pathways for the whole polymer record.
    """

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.1,
        activation: str = "relu"
    ):
        super().__init__()

        # Validate constraints
        if num_layers > MAX_LAYERS:
            raise ValueError(f"num_layers ({num_layers}) exceeds MAX_LAYERS ({MAX_LAYERS})")
        if hidden_dim > MAX_HIDDEN_DIM:
            raise ValueError(f"hidden_dim ({hidden_dim}) exceeds MAX_HIDDEN_DIM ({MAX_HIDDEN_DIM})")
        
        self.num_layers = num_layers
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        self.num_classes = num_classes

        # Activation function
        if activation == "relu":
            self.act = F.relu
        else:
            raise ValueError(f"Unsupported activation: {activation}")

        # Build layers
        self.convs = nn.ModuleList()
        
        # First layer: input -> hidden
        self.convs.append(GCNConv(num_features, hidden_dim))
        self.bns = nn.ModuleList()
        self.bns.append(nn.BatchNorm1d(hidden_dim))

        # Middle layers: hidden -> hidden
        for _ in range(num_layers - 2):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
            self.bns.append(nn.BatchNorm1d(hidden_dim))

        # Last layer: hidden -> hidden (if > 1 layer) or hidden -> classes (if 1 layer logic, but we usually project at end)
        # Standard pattern: L-1 GCN, then final projection
        if num_layers > 1:
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
            self.bns.append(nn.BatchNorm1d(hidden_dim))

        # Final projection head: hidden -> classes
        self.head = nn.Linear(hidden_dim, num_classes)

        self._reset_parameters()

    def _reset_parameters(self):
        for conv in self.convs:
            conv.reset_parameters()
        for bn in self.bns:
            bn.reset_parameters()
        nn.init.xavier_uniform_(self.head.weight)
        nn.init.zeros_(self.head.bias)

    def forward(self, data: Data) -> torch.Tensor:
        """
        Forward pass.

        Args:
            data: PyG Data object containing x, edge_index, batch, etc.
        
        Returns:
            Tensor of shape [num_graphs, num_classes]
        """
        x, edge_index, batch = data.x, data.edge_index, data.batch

        # Layer 1
        x = self.convs[0](x, edge_index)
        x = self.bns[0](x)
        x = self.act(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Middle layers
        for i in range(1, len(self.convs)):
            x = self.convs[i](x, edge_index)
            x = self.bns[i](x)
            x = self.act(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # Global pooling (Mean pooling)
        x = POOLING(x, batch)

        # Final classification head
        x = self.head(x)
        return x


class IntegratedGradients:
    """
    Integrated Gradients implementation for feature attribution.
    Computes the importance of input features (atoms/bonds) for a prediction.
    """

    def __init__(self, model: PolymerGNN, n_steps: int = 50):
        self.model = model
        self.n_steps = n_steps
        self.model.eval()

    def compute(self, data: Data, baseline: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Compute Integrated Gradients for a batch of graphs.

        Args:
            data: PyG Data object.
            baseline: Baseline input (e.g., zero tensor). Defaults to zeros.
        
        Returns:
            Tensor of shape [num_nodes, num_features] representing importance scores.
        """
        self.model.zero_grad()
        self.model.train() # Enable gradients

        if baseline is None:
            baseline = torch.zeros_like(data.x, device=data.x.device)

        # Interpolate between baseline and input
        alphas = torch.linspace(0, 1, self.n_steps, device=data.x.device).view(-1, 1)
        
        # We need to compute gradients for each alpha step
        # To do this efficiently, we iterate or use a loop over steps
        # Since PyG handles batching, we might need to be careful with graph boundaries
        # But for simplicity in this architecture, we treat x as a tensor.
        
        # Accumulate gradients
        accumulated_gradients = torch.zeros_like(data.x)

        for alpha in alphas:
            # Interpolated input
            interpolated_x = baseline + alpha * (data.x - baseline)
            
            # Create a temporary data object with interpolated features
            # We must preserve the graph structure (edge_index, batch)
            interp_data = Data(
                x=interpolated_x,
                edge_index=data.edge_index,
                batch=data.batch,
                y=data.y if hasattr(data, 'y') else None
            )

            # Forward pass
            output = self.model(interp_data)
            
            # We want the gradient w.r.t input x for the specific class prediction
            # For multi-class, we can sum or pick a specific class. 
            # Here we compute gradient of the sum of outputs (or target class if provided)
            # Assuming we want to explain the prediction for the ground truth class if available,
            # or just the magnitude of the output.
            # For general attribution, we sum the output logits.
            output.sum().backward()

            # Accumulate gradients
            accumulated_gradients += interp_data.x.grad

            # Clear grads for next step
            self.model.zero_grad()

        # Average gradients
        avg_gradients = accumulated_gradients / self.n_steps

        # Approximation: (Input - Baseline) * Average Gradient
        attribution = (data.x - baseline) * avg_gradients

        self.model.zero_grad()
        self.model.eval()

        return attribution


def create_model_from_config(config: Dict[str, Any]) -> PolymerGNN:
    """
    Factory function to create a PolymerGNN instance from a configuration dictionary.
    Ensures constraints are respected.
    """
    num_features = config.get('num_features', 10) # Default, overridden by data
    num_classes = config.get('num_classes', 3)
    hidden_dim = min(config.get('hidden_dim', 128), MAX_HIDDEN_DIM)
    num_layers = min(config.get('num_layers', 2), MAX_LAYERS)
    dropout = config.get('dropout', 0.1)
    activation = config.get('activation', 'relu')

    logger.info(f"Creating PolymerGNN: layers={num_layers}, hidden={hidden_dim}, dropout={dropout}")
    
    return PolymerGNN(
        num_features=num_features,
        num_classes=num_classes,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout,
        activation=activation
    )


def validate_model_constraints(model: PolymerGNN) -> bool:
    """
    Validates that the model adheres to the project constraints.
    """
    valid = True
    if model.num_layers > MAX_LAYERS:
        logger.error(f"Constraint Violation: Layers {model.num_layers} > {MAX_LAYERS}")
        valid = False
    if model.hidden_dim > MAX_HIDDEN_DIM:
        logger.error(f"Constraint Violation: Hidden Dim {model.hidden_dim} > {MAX_HIDDEN_DIM}")
        valid = False
    return valid


def compute_feature_importance(
    model: PolymerGNN,
    data: Data,
    n_steps: int = 50
) -> List[Dict[str, Any]]:
    """
    Computes feature importance using Integrated Gradients.
    
    Returns a list of dictionaries with atom/bond importance scores.
    """
    ig = IntegratedGradients(model, n_steps=n_steps)
    scores = ig.compute(data)
    
    # Normalize scores for reporting
    abs_scores = torch.abs(scores).sum(dim=1) # Sum across features per node
    max_score = abs_scores.max()
    if max_score > 0:
        normalized_scores = abs_scores / max_score
    else:
        normalized_scores = abs_scores

    result = []
    for i, score in enumerate(normalized_scores):
        result.append({
            "atom_index": int(i),
            "importance_score": float(abs_scores[i].item()),
            "normalized_score": float(score.item())
        })
    
    return result


def main():
    """
    Main entry point for model.py when run as a script.
    Performs a sanity check: instantiates model, runs a dummy forward pass,
    and validates constraints.
    """
    logger.info("Running model.py sanity check...")
    
    # Create a dummy configuration
    config = {
        "num_features": 10,
        "num_classes": 3,
        "hidden_dim": 64,
        "num_layers": 2,
        "dropout": 0.1
    }

    try:
        model = create_model_from_config(config)
        
        if not validate_model_constraints(model):
            raise RuntimeError("Model constraints validation failed.")

        # Create dummy data
        num_nodes = 20
        num_edges = 40
        x = torch.randn(num_nodes, config['num_features'])
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        batch = torch.zeros(num_nodes, dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index, batch=batch)

        # Forward pass
        model.eval()
        with torch.no_grad():
            output = model(data)
        
        logger.info(f"Forward pass successful. Output shape: {output.shape}")
        
        # Test Integrated Gradients
        model.train()
        importances = compute_feature_importance(model, data, n_steps=10)
        logger.info(f"Feature importance computed for {len(importances)} nodes.")
        
        logger.info("Model sanity check PASSED.")
        
    except Exception as e:
        logger.error(f"Model sanity check FAILED: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Setup logging
    setup_logging_level = logging.INFO
    logger = get_logger(__name__)
    logger.setLevel(setup_logging_level)
    
    main()
