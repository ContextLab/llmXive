from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Batch
from typing import Optional, Dict, Any, Tuple
import logging

from utils import get_logger

logger = get_logger(__name__)

class PolymerGNN(nn.Module):
    """
    Lightweight Graph Neural Network for polymer degradation pathway prediction.
    
    Constraints (FR-003):
    - Maximum 3 layers
    - Hidden dimension <= 128
    - CPU-only execution (no CUDA dependencies enforced at inference time)
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        output_dim: int = 3,
        dropout: float = 0.1
    ):
        """
        Initialize the GNN model.
        
        Args:
            input_dim: Number of input node features (e.g., atom features)
            hidden_dim: Hidden dimension size (must be <= 128)
            num_layers: Number of GCN layers (must be <= 3)
            output_dim: Number of degradation pathway classes
            dropout: Dropout rate for regularization
        """
        super().__init__()
        
        # Validate constraints
        if hidden_dim > 128:
            raise ValueError(f"hidden_dim must be <= 128, got {hidden_dim}")
        if num_layers > 3:
            raise ValueError(f"num_layers must be <= 3, got {num_layers}")
        if num_layers < 1:
            raise ValueError(f"num_layers must be >= 1, got {num_layers}")
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Build GCN layers
        self.convs = nn.ModuleList()
        
        # First layer
        self.convs.append(GCNConv(input_dim, hidden_dim))
        
        # Intermediate layers
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
        
        # Dropout layers
        self.dropout = dropout
        self.batch_norms = nn.ModuleList([
            nn.BatchNorm1d(hidden_dim) for _ in range(num_layers)
        ])
        
        # Output layer
        self.fc = nn.Linear(hidden_dim, output_dim)
        
        logger.info(
            f"Initialized PolymerGNN: input_dim={input_dim}, "
            f"hidden_dim={hidden_dim}, num_layers={num_layers}, output_dim={output_dim}"
        )
    
    def forward(self, data: Batch) -> torch.Tensor:
        """
        Forward pass through the GNN.
        
        Args:
            data: Batch of molecular graphs (PyTorch Geometric Batch object)
                Expected attributes: x (node features), edge_index, batch
        
        Returns:
            torch.Tensor: Logits for each graph in the batch (shape: [batch_size, output_dim])
        """
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            x = self.batch_norms[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Global pooling to get graph-level representation
        x = global_mean_pool(x, batch)
        
        # Final classification layer
        logits = self.fc(x)
        
        return logits


class IntegratedGradients:
    """
    Integrated Gradients for feature attribution on GNN models.
    
    Computes the importance of each node/atom in the molecular graph
    by integrating gradients along a path from a baseline to the input.
    """
    
    def __init__(
        self,
        model: PolymerGNN,
        baseline: Optional[torch.Tensor] = None
    ):
        """
        Initialize Integrated Gradients.
        
        Args:
            model: The trained PolymerGNN model
            baseline: Baseline input tensor (default: zero tensor of same shape as input)
        """
        self.model = model
        self.baseline = baseline
        self.model.eval()
    
    def compute_gradients(
        self,
        data: Batch,
        target_class: Optional[int] = None,
        steps: int = 50
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute Integrated Gradients for a batch of molecular graphs.
        
        Args:
            data: Batch of molecular graphs
            target_class: Specific class to compute attributions for.
                         If None, computes for the predicted class of each sample.
            steps: Number of integration steps (higher = more accurate)
        
        Returns:
            Tuple of (attributions, predicted_classes)
            - attributions: Node-level attributions (shape: [num_nodes, input_dim])
            - predicted_classes: Predicted class for each graph in batch
        """
        self.model.train()  # Enable gradients
        
        # Move data to device
        device = next(self.model.parameters()).device
        x = data.x.to(device)
        edge_index = data.edge_index.to(device)
        batch = data.batch.to(device)
        
        # Determine target class for each sample
        with torch.no_grad():
            logits = self.model(data)
            probs = F.softmax(logits, dim=-1)
            predicted_classes = torch.argmax(probs, dim=-1)
        
        if target_class is not None:
            target_classes = torch.full_like(predicted_classes, target_class)
        else:
            target_classes = predicted_classes
        
        # Prepare baseline
        if self.baseline is not None:
            baseline = self.baseline.to(device)
        else:
            baseline = torch.zeros_like(x)
        
        # Generate interpolated inputs
        alpha = torch.linspace(0, 1, steps, device=device)
        
        # Accumulate gradients
        attributions = torch.zeros_like(x, device=device)
        
        for i in range(steps):
            # Create interpolated input
            alpha_i = alpha[i]
            interpolated_x = baseline + alpha_i * (x - baseline)
            
            # Create temporary batch with interpolated features
            temp_data = Batch(
                x=interpolated_x,
                edge_index=edge_index,
                batch=batch,
                ptr=data.ptr if hasattr(data, 'ptr') else None
            )
            
            # Compute gradients
            temp_data.x.requires_grad_(True)
            
            output = self.model(temp_data)
            
            # Select target class output for each sample
            if target_class is not None:
                # All samples target same class
                target_output = output[:, target_class]
            else:
                # Each sample targets its own predicted class
                target_output = output[torch.arange(len(output)), target_classes]
            
            # Backpropagate
            target_output.sum().backward()
            
            # Accumulate gradients
            with torch.no_grad():
                grad = temp_data.x.grad
                if grad is not None:
                    attributions += grad
            
            # Clear gradients
            temp_data.x.grad = None
        
        # Scale by (input - baseline)
        attributions = attributions / steps * (x - baseline)
        
        # Reset model to eval
        self.model.eval()
        
        return attributions, predicted_classes


def create_model_from_config(config: Dict[str, Any]) -> PolymerGNN:
    """
    Create a PolymerGNN instance from a configuration dictionary.
    
    Args:
        config: Dictionary containing model parameters
            - input_dim: int
            - hidden_dim: int (default: 64, max: 128)
            - num_layers: int (default: 2, max: 3)
            - output_dim: int
            - dropout: float (default: 0.1)
    
    Returns:
        PolymerGNN: Initialized model instance
    """
    input_dim = config.get('input_dim', 64)
    hidden_dim = min(config.get('hidden_dim', 64), 128)
    num_layers = min(config.get('num_layers', 2), 3)
    output_dim = config.get('output_dim', 3)
    dropout = config.get('dropout', 0.1)
    
    model = PolymerGNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        output_dim=output_dim,
        dropout=dropout
    )
    
    return model


def validate_model_constraints(model: PolymerGNN) -> bool:
    """
    Validate that a PolymerGNN model meets the architectural constraints.
    
    Constraints:
    - Number of layers <= 3
    - Hidden dimension <= 128
    
    Args:
        model: The PolymerGNN model to validate
    
    Returns:
        bool: True if all constraints are satisfied, False otherwise
    """
    constraints_met = True
    
    # Check number of layers
    if model.num_layers > 3:
        logger.error(
            f"Constraint violation: num_layers={model.num_layers} > 3"
        )
        constraints_met = False
    
    # Check hidden dimension
    if model.hidden_dim > 128:
        logger.error(
            f"Constraint violation: hidden_dim={model.hidden_dim} > 128"
        )
        constraints_met = False
    
    if constraints_met:
        logger.info(
            f"Model constraints validated: num_layers={model.num_layers}, "
            f"hidden_dim={model.hidden_dim}"
        )
    
    return constraints_met