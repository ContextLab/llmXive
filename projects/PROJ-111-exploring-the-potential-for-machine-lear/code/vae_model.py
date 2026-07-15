"""
Variational Autoencoder (VAE) for spin configuration analysis.

Architecture:
- Encoder: 2 Convolutional layers -> Flatten -> Linear -> (mu, log_var)
- Decoder: Linear -> Unflatten -> 2 Deconvolutional layers -> Output

Latent dimension: 10
Input shape: (batch, 3, L, L) where L is 16 or 24
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional

class VAE(nn.Module):
    """
    Variational Autoencoder for 2D spin configurations.
    
    Args:
        latent_dim (int): Dimension of the latent space. Default: 10.
        input_channels (int): Number of input channels (spin components). Default: 3.
        hidden_channels (int): Number of channels in hidden layers. Default: 32.
    """
    def __init__(self, latent_dim: int = 10, input_channels: int = 3, hidden_channels: int = 32):
        super(VAE, self).__init__()
        
        self.latent_dim = latent_dim
        self.input_channels = input_channels
        self.hidden_channels = hidden_channels
        
        # Encoder: 2 Convolutional layers
        # Input: (B, 3, L, L)
        # Layer 1: Conv2d(3, 32, kernel=4, stride=2, padding=1) -> (B, 32, L/2, L/2)
        self.enc1 = nn.Conv2d(input_channels, hidden_channels, kernel_size=4, stride=2, padding=1)
        self.bn1 = nn.BatchNorm2d(hidden_channels)
        
        # Layer 2: Conv2d(32, 64, kernel=4, stride=2, padding=1) -> (B, 64, L/4, L/4)
        self.enc2 = nn.Conv2d(hidden_channels, hidden_channels * 2, kernel_size=4, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(hidden_channels * 2)
        
        # Calculate the size of the flattened vector after 2 conv layers
        # For L=16: (16/2)/2 = 4 -> 4x4 grid. For L=24: (24/2)/2 = 6 -> 6x6 grid.
        # We handle this dynamically in the forward pass or assume a fixed max size and adjust.
        # To be safe for variable L, we compute the flat size in forward.
        
        # Latent space parameters
        self.fc_mu = nn.Linear(hidden_channels * 2 * 2, latent_dim) # Placeholder, recalculated below
        self.fc_log_var = nn.Linear(hidden_channels * 2 * 2, latent_dim)
        
        # Decoder: 2 Deconvolutional layers
        # Input to decoder: (B, 64, L/4, L/4)
        # Layer 1: ConvTranspose2d(64, 32, kernel=4, stride=2, padding=1) -> (B, 32, L/2, L/2)
        self.dec1 = nn.ConvTranspose2d(hidden_channels * 2, hidden_channels, kernel_size=4, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(hidden_channels)
        
        # Layer 2: ConvTranspose2d(32, 3, kernel=4, stride=2, padding=1) -> (B, 3, L, L)
        self.dec2 = nn.ConvTranspose2d(hidden_channels, input_channels, kernel_size=4, stride=2, padding=1)
        
        # We need to dynamically set the input size for the linear layers based on L
        # This is handled in the forward method by computing the feature map size
        self._latent_linear_input_dim = None

    def _get_latent_input_dim(self, batch_size: int, L: int) -> int:
        """Calculate the flattened dimension before the linear layers."""
        # After enc1: L -> L/2
        # After enc2: L/2 -> L/4
        # Feature map size: (L/4) * (L/4) * (hidden_channels * 2)
        if self._latent_linear_input_dim is None:
            feature_size = (L // 4) * (L // 4)
            self._latent_linear_input_dim = feature_size * (self.hidden_channels * 2)
        return self._latent_linear_input_dim

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encoder forward pass.
        
        Args:
            x: Input tensor of shape (batch, 3, L, L)
        
        Returns:
            mu: Mean of latent distribution
            log_var: Log variance of latent distribution
        """
        # Layer 1
        x = F.relu(self.bn1(self.enc1(x)))
        # Layer 2
        x = F.relu(self.bn2(self.enc2(x)))
        
        # Flatten
        batch_size = x.size(0)
        x = x.view(batch_size, -1)
        
        # Ensure linear layers are sized correctly for the current input L
        if self._latent_linear_input_dim != x.size(1):
            self._latent_linear_input_dim = x.size(1)
            self.fc_mu = nn.Linear(self._latent_linear_input_dim, self.latent_dim)
            self.fc_log_var = nn.Linear(self._latent_linear_input_dim, self.latent_dim)
        
        mu = self.fc_mu(x)
        log_var = self.fc_log_var(x)
        
        return mu, log_var

    def reparameterize(self, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        """
        Reparameterization trick.
        
        Args:
            mu: Mean tensor
            log_var: Log variance tensor
        
        Returns:
            z: Sampled latent vector
        """
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor, L: int) -> torch.Tensor:
        """
        Decoder forward pass.
        
        Args:
            z: Latent vector tensor of shape (batch, latent_dim)
            L: Original spatial dimension (needed to reshape correctly if dynamic)
        
        Returns:
            x_recon: Reconstructed tensor of shape (batch, 3, L, L)
        """
        # We need to reshape z back to the feature map size before deconv
        # Feature map size is (L/4, L/4)
        feature_size = L // 4
        hidden_dim = self.hidden_channels * 2
        
        # If the linear layer size was changed, we might need to handle this carefully.
        # Assuming the input z matches the expected size from the encoder for this L.
        x = z.view(-1, hidden_dim, feature_size, feature_size)
        
        # Layer 1 (Deconv)
        x = F.relu(self.bn3(self.dec1(x)))
        # Layer 2 (Deconv)
        x = self.dec2(x)
        
        # Apply tanh to constrain output to [-1, 1] matching spin vectors normalized
        return torch.tanh(x)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Full VAE forward pass.
        
        Args:
            x: Input tensor (batch, 3, L, L)
        
        Returns:
            x_recon: Reconstructed input
            mu: Latent mean
            log_var: Latent log variance
        """
        batch_size = x.size(0)
        L = x.size(-1)
        
        mu, log_var = self.encode(x)
        z = self.reparameterize(mu, log_var)
        x_recon = self.decode(z, L)
        
        return x_recon, mu, log_var

    def loss_function(self, x_recon: torch.Tensor, x: torch.Tensor, mu: torch.Tensor, log_var: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Calculate VAE loss (MSE + KL divergence).
        
        Args:
            x_recon: Reconstructed input
            x: Original input
            mu: Latent mean
            log_var: Latent log variance
        
        Returns:
            total_loss: Total loss
            recon_loss: Reconstruction loss (MSE)
            kl_loss: KL divergence loss
        """
        # Reconstruction loss (MSE)
        recon_loss = F.mse_loss(x_recon, x, reduction='sum')
        
        # KL Divergence: -0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
        kl_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())
        
        total_loss = recon_loss + kl_loss
        
        return total_loss, recon_loss, kl_loss

def create_vae_model(latent_dim: int = 10) -> VAE:
    """
    Factory function to create a VAE model instance.
    
    Args:
        latent_dim: Dimension of the latent space.
    
    Returns:
        Configured VAE model.
    """
    return VAE(latent_dim=latent_dim)