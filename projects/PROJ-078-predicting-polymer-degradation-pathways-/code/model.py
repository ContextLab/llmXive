from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Batch
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import logging
import os
from pathlib import Path

from utils import get_logger, get_project_paths
from data_models import PolymerRecord, MolecularGraph

logger = get_logger(__name__)

class PolymerGNN(nn.Module):
    """
    Lightweight Graph Neural Network for polymer degradation prediction.
    Constraints: <= 3 layers, hidden_dim <= 128, CPU-only.
    """
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int = 128, num_layers: int = 3, num_classes: int = 3):
        super().__init__()
        self.num_layers = num_layers
        self.hidden_dim = hidden_dim

        # Input projection
        self.lin_in = nn.Linear(node_dim, hidden_dim)
        if edge_dim > 0:
            self.lin_edge = nn.Linear(edge_dim, hidden_dim)

        # GCN layers
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            in_dim = hidden_dim if i > 0 else hidden_dim
            out_dim = hidden_dim
            conv = GCNConv(in_dim, out_dim)
            self.convs.append(conv)

        # Output layer
        self.lin_out = nn.Linear(hidden_dim, num_classes)

        # Batch norm and dropout for stability
        self.bns = nn.ModuleList([nn.BatchNorm1d(hidden_dim) for _ in range(num_layers)])
        self.dropout = nn.Dropout(0.1)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: Optional[torch.Tensor] = None,
                batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: Node features [N, node_dim]
            edge_index: Edge indices [2, E]
            edge_attr: Edge features [E, edge_dim] (optional)
            batch: Batch vector for pooling [N] (optional)
        Returns:
            logits: [B, num_classes] if batch provided, else [N, num_classes]
        """
        x = self.lin_in(x)
        
        # Handle edge features if present
        if edge_attr is not None and hasattr(self, 'lin_edge'):
            edge_attr = self.lin_edge(edge_attr)

        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if edge_attr is not None and i == 0:
                # Simple edge feature aggregation could go here if needed
                pass
            
            x = self.bns[i](x)
            x = F.relu(x)
            x = self.dropout(x)

        if batch is not None:
            x = global_mean_pool(x, batch)

        x = self.lin_out(x)
        return x

class IntegratedGradients:
    """
    Computes Integrated Gradients feature attributions for a PolymerGNN model.
    Implements the formula: IG_i(x) = (x_i - x'_i) * integral_alpha=0^1 [
        dF(x' + alpha * (x - x')) / dx_i ] d_alpha
    """
    def __init__(self, model: PolymerGNN, n_steps: int = 50, baseline: Optional[torch.Tensor] = None):
        """
        Args:
            model: The trained PolymerGNN model.
            n_steps: Number of integration steps (higher = more accurate, slower).
            baseline: Baseline input tensor. If None, zeros are used.
        """
        self.model = model
        self.n_steps = n_steps
        self.baseline = baseline
        self.model.eval()

    def compute_attributions(self, data: Batch, target_class: Optional[int] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Computes Integrated Gradients for the input graph data.
        
        Args:
            data: A PyTorch Geometric Batch object containing x, edge_index, batch, etc.
            target_class: The class index to compute attributions for. If None, uses the predicted class.
        
        Returns:
            attributions: Tensor of shape [N, node_dim] representing node feature attributions.
            baseline_diff: Tensor of shape [N, node_dim] representing (x - baseline).
        """
        with torch.no_grad():
            x = data.x.clone().requires_grad_(True)
            edge_index = data.edge_index
            batch = data.batch if hasattr(data, 'batch') else None
            edge_attr = data.edge_attr if hasattr(data, 'edge_attr') else None

            # Determine baseline
            if self.baseline is None:
                baseline_x = torch.zeros_like(x)
            else:
                baseline_x = self.baseline.to(x.device)

            # Determine target class
            if target_class is None:
                # Run forward pass to get prediction
                outputs = self.model(x, edge_index, edge_attr, batch)
                if batch is not None:
                    outputs = outputs.squeeze()
                    if outputs.dim() == 1:
                        target_class = torch.argmax(outputs).item()
                    else:
                        # For batched graph-level predictions
                        target_class = torch.argmax(outputs, dim=-1).item()
                else:
                    target_class = torch.argmax(outputs, dim=-1).item()
            
            # Ensure target_class is a scalar integer for indexing
            if isinstance(target_class, torch.Tensor):
                target_class = target_class.item()

            # Integration
            alpha_values = torch.linspace(0, 1, steps=self.n_steps, device=x.device)
            integrated_gradients = torch.zeros_like(x)

            for alpha in alpha_values:
                # Interpolate between baseline and input
                interpolated_x = baseline_x + alpha * (x - baseline_x)
                interpolated_x.requires_grad_(True)

                # Forward pass
                outputs = self.model(interpolated_x, edge_index, edge_attr, batch)
                
                # Select the target class logit
                if batch is not None:
                    # Graph-level prediction: select per graph in batch
                    # Assuming outputs shape [num_graphs, num_classes]
                    if outputs.dim() == 2:
                        target_logits = outputs[:, target_class]
                    else:
                        # Fallback if model output shape is unexpected
                        target_logits = outputs
                else:
                    # Node-level or single graph
                    if outputs.dim() == 2:
                        target_logits = outputs[:, target_class]
                    else:
                        target_logits = outputs

                # Backward pass to get gradients
                target_logits.sum().backward()

                # Accumulate gradients
                if interpolated_x.grad is not None:
                    integrated_gradients += interpolated_x.grad.detach()
                
                # Clear gradients for next step
                interpolated_x.grad = None

            # Scale by (x - baseline)
            diff = x - baseline_x
            attributions = diff * (integrated_gradients / self.n_steps)

            return attributions, diff

def create_model_from_config(config: Dict[str, Any]) -> PolymerGNN:
    """
    Factory function to create a PolymerGNN instance from a config dictionary.
    """
    node_dim = config.get('node_dim', 64) # Default or read from data
    edge_dim = config.get('edge_dim', 0)
    hidden_dim = config.get('hidden_dim', 128)
    num_layers = config.get('num_layers', 3)
    num_classes = config.get('num_classes', 3)

    # Validate constraints
    if hidden_dim > 128:
        logger.warning(f"Hidden dim {hidden_dim} exceeds constraint of 128. Clamping.")
        hidden_dim = 128
    if num_layers > 3:
        logger.warning(f"Num layers {num_layers} exceeds constraint of 3. Clamping.")
        num_layers = 3

    return PolymerGNN(node_dim, edge_dim, hidden_dim, num_layers, num_classes)

def validate_model_constraints(model: PolymerGNN) -> bool:
    """
    Validates that the model meets the lightweight constraints:
    - <= 3 layers
    - hidden_dim <= 128
    """
    valid = True
    if model.num_layers > 3:
        logger.error(f"Model has {model.num_layers} layers, exceeds limit of 3.")
        valid = False
    if model.hidden_dim > 128:
        logger.error(f"Model has hidden_dim {model.hidden_dim}, exceeds limit of 128.")
        valid = False
    return valid

def compute_feature_importance(model: PolymerGNN, data: Batch, target_class: Optional[int] = None, 
                               n_steps: int = 50) -> Dict[str, Any]:
    """
    Computes feature importance scores using Integrated Gradients.
    
    Args:
        model: Trained PolymerGNN model.
        data: Batched graph data.
        target_class: Specific class to analyze.
        n_steps: Integration steps.
        
    Returns:
        Dictionary containing attribution maps and statistics.
    """
    ig = IntegratedGradients(model, n_steps=n_steps)
    attributions, diff = ig.compute_attributions(data, target_class)
    
    # Aggregate attributions per node (sum of absolute values across features)
    node_importance = torch.abs(attributions).sum(dim=1)
    
    # Aggregate per graph if batched
    if hasattr(data, 'batch'):
        graph_importance = torch.zeros(data.num_graphs, device=data.x.device)
        for i in range(data.num_graphs):
            mask = data.batch == i
            graph_importance[i] = node_importance[mask].sum()
        
        return {
            "node_attributions": attributions.detach().cpu().numpy(),
            "node_importance": node_importance.detach().cpu().numpy(),
            "graph_importance": graph_importance.detach().cpu().numpy(),
            "baseline_diff": diff.detach().cpu().numpy()
        }
    else:
        return {
            "node_attributions": attributions.detach().cpu().numpy(),
            "node_importance": node_importance.detach().cpu().numpy(),
            "graph_importance": node_importance.detach().cpu().numpy(),
            "baseline_diff": diff.detach().cpu().numpy()
        }