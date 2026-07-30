from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Batch
from typing import Optional, Dict, Any, List, Tuple
import logging
import json
import os

logger = logging.getLogger(__name__)

class PolymerGNN(nn.Module):
    """
    Lightweight Graph Neural Network for polymer degradation prediction.
    
    Constraints:
    - Maximum 3 layers (as per FR-003)
    - Hidden dimension <= 128 (as per FR-003)
    - CPU-only design (no CUDA dependencies)
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        output_dim: int = 3,
        num_layers: int = 3,
        dropout: float = 0.1
    ):
        """
        Initialize the GNN model.
        
        Args:
            input_dim: Dimension of input node features
            hidden_dim: Hidden layer dimension (must be <= 128)
            output_dim: Number of output classes (degradation pathways)
            num_layers: Number of GNN layers (must be <= 3)
            dropout: Dropout probability
        
        Raises:
            ValueError: If constraints are violated
        """
        super().__init__()
        
        # Validate constraints
        if num_layers > 3:
            raise ValueError(f"num_layers must be <= 3, got {num_layers}")
        if hidden_dim > 128:
            raise ValueError(f"hidden_dim must be <= 128, got {hidden_dim}")
        
        self.num_layers = num_layers
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        
        # Build GNN layers
        self.convs = nn.ModuleList()
        
        # First layer
        self.convs.append(GCNConv(input_dim, hidden_dim))
        self.bns = nn.ModuleList([nn.BatchNorm1d(hidden_dim)])
        
        # Middle layers
        for _ in range(num_layers - 2):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
            self.bns.append(nn.BatchNorm1d(hidden_dim))
        
        # Last layer (if num_layers > 1)
        if num_layers > 1:
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
            self.bns.append(nn.BatchNorm1d(hidden_dim))
        
        # Output layer
        self.output_layer = nn.Linear(hidden_dim, output_dim)
        
        logger.info(f"Initialized PolymerGNN with {num_layers} layers, hidden_dim={hidden_dim}")
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
               batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through the GNN.
        
        Args:
            x: Node features tensor [num_nodes, input_dim]
            edge_index: Edge indices tensor [2, num_edges]
            batch: Batch vector for pooling (optional)
        
        Returns:
            Graph-level predictions [num_graphs, output_dim]
        """
        # Apply GNN layers
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            x = self.bns[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Global pooling
        if batch is not None:
            x = global_mean_pool(x, batch)
        else:
            # If no batch provided, assume single graph
            x = x.mean(dim=0, keepdim=True)
        
        # Output layer
        x = self.output_layer(x)
        
        return x
    
    def get_num_params(self) -> int:
        """Return total number of parameters."""
        return sum(p.numel() for p in self.parameters())


class IntegratedGradients:
    """
    Integrated Gradients implementation for feature importance.
    
    Computes feature attributions by integrating gradients along a path
    from a baseline to the input.
    """
    
    def __init__(self, model: PolymerGNN, device: str = 'cpu'):
        """
        Initialize Integrated Gradients.
        
        Args:
            model: Trained PolymerGNN model
            device: Device to run computations on
        """
        self.model = model
        self.device = device
        self.model.to(device)
        self.model.eval()
        
        logger.info("Initialized IntegratedGradients")
    
    def compute_attributions(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        baseline: Optional[torch.Tensor] = None,
        steps: int = 50,
        target_class: Optional[int] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute Integrated Gradients attributions for node features.
        
        Args:
            x: Input node features [num_nodes, input_dim]
            edge_index: Edge indices [2, num_edges]
            baseline: Baseline features (default: zero vector)
            steps: Number of interpolation steps
            target_class: Target class index (if None, use argmax)
        
        Returns:
            Tuple of (node_attributions, edge_attributions)
        """
        x = x.to(self.device)
        edge_index = edge_index.to(self.device)
        
        if baseline is None:
            baseline = torch.zeros_like(x)
        else:
            baseline = baseline.to(self.device)
        
        # Generate interpolation path
        alphas = torch.linspace(0, 1, steps).to(self.device)
        
        # Initialize attributions
        node_attributions = torch.zeros_like(x)
        
        with torch.no_grad():
            self.model.eval()
            
            for alpha in alphas:
                # Interpolate between baseline and input
                interpolated_x = baseline + alpha * (x - baseline)
                interpolated_x.requires_grad_(True)
                
                # Forward pass
                output = self.model(interpolated_x, edge_index)
                
                # Select target class
                if target_class is not None:
                    score = output[:, target_class]
                else:
                    score = output.argmax(dim=1)
                    score = output[:, score]
                
                # Compute gradients
                score.backward()
                
                # Accumulate gradients
                node_attributions += interpolated_x.grad.detach()
                
                # Clear gradients
                interpolated_x.grad.zero_()
        
        # Scale by (input - baseline)
        node_attributions = node_attributions / steps * (x - baseline)
        
        # Aggregate to edge attributions (simplified: sum of node attributions)
        edge_attributions = self._compute_edge_attributions(
            node_attributions, edge_index
        )
        
        return node_attributions, edge_attributions
    
    def _compute_edge_attributions(
        self,
        node_attributions: torch.Tensor,
        edge_index: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute edge attributions from node attributions.
        
        Args:
            node_attributions: Node-level attributions [num_nodes, input_dim]
            edge_index: Edge indices [2, num_edges]
        
        Returns:
            Edge attributions [num_edges, input_dim]
        """
        src, dst = edge_index
        edge_attr = (node_attributions[src] + node_attributions[dst]) / 2
        return edge_attr


def create_model_from_config(config: Dict[str, Any]) -> PolymerGNN:
    """
    Create a PolymerGNN model from configuration.
    
    Args:
        config: Dictionary with model configuration
            - input_dim: int
            - hidden_dim: int (default: 64)
            - output_dim: int (default: 3)
            - num_layers: int (default: 3)
            - dropout: float (default: 0.1)
    
    Returns:
        Configured PolymerGNN model
    """
    input_dim = config.get('input_dim', 10)
    hidden_dim = config.get('hidden_dim', 64)
    output_dim = config.get('output_dim', 3)
    num_layers = config.get('num_layers', 3)
    dropout = config.get('dropout', 0.1)
    
    model = PolymerGNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
        num_layers=num_layers,
        dropout=dropout
    )
    
    logger.info(f"Created model with {model.get_num_params()} parameters")
    return model


def validate_model_constraints(model: PolymerGNN) -> bool:
    """
    Validate that the model meets all constraints.
    
    Args:
        model: PolymerGNN model to validate
    
    Returns:
        True if all constraints are satisfied
    
    Raises:
        ValueError: If any constraint is violated
    """
    errors = []
    
    if model.num_layers > 3:
        errors.append(f"num_layers ({model.num_layers}) exceeds max of 3")
    
    if model.hidden_dim > 128:
        errors.append(f"hidden_dim ({model.hidden_dim}) exceeds max of 128")
    
    if errors:
        raise ValueError("Model constraint violations:\n" + "\n".join(errors))
    
    logger.info("Model constraints validated successfully")
    return True


def compute_feature_importance(
    model: PolymerGNN,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    target_class: int,
    steps: int = 50
) -> Dict[str, torch.Tensor]:
    """
    Compute feature importance using Integrated Gradients.
    
    Args:
        model: Trained PolymerGNN model
        x: Input node features
        edge_index: Edge indices
        target_class: Target class for attribution
        steps: Number of IG steps
    
    Returns:
        Dictionary with 'node_attributions' and 'edge_attributions'
    """
    ig = IntegratedGradients(model)
    node_attr, edge_attr = ig.compute_attributions(
        x, edge_index, target_class=target_class, steps=steps
    )
    
    return {
        'node_attributions': node_attr,
        'edge_attributions': edge_attr
    }


def main():
    """
    Main function to demonstrate model creation and validation.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example configuration
    config = {
        'input_dim': 10,
        'hidden_dim': 64,
        'output_dim': 3,
        'num_layers': 3,
        'dropout': 0.1
    }
    
    # Create model
    model = create_model_from_config(config)
    
    # Validate constraints
    validate_model_constraints(model)
    
    # Print model summary
    print(f"Model created successfully with {model.get_num_params()} parameters")
    print(f"Number of layers: {model.num_layers}")
    print(f"Hidden dimension: {model.hidden_dim}")
    
    # Example forward pass
    dummy_x = torch.randn(100, config['input_dim'])
    dummy_edge_index = torch.randint(0, 100, (2, 200))
    dummy_batch = torch.zeros(100, dtype=torch.long)
    
    model.eval()
    with torch.no_grad():
        output = model(dummy_x, dummy_edge_index, dummy_batch)
    
    print(f"Output shape: {output.shape}")
    print("Model validation complete")


if __name__ == '__main__':
    main()