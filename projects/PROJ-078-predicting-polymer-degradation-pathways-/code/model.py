from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Batch
from typing import Optional, Dict, Any, Tuple, List
import numpy as np

# Import existing data models if needed for type hinting, though not strictly required for the model class itself
# from data_models import MolecularGraph 

class PolymerGNN(nn.Module):
    """
    Lightweight Graph Neural Network for Polymer Degradation Pathway Prediction.
    
    Constraints:
    - Max 3 layers (including input and output layers)
    - Hidden dimension <= 128
    - CPU-only design (no CUDA-specific optimizations enforced here, but compatible)
    
    Architecture:
    - Input Layer: Maps node features to hidden_dim
    - 1-2 GCN Convolutional Layers (configurable, max 2 conv layers to keep total depth <= 3)
    - Global Mean Pooling
    - Output Layer: Maps hidden_dim to num_classes
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        num_classes: int = 3,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super(PolymerGNN, self).__init__()
        
        # Constraint Validation
        if num_layers > 2:
            raise ValueError(f"Number of convolutional layers must be <= 2 (total depth <= 3). Got {num_layers}.")
        if hidden_dim > 128:
            raise ValueError(f"Hidden dimension must be <= 128. Got {hidden_dim}.")
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Input projection
        self.conv1 = GCNConv(input_dim, hidden_dim)
        
        # Additional convolutional layers
        self.convs = nn.ModuleList()
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
        
        # Output projection
        self.fc_out = nn.Linear(hidden_dim, num_classes)
        
        # BatchNorm for stability
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bns = nn.ModuleList([nn.BatchNorm1d(hidden_dim) for _ in range(num_layers - 1)])

    def forward(self, data: Batch) -> torch.Tensor:
        """
        Forward pass for a batch of graphs.
        
        Args:
            data: torch_geometric.data.Batch object containing:
                  - x: Node features [num_nodes, input_dim]
                  - edge_index: Edge connectivity [2, num_edges]
                  - batch: Batch vector [num_nodes] mapping nodes to graphs
        
        Returns:
            Logits tensor [num_graphs, num_classes]
        """
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        # First layer
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Subsequent layers
        for conv, bn in zip(self.convs, self.bns):
            x = conv(x, edge_index)
            x = bn(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Global pooling
        x = global_mean_pool(x, batch)
        
        # Output layer
        x = self.fc_out(x)
        
        return x


class IntegratedGradients:
    """
    Integrated Gradients implementation for feature attribution.
    
    Computes the contribution of each node feature to the model's prediction
    by integrating gradients along a path from a baseline to the input.
    """
    
    def __init__(self, model: PolymerGNN, device: torch.device = None):
        self.model = model
        self.device = device if device else torch.device('cpu')
        self.model.to(self.device)
        self.model.eval()

    def compute(
        self,
        data: Batch,
        baseline: Optional[torch.Tensor] = None,
        steps: int = 50,
        target_class: Optional[int] = None
    ) -> torch.Tensor:
        """
        Compute Integrated Gradients for a batch of graphs.
        
        Args:
            data: Batch of graphs.
            baseline: Baseline input tensor (same shape as data.x). Defaults to zeros.
            steps: Number of interpolation steps.
            target_class: Specific class index to compute attribution for. If None, returns for all classes.
        
        Returns:
            Attribution tensor of shape [num_nodes, input_dim] (or [num_nodes, 1] if target_class specified).
        """
        data = data.to(self.device)
        x = data.x.requires_grad_(True)
        
        if baseline is None:
            baseline = torch.zeros_like(x, device=self.device)
        
        # Interpolate between baseline and input
        # x_alpha = baseline + alpha * (x - baseline)
        # We compute gradients at each alpha step and sum them.
        
        attributions = torch.zeros_like(x)
        
        # We need to handle the graph structure (edge_index, batch) which are constant
        # The input x varies.
        
        with torch.no_grad():
            # Pre-compute edge_index and batch on device
            edge_index = data.edge_index
            batch = data.batch
        
        for i in range(steps):
            alpha = (i + 0.5) / steps
            x_alpha = baseline + alpha * (x - baseline)
            
            # Create a temporary data object with the interpolated features
            # We must clone to avoid modifying the original data.x reference if it's shared
            data_alpha = Batch()
            data_alpha.x = x_alpha
            data_alpha.edge_index = edge_index
            data_alpha.batch = batch
            # Copy other attributes if necessary, but usually x, edge_index, batch are enough for forward
            if hasattr(data, 'y'):
                data_alpha.y = data.y
            
            # Forward pass
            output = self.model(data_alpha)
            
            if target_class is not None:
                # Select specific class score
                score = output[:, target_class].sum()
            else:
                # Sum of all scores (or could be specific class logic)
                # For standard IG, we usually pick a target. If none, we might sum or pick max.
                # Here we sum to get total attribution magnitude, or return a tensor for each class.
                # To keep it simple and standard: if no target, return attribution for the predicted class or sum.
                # Let's assume we want attribution for the predicted class for each graph in batch.
                # However, for a generic return, let's just return the gradient of the sum of all outputs.
                score = output.sum()
            
            # Backward
            score.backward(retain_graph=True)
            
            # Accumulate gradients
            attributions += x.grad
            x.grad.zero_()
        
        # Scale by (Input - Baseline) / steps
        # The formula is: (Input - Baseline) * integral(grad) approx (Input - Baseline) * sum(grad) / steps
        # Wait, the standard formula is: (Input - Baseline) * (1/steps) * sum(grad)
        # My loop summed the gradients. So:
        attributions = (x - baseline) * (attributions / steps)
        
        return attributions.cpu()


def create_model_from_config(config: Dict[str, Any]) -> PolymerGNN:
    """
    Factory function to create a PolymerGNN instance from a configuration dictionary.
    
    Args:
        config: Dictionary containing 'input_dim', 'hidden_dim', 'num_classes', 'num_layers'.
    
    Returns:
        Configured PolymerGNN instance.
    """
    input_dim = config.get('input_dim', 64)
    hidden_dim = config.get('hidden_dim', 128)
    num_classes = config.get('num_classes', 3)
    num_layers = config.get('num_layers', 2)
    dropout = config.get('dropout', 0.1)
    
    return PolymerGNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_classes=num_classes,
        num_layers=num_layers,
        dropout=dropout
    )


def validate_model_constraints(model: PolymerGNN) -> Tuple[bool, str]:
    """
    Validates that the model meets the architectural constraints:
    - Total layers <= 3 (Input + Conv + Output) -> Conv layers <= 2
    - Hidden dim <= 128
    
    Args:
        model: The PolymerGNN instance to validate.
    
    Returns:
        Tuple (is_valid, message)
    """
    if model.hidden_dim > 128:
        return False, f"Hidden dimension {model.hidden_dim} exceeds limit of 128."
    
    if model.num_layers > 2:
        return False, f"Number of convolutional layers {model.num_layers} exceeds limit of 2 (total depth {model.num_layers + 1})."
    
    return True, "Model constraints satisfied."