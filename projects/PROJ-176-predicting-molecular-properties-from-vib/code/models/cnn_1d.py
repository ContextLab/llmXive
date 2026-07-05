"""
1-D CNN Model for predicting molecular properties from vibrational spectra.

Architecture:
- Three convolutional blocks with kernel size 9 and 64 filters.
- ReLU activation and MaxPooling after each block.
- Separate regression heads for Dipole, Polarizability, and HOMO-LUMO gap.

Constraints:
- CPU-only execution (no CUDA ops forced).
- Standard float precision (float32).
"""

import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    """A single convolutional block with Conv1d, ReLU, and MaxPool."""
    
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 9, stride: int = 1, padding: int = 4):
        super().__init__()
        self.conv = nn.Conv1d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv(x)
        x = self.relu(x)
        x = self.pool(x)
        return x


class MolecularPropertyCNN(nn.Module):
    """
    1-D CNN with three convolutional blocks and three separate regression heads.
    
    Inputs:
        x (Tensor): Shape (batch_size, 1, sequence_length) - Single channel spectrum.
    
    Outputs:
        dict: {
            'dipole': Tensor (batch_size, 3),
            'polarizability': Tensor (batch_size, 1),
            'homo_lumo': Tensor (batch_size, 1)
        }
    """
    
    def __init__(self, input_channels: int = 1, base_filters: int = 64, kernel_size: int = 9):
        super().__init__()
        
        # Determine padding to maintain spatial dimensions roughly (same padding approx)
        # For kernel=9, stride=1, padding=4 keeps size same before pooling.
        padding = kernel_size // 2
        
        # Block 1
        self.block1 = ConvBlock(input_channels, base_filters, kernel_size=kernel_size, padding=padding)
        
        # Block 2
        self.block2 = ConvBlock(base_filters, base_filters, kernel_size=kernel_size, padding=padding)
        
        # Block 3
        self.block3 = ConvBlock(base_filters, base_filters, kernel_size=kernel_size, padding=padding)
        
        # Calculate flattened feature size after 3 pooling operations
        # Each pool reduces length by 2. Total reduction: 2^3 = 8.
        # We assume a fixed input length for the final linear layers.
        # To be robust, we will calculate this dynamically in forward if needed,
        # but for strict architecture definition, we assume a standard input size.
        # However, to support variable input sizes, we use adaptive pooling or
        # calculate the size dynamically in the forward pass.
        # Given the task requires a specific architecture, we will implement a dynamic
        # size calculation to ensure the linear layers receive the correct input size
        # regardless of the spectrum length (as long as it's > 8).
        
        # Head for Dipole Moment (3 components: x, y, z)
        self.head_dipole = nn.Sequential(
            nn.Flatten(start_dim=1),
            nn.Linear(base_filters * 1 * 1, 128), # Placeholder for dynamic size calculation
            nn.ReLU(),
            nn.Linear(128, 3)
        )
        
        # Head for Polarizability (scalar)
        self.head_polarizability = nn.Sequential(
            nn.Flatten(start_dim=1),
            nn.Linear(base_filters * 1 * 1, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
        
        # Head for HOMO-LUMO Gap (scalar)
        self.head_homo_lumo = nn.Sequential(
            nn.Flatten(start_dim=1),
            nn.Linear(base_filters * 1 * 1, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
        
        # Store the feature size for dynamic calculation
        self.feature_size = None
    
    def _get_feature_size(self, x: torch.Tensor) -> int:
        """Calculate the flattened feature size after conv blocks."""
        with torch.no_grad():
            # Pass a dummy tensor through conv blocks to get shape
            out = self.block1(x)
            out = self.block2(out)
            out = self.block3(out)
            return out.view(out.size(0), -1).size(1)
    
    def forward(self, x: torch.Tensor) -> dict:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, 1, spectrum_length)
        
        Returns:
            dict with keys 'dipole', 'polarizability', 'homo_lumo'
        """
        # Ensure input shape
        if x.dim() == 2:
            x = x.unsqueeze(1) # Add channel dim if missing
        
        # Calculate feature size if not set or if input shape changed
        if self.feature_size is None or self.feature_size != x.size(1): # Simplified check
            # Re-calculate based on actual conv output
            temp_out = self.block1(x)
            temp_out = self.block2(temp_out)
            temp_out = self.block3(temp_out)
            self.feature_size = temp_out.view(temp_out.size(0), -1).size(1)
            
            # Re-initialize heads with correct input size
            # Note: In a real training loop, we might want to avoid re-initializing weights.
            # For this implementation, we assume the input size is fixed or we handle
            # the linear layer dimensions dynamically by using a fixed bottleneck size.
            # To strictly follow "separate regression heads" without dynamic re-init,
            # we assume a fixed input length for the linear layer.
            # However, to be safe with variable lengths, we can use AdaptiveAvgPool1d
            # before the linear layers.
            pass 
        
        # Forward through conv blocks
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        
        # Use AdaptiveAvgPool1d to handle variable input lengths robustly
        # This ensures the feature size before flattening is fixed (e.g., 1)
        # regardless of the input spectrum length.
        x = nn.AdaptiveAvgPool1d(1)(x)
        x = x.squeeze(-1) # Shape: (batch_size, base_filters)
        
        # Pass through heads
        dipole = self._head_dipole_impl(x)
        polarizability = self._head_polarizability_impl(x)
        homo_lumo = self._head_homo_lumo_impl(x)
        
        return {
            'dipole': dipole,
            'polarizability': polarizability,
            'homo_lumo': homo_lumo
        }
    
    def _head_dipole_impl(self, x: torch.Tensor) -> torch.Tensor:
        # Re-implementing logic inline to avoid dynamic re-init issues
        # We define the layers in __init__ but ensure they accept the correct input size
        # Since we used AdaptiveAvgPool1d(1), the input to these layers is (batch, 64)
        # Let's define the layers properly in __init__ to match (batch, 64)
        return self.dipole_head(x)
    
    def _head_polarizability_impl(self, x: torch.Tensor) -> torch.Tensor:
        return self.polarizability_head(x)
    
    def _head_homo_lumo_impl(self, x: torch.Tensor) -> torch.Tensor:
        return self.homo_lumo_head(x)

# Corrected __init__ to define layers with fixed input size after AdaptiveAvgPool1d
class MolecularPropertyCNN(nn.Module):
    """
    1-D CNN with three convolutional blocks and three separate regression heads.
    
    Architecture Details:
    - 3 Conv Blocks: Kernel=9, Filters=64, ReLU, MaxPool(2)
    - AdaptiveAvgPool1d(1) to handle variable input lengths
    - Linear layers take input size = 64 (from base_filters)
    
    Outputs:
        dict: {
            'dipole': Tensor (batch_size, 3),
            'polarizability': Tensor (batch_size, 1),
            'homo_lumo': Tensor (batch_size, 1)
        }
    """
    
    def __init__(self, input_channels: int = 1, base_filters: int = 64, kernel_size: int = 9):
        super().__init__()
        
        padding = kernel_size // 2
        
        # Block 1
        self.block1 = ConvBlock(input_channels, base_filters, kernel_size=kernel_size, padding=padding)
        # Block 2
        self.block2 = ConvBlock(base_filters, base_filters, kernel_size=kernel_size, padding=padding)
        # Block 3
        self.block3 = ConvBlock(base_filters, base_filters, kernel_size=kernel_size, padding=padding)
        
        # Adaptive pooling to reduce temporal dimension to 1
        self.adaptive_pool = nn.AdaptiveAvgPool1d(1)
        
        # Input size to linear layers is base_filters (64)
        linear_input_size = base_filters
        
        # Head for Dipole Moment (3 components)
        self.dipole_head = nn.Sequential(
            nn.Linear(linear_input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 3)
        )
        
        # Head for Polarizability (scalar)
        self.polarizability_head = nn.Sequential(
            nn.Linear(linear_input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
        
        # Head for HOMO-LUMO Gap (scalar)
        self.homo_lumo_head = nn.Sequential(
            nn.Linear(linear_input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
    
    def forward(self, x: torch.Tensor) -> dict:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, 1, spectrum_length)
        
        Returns:
            dict with keys 'dipole', 'polarizability', 'homo_lumo'
        """
        # Ensure input has channel dimension
        if x.dim() == 2:
            x = x.unsqueeze(1)
        
        # Convolutional blocks
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        
        # Adaptive pooling to (batch_size, 64, 1)
        x = self.adaptive_pool(x)
        x = x.squeeze(-1) # Shape: (batch_size, 64)
        
        # Heads
        dipole = self.dipole_head(x)
        polarizability = self.polarizability_head(x)
        homo_lumo = self.homo_lumo_head(x)
        
        return {
            'dipole': dipole,
            'polarizability': polarizability,
            'homo_lumo': homo_lumo
        }