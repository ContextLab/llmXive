"""
Student Model Implementation for CPU-Only Diffusion Simulation.

This module provides a simplified diffusion model wrapper designed for
CPU-only execution, compatible with the llmXive pipeline. It implements
a U-Net-like architecture with configurable bit-width quantization support
via the QuantizationEmulator.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_path_str
from simulation.quantization_emulator import QuantizationEmulator, create_quantization_emulator


class TrainingLoopError(Exception):
    """Custom exception for training loop errors."""
    pass


class SimplifiedDiffusionStudent(nn.Module):
    """
    A simplified U-Net based diffusion model optimized for CPU execution.

    This model implements a minimal diffusion process suitable for simulation
    on CPU hardware. It supports integration with the QuantizationEmulator
    to simulate NVFP4 precision constraints.

    Args:
        in_channels (int): Number of input channels (default: 3 for RGB)
        out_channels (int): Number of output channels (default: 3 for RGB)
        base_channels (int): Base number of channels for the first layer (default: 32)
        num_res_blocks (int): Number of residual blocks per resolution (default: 2)
        num_timesteps (int): Number of diffusion timesteps (default: 1000)
        quantization_bit_width (int): Target bit-width for quantization emulation (2, 4, or 8)
        device (str): Device to run on ('cpu' only for this implementation)
    """

    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 3,
        base_channels: int = 32,
        num_res_blocks: int = 2,
        num_timesteps: int = 1000,
        quantization_bit_width: int = 4,
        device: str = "cpu"
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_channels = base_channels
        self.num_res_blocks = num_res_blocks
        self.num_timesteps = num_timesteps
        self.device = device
        self.quantization_bit_width = quantization_bit_width

        # Initialize quantization emulator
        self.quantizer = create_quantization_emulator(quantization_bit_width)

        # Time embedding layers
        self.time_embed = nn.Sequential(
            nn.Linear(1, base_channels * 4),
            nn.SiLU(),
            nn.Linear(base_channels * 4, base_channels * 4)
        )

        # Input block
        self.input_block = nn.Sequential(
            nn.Conv2d(in_channels, base_channels, kernel_size=3, padding=1),
            nn.GroupNorm(8, base_channels),
            nn.SiLU()
        )

        # Downsample blocks
        self.down_blocks = nn.ModuleList()
        channels = base_channels
        for _ in range(num_res_blocks):
            self.down_blocks.append(
                nn.Sequential(
                    nn.Conv2d(channels, channels, kernel_size=3, padding=1),
                    nn.GroupNorm(8, channels),
                    nn.SiLU(),
                    nn.Conv2d(channels, channels, kernel_size=3, padding=1),
                    nn.GroupNorm(8, channels),
                    nn.SiLU()
                )
            )
            self.down_blocks.append(nn.AvgPool2d(2))
            channels *= 2

        # Middle block
        self.mid_block = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
            nn.GroupNorm(8, channels),
            nn.SiLU(),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
            nn.GroupNorm(8, channels),
            nn.SiLU()
        )

        # Upsample blocks
        self.up_blocks = nn.ModuleList()
        for _ in range(num_res_blocks):
            channels //= 2
            self.up_blocks.append(
                nn.Sequential(
                    nn.Conv2d(channels * 2, channels, kernel_size=3, padding=1),
                    nn.GroupNorm(8, channels),
                    nn.SiLU(),
                    nn.Conv2d(channels, channels, kernel_size=3, padding=1),
                    nn.GroupNorm(8, channels),
                    nn.SiLU()
                )
            )
            if _ < num_res_blocks - 1:
                self.up_blocks.append(nn.Upsample(scale_factor=2, mode='nearest'))

        # Output block
        self.output_block = nn.Sequential(
            nn.Conv2d(base_channels, base_channels, kernel_size=3, padding=1),
            nn.GroupNorm(8, base_channels),
            nn.SiLU(),
            nn.Conv2d(base_channels, out_channels, kernel_size=3, padding=1)
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize model weights for stable training."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.GroupNorm):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                nn.init.constant_(m.bias, 0)

    def _apply_quantization(self, tensor: torch.Tensor) -> torch.Tensor:
        """Apply quantization emulation to a tensor."""
        return self.quantizer.quantize(tensor)

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the diffusion model.

        Args:
            x: Input tensor of shape (B, C, H, W)
            t: Timestep tensor of shape (B,)

        Returns:
            Output tensor of shape (B, C, H, W)
        """
        # Ensure CPU execution
        if x.device.type != 'cpu':
            x = x.cpu()
        if t.device.type != 'cpu':
            t = t.cpu()

        # Time embedding
        t_emb = t.float().unsqueeze(-1)
        t_emb = self.time_embed(t_emb)

        # Input block
        h = self.input_block(x)

        # Downsample blocks with skip connections
        skips = [h]
        for i, block in enumerate(self.down_blocks):
            h = block(h)
            # Apply quantization emulation at each layer
            h = self._apply_quantization(h)
            if i % 2 == 1:  # After downsampling
                skips.append(h)

        # Middle block
        h = self.mid_block(h)
        h = self._apply_quantization(h)

        # Upsample blocks with skip connections
        for i, block in enumerate(self.up_blocks):
            if i % 2 == 0:  # Convolution block
                # Concatenate with skip connection
                skip = skips.pop()
                h = torch.cat([h, skip], dim=1)
            h = block(h)
            # Apply quantization emulation
            h = self._apply_quantization(h)

        # Output block
        h = self.output_block(h)
        h = self._apply_quantization(h)

        return h

    def get_noise_schedule(self, num_timesteps: Optional[int] = None) -> torch.Tensor:
        """
        Generate a linear noise schedule for diffusion.

        Args:
            num_timesteps: Number of timesteps (uses self.num_timesteps if None)

        Returns:
            Tensor of noise schedule values
        """
        if num_timesteps is None:
            num_timesteps = self.num_timesteps

        timesteps = torch.linspace(0.0001, 0.02, num_timesteps)
        return timesteps

    def add_noise(self, x: torch.Tensor, t: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Add noise to input according to diffusion schedule.

        Args:
            x: Clean input tensor
            t: Timestep

        Returns:
            Tuple of (noisy_input, noise)
        """
        noise = torch.randn_like(x)
        schedule = self.get_noise_schedule()
        beta = schedule[t]
        alpha = 1 - beta
        noisy_x = torch.sqrt(alpha) * x + torch.sqrt(1 - alpha) * noise
        return noisy_x, noise

    def predict_noise(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        Predict noise from noisy input.

        Args:
            x: Noisy input tensor
            t: Timestep

        Returns:
            Predicted noise tensor
        """
        return self.forward(x, t)


def create_student_model(
    in_channels: int = 3,
    out_channels: int = 3,
    base_channels: int = 32,
    num_res_blocks: int = 2,
    num_timesteps: int = 1000,
    quantization_bit_width: int = 4,
    device: str = "cpu"
) -> SimplifiedDiffusionStudent:
    """
    Factory function to create a SimplifiedDiffusionStudent model.

    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels
        base_channels: Base number of channels
        num_res_blocks: Number of residual blocks per resolution
        num_timesteps: Number of diffusion timesteps
        quantization_bit_width: Target bit-width (2, 4, or 8)
        device: Device to run on (must be 'cpu')

    Returns:
        Configured SimplifiedDiffusionStudent model
    """
    if device != "cpu":
        raise ValueError("SimplifiedDiffusionStudent only supports CPU execution. "
                       f"Got device='{device}', but must be 'cpu'.")

    if quantization_bit_width not in [2, 4, 8]:
        raise ValueError(f"quantization_bit_width must be 2, 4, or 8. Got {quantization_bit_width}")

    model = SimplifiedDiffusionStudent(
        in_channels=in_channels,
        out_channels=out_channels,
        base_channels=base_channels,
        num_res_blocks=num_res_blocks,
        num_timesteps=num_timesteps,
        quantization_bit_width=quantization_bit_width,
        device=device
    )

    return model


def main():
    """
    Main function to test the student model.
    """
    print("Testing SimplifiedDiffusionStudent model...")

    # Create model
    model = create_student_model(
        in_channels=3,
        out_channels=3,
        base_channels=32,
        num_res_blocks=2,
        num_timesteps=1000,
        quantization_bit_width=4,
        device="cpu"
    )

    # Create sample input
    batch_size = 2
    height, width = 64, 64
    x = torch.randn(batch_size, 3, height, width)
    t = torch.randint(0, 1000, (batch_size,))

    # Forward pass
    output = model(x, t)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Quantization bit-width: {model.quantization_bit_width}")

    # Test noise addition and prediction
    noisy_x, noise = model.add_noise(x, t)
    predicted_noise = model.predict_noise(noisy_x, t)

    print(f"Noisy input shape: {noisy_x.shape}")
    print(f"Predicted noise shape: {predicted_noise.shape}")

    # Verify shapes match
    assert output.shape == x.shape, f"Output shape {output.shape} != input shape {x.shape}"
    assert predicted_noise.shape == noise.shape, f"Predicted noise shape mismatch"

    print("✓ All tests passed!")

    return model


if __name__ == "__main__":
    main()