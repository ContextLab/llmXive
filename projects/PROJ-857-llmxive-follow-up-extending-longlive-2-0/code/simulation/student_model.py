"""
Simplified Diffusion Student Model for CPU-only execution.

Implements a lightweight U-Net style diffusion model compatible with CPU inference
and training, designed to work with the quantization emulator (T007a) and
the training loop (T012).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
import os
from pathlib import Path

class TrainingLoopError(Exception):
    """Custom exception for errors occurring during model initialization or training."""
    pass

class SimplifiedDiffusionStudent(nn.Module):
    """
    A simplified U-Net based diffusion model optimized for CPU execution.
    
    This model processes 4-second video clips (downsampled from Kinetics-400)
    and is designed to be compatible with stochastic rounding quantization.
    
    Architecture:
    - Input: (Batch, Channels, Time, Height, Width)
    - Encoder: 3D Convolutional layers with downsampling
    - Bottleneck: Residual blocks with attention (simplified)
    - Decoder: Transposed 3D Convolutions with skip connections
    - Output: (Batch, Channels, Time, Height, Width) - predicted noise
    
    Note: Designed to fit within 7GB RAM limit when processing small clips.
    """
    
    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 3,
        base_channels: int = 32,
        time_channels: int = 16,
        num_res_blocks: int = 2,
        num_time_steps: int = 1000,
        dropout: float = 0.1,
        device: str = 'cpu'
    ):
        super().__init__()
        
        if device != 'cpu':
            raise TrainingLoopError(
                f"SimplifiedDiffusionStudent is CPU-only. Got device: {device}"
            )
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_channels = base_channels
        self.num_time_steps = num_time_steps
        self.device = device
        
        # Time embedding
        self.time_embed = nn.Sequential(
            nn.Linear(time_channels, base_channels * 4),
            nn.SiLU(),
            nn.Linear(base_channels * 4, base_channels * 4)
        )
        
        # Input block
        self.input_proj = nn.Conv3d(
            in_channels, base_channels, kernel_size=3, padding=1
        )
        
        # Encoder blocks
        self.encoder1 = self._make_res_block(base_channels, base_channels * 2, num_res_blocks, dropout)
        self.down1 = nn.Conv3d(base_channels * 2, base_channels * 2, kernel_size=3, stride=2, padding=1)
        
        self.encoder2 = self._make_res_block(base_channels * 2, base_channels * 4, num_res_blocks, dropout)
        self.down2 = nn.Conv3d(base_channels * 4, base_channels * 4, kernel_size=3, stride=2, padding=1)
        
        # Bottleneck
        self.bottleneck = self._make_res_block(base_channels * 4, base_channels * 4, num_res_blocks, dropout)
        
        # Decoder blocks
        self.up2 = nn.ConvTranspose3d(
            base_channels * 4, base_channels * 2, kernel_size=2, stride=2
        )
        self.decoder2 = self._make_res_block(base_channels * 4, base_channels * 2, num_res_blocks, dropout)
        
        self.up1 = nn.ConvTranspose3d(
            base_channels * 2, base_channels, kernel_size=2, stride=2
        )
        self.decoder1 = self._make_res_block(base_channels * 2, base_channels, num_res_blocks, dropout)
        
        # Output block
        self.final_conv = nn.Sequential(
            nn.GroupNorm(8, base_channels),
            nn.SiLU(),
            nn.Conv3d(base_channels, out_channels, kernel_size=3, padding=1)
        )
        
        self.to(device)
        
    def _make_res_block(
        self,
        in_channels: int,
        out_channels: int,
        num_blocks: int,
        dropout: float
    ) -> nn.Sequential:
        """Create a sequence of residual blocks."""
        layers = []
        current_channels = in_channels
        
        for i in range(num_blocks):
            layers.append(
                ResidualBlock(current_channels, out_channels, dropout, self.device)
            )
            current_channels = out_channels
        
        return nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the diffusion model.
        
        Args:
            x: Input tensor of shape (B, C, T, H, W)
            t: Time step tensor of shape (B,) or (B, 1)
            
        Returns:
            Predicted noise tensor of shape (B, C, T, H, W)
        """
        # Time embedding
        t_emb = self.time_embedding(t)
        
        # Input projection
        h = self.input_proj(x)
        
        # Encoder
        enc1 = self.encoder1(h)
        h = self.down1(enc1)
        
        enc2 = self.encoder2(h)
        h = self.down2(enc2)
        
        # Bottleneck
        h = self.bottleneck(h)
        
        # Decoder
        h = self.up2(h)
        h = self.decoder2(torch.cat([h, enc2], dim=1))
        
        h = self.up1(h)
        h = self.decoder1(torch.cat([h, enc1], dim=1))
        
        # Output
        output = self.final_conv(h)
        
        return output
    
    def time_embedding(self, t: torch.Tensor) -> torch.Tensor:
        """Create time embedding."""
        # Ensure t is 2D
        if t.dim() == 1:
            t = t.unsqueeze(1)
        
        # Sinusoidal embedding
        device = t.device
        half_dim = self.base_channels * 4 // 2
        emb = torch.log(torch.tensor(10000.0, device=device)) / (half_dim - 1)
        emb = torch.exp(torch.arange(half_dim, device=device) * -emb)
        emb = t.float() * emb
        emb = torch.cat([torch.sin(emb), torch.cos(emb)], dim=1)
        
        return self.time_embed(emb)

class ResidualBlock(nn.Module):
    """Residual block with optional dropout."""
    
    def __init__(self, in_channels: int, out_channels: int, dropout: float, device: str):
        super().__init__()
        self.device = device
        
        self.conv1 = nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1)
        self.norm1 = nn.GroupNorm(8, out_channels)
        self.conv2 = nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1)
        self.norm2 = nn.GroupNorm(8, out_channels)
        self.dropout = nn.Dropout(dropout)
        
        if in_channels != out_channels:
            self.skip_conv = nn.Conv3d(in_channels, out_channels, kernel_size=1)
        else:
            self.skip_conv = nn.Identity()
        
        self.to(device)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with residual connection."""
        residual = self.skip_conv(x)
        
        h = F.silu(self.norm1(self.conv1(x)))
        h = self.dropout(h)
        h = self.norm2(self.conv2(h))
        
        return F.silu(h + residual)

def create_student_model(
    config: Optional[Dict[str, Any]] = None,
    device: str = 'cpu'
) -> SimplifiedDiffusionStudent:
    """
    Factory function to create a SimplifiedDiffusionStudent model.
    
    Args:
        config: Optional dictionary with model configuration parameters.
               Supported keys: in_channels, out_channels, base_channels,
               time_channels, num_res_blocks, num_time_steps, dropout.
        device: Device to create the model on (default: 'cpu').
                
    Returns:
        Initialized SimplifiedDiffusionStudent model.
        
    Raises:
        TrainingLoopError: If device is not 'cpu' or config is invalid.
    """
    if device != 'cpu':
        raise TrainingLoopError(
            f"SimplifiedDiffusionStudent only supports CPU. Got: {device}"
        )
    
    defaults = {
        'in_channels': 3,
        'out_channels': 3,
        'base_channels': 32,
        'time_channels': 16,
        'num_res_blocks': 2,
        'num_time_steps': 1000,
        'dropout': 0.1
    }
    
    if config:
        defaults.update(config)
    
    model = SimplifiedDiffusionStudent(
        in_channels=defaults['in_channels'],
        out_channels=defaults['out_channels'],
        base_channels=defaults['base_channels'],
        time_channels=defaults['time_channels'],
        num_res_blocks=defaults['num_res_blocks'],
        num_time_steps=defaults['num_time_steps'],
        dropout=defaults['dropout'],
        device=device
    )
    
    return model

def main():
    """
    Main function to demonstrate model initialization and basic forward pass.
    This script verifies the model can be created and runs a small inference test.
    """
    print("Initializing SimplifiedDiffusionStudent model...")
    
    try:
        model = create_student_model(device='cpu')
        model.eval()
        
        print(f"Model created successfully on CPU.")
        print(f"Number of parameters: {sum(p.numel() for p in model.parameters()):,}")
        
        # Create a dummy input (small batch for testing)
        # Shape: (Batch, Channels, Time, Height, Width)
        batch_size = 2
        channels = 3
        time_steps = 4  # 4-second clip at 1fps
        height = 32
        width = 32
        
        dummy_input = torch.randn(batch_size, channels, time_steps, height, width)
        dummy_time = torch.tensor([100, 500])
        
        print(f"Running forward pass with input shape: {dummy_input.shape}")
        
        with torch.no_grad():
            output = model(dummy_input, dummy_time)
        
        print(f"Forward pass successful. Output shape: {output.shape}")
        print("Model validation complete.")
        
        # Verify output is on CPU
        assert output.device.type == 'cpu', "Output must be on CPU"
        
        # Verify no NaN/Inf
        assert not torch.isnan(output).any(), "Output contains NaN values"
        assert not torch.isinf(output).any(), "Output contains Inf values"
        
        print("All checks passed.")
        
    except TrainingLoopError as e:
        print(f"Error during model operations: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()