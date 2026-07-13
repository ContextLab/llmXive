from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

class SchNetGNN(nn.Module):
    """
    Simplified SchNet-style Graph Neural Network for dipole moment prediction.
    This implementation uses a continuous-filter convolution approach.
    """
    
    def __init__(self, input_dim: int = 100, hidden_dim: int = 64, num_layers: int = 3):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Input embedding layer
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # Simple message passing layers (simplified SchNet)
        self.conv_layers = nn.ModuleList()
        self.fc_layers = nn.ModuleList()
        
        for i in range(num_layers):
            self.conv_layers.append(nn.Linear(hidden_dim, hidden_dim))
            self.fc_layers.append(nn.Linear(hidden_dim, hidden_dim))
        
        # Output layer
        self.output_proj = nn.Linear(hidden_dim, 1)
        
        # Gaussian expansion for distance encoding (simplified)
        self.num_gaussians = 32
        self.gaussian_centers = nn.Parameter(torch.linspace(0, 5, self.num_gaussians))
        self.gaussian_widths = nn.Parameter(torch.ones(self.num_gaussians) * 0.5)
    
    def _gaussian_expansion(self, distances: torch.Tensor) -> torch.Tensor:
        """Compute Gaussian expansion of distances."""
        # Expand dimensions for broadcasting
        distances = distances.unsqueeze(-1)  # [batch, 1]
        centers = self.gaussian_centers.unsqueeze(0)  # [1, num_gaussians]
        widths = self.gaussian_widths.unsqueeze(0)  # [1, num_gaussians]
        
        # Gaussian expansion
        expansion = torch.exp(-widths * (distances - centers) ** 2)
        return expansion  # [batch, num_gaussians]
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input features of shape [batch_size, input_dim]
            
        Returns:
            Predicted dipole moments of shape [batch_size, 1]
        """
        # Input projection
        h = self.input_proj(x)
        h = F.relu(h)
        
        # Message passing layers
        for i in range(self.num_layers):
            # Simple convolution (in a real SchNet, this would use graph structure)
            conv_out = self.conv_layers[i](h)
            fc_out = self.fc_layers[i](h)
            
            # Combine with skip connection
            h = h + F.relu(conv_out + fc_out)
        
        # Output projection
        output = self.output_proj(h)
        
        # Reduce to single value per sample (if multiple atoms, sum/mean)
        # For this simplified version, we assume input is already aggregated
        if output.dim() > 2:
            output = output.mean(dim=1, keepdim=True)
        
        return output.squeeze(-1)  # [batch_size]