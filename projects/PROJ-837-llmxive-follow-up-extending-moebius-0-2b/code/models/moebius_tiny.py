"""
Moebius-Tiny: A simplified, CPU-optimized image inpainting backbone.

Architecture constraints:
- Total parameters <= 15M
- Designed for CPU inference (no CUDA dependencies)
- Compatible with Moebius-Dynamic gating mechanism
- Uses standard PyTorch operations for maximum portability

This module implements a lightweight UNet-style encoder-decoder with
residual blocks, optimized for the Places2/CelebA-HQ inpainting task.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional

from models.data_models import InferenceResult, GatingState
from utils.seed import set_seed
from utils.logger import get_logger

logger = get_logger(__name__)

# --- Configuration Constants ---
# Target parameter count: ~12-14M to stay safely under 15M limit
BASE_CHANNELS = 32  # Reduced from standard 64 to save params
MAX_CHANNELS = 256  # Cap for decoder
NUM_RES_BLOCKS = 2  # Per resolution level


class ResidualBlock(nn.Module):
    """
    A lightweight residual block with Group Normalization.
    GroupNorm is chosen over BatchNorm for better stability with small batch sizes
    and CPU inference.
    """
    def __init__(self, in_channels: int, out_channels: int, groups: int = 8):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.norm1 = nn.GroupNorm(groups, out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.norm2 = nn.GroupNorm(groups, out_channels)
        
        # Projection if channels change
        if in_channels != out_channels:
            self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1)
        else:
            self.shortcut = nn.Identity()
            
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = self.shortcut(x)
        
        out = F.silu(self.norm1(self.conv1(x)))
        out = self.norm2(self.conv2(out))
        
        return F.silu(out + identity)

class EncoderBlock(nn.Module):
    """
    Encoder block: Conv + Downsample + Residuals.
    """
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.downsample = nn.Conv2d(in_channels, out_channels, kernel_size=4, stride=2, padding=1)
        self.res_blocks = nn.ModuleList([
            ResidualBlock(out_channels, out_channels) for _ in range(NUM_RES_BLOCKS)
        ])
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.downsample(x)
        for block in self.res_blocks:
            x = block(x)
        return x

class DecoderBlock(nn.Module):
    """
    Decoder block: Upsample + Concat + Residuals.
    """
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()
        self.upsample = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=4, stride=2, padding=1)
        # Input channels = out_channels (from upsample) + skip_channels
        self.res_blocks = nn.ModuleList([
            ResidualBlock(out_channels + skip_channels, out_channels) for _ in range(NUM_RES_BLOCKS)
        ])
        
    def forward(self, x: torch.Tensor, skip_x: torch.Tensor) -> torch.Tensor:
        x = self.upsample(x)
        # Concatenate with skip connection
        x = torch.cat([x, skip_x], dim=1)
        for block in self.res_blocks:
            x = block(x)
        return x

class MoebiusTiny(nn.Module):
    """
    Moebius-Tiny: The main inpainting backbone.
    
    Architecture:
    - Encoder: 4 levels (Downsampling by 2 each)
    - Bottleneck: 2 Residual blocks
    - Decoder: 4 levels (Upsampling by 2 each)
    - Output: 3-channel RGB image (or 4-channel with mask if configured)
    
    Parameters:
    - Input: (B, 4, H, W) where channels = RGB + Mask
    - Output: (B, 3, H, W) reconstructed RGB
    """
    def __init__(self, input_channels: int = 4, output_channels: int = 3):
        super().__init__()
        
        # Initial convolution
        self.initial_conv = nn.Conv2d(input_channels, BASE_CHANNELS, kernel_size=7, padding=3)
        
        # Encoder path
        self.enc1 = EncoderBlock(BASE_CHANNELS, BASE_CHANNELS * 2)
        self.enc2 = EncoderBlock(BASE_CHANNELS * 2, BASE_CHANNELS * 4)
        self.enc3 = EncoderBlock(BASE_CHANNELS * 4, BASE_CHANNELS * 8)
        self.enc4 = EncoderBlock(BASE_CHANNELS * 8, BASE_CHANNELS * 16)
        
        # Bottleneck
        self.bottleneck = nn.Sequential(
            ResidualBlock(BASE_CHANNELS * 16, BASE_CHANNELS * 16),
            ResidualBlock(BASE_CHANNELS * 16, BASE_CHANNELS * 16)
        )
        
        # Decoder path
        self.dec1 = DecoderBlock(BASE_CHANNELS * 16, BASE_CHANNELS * 8, BASE_CHANNELS * 8)
        self.dec2 = DecoderBlock(BASE_CHANNELS * 8, BASE_CHANNELS * 4, BASE_CHANNELS * 4)
        self.dec3 = DecoderBlock(BASE_CHANNELS * 4, BASE_CHANNELS * 2, BASE_CHANNELS * 2)
        self.dec4 = DecoderBlock(BASE_CHANNELS * 2, BASE_CHANNELS, BASE_CHANNELS)
        
        # Output head
        self.output_conv = nn.Conv2d(BASE_CHANNELS, output_channels, kernel_size=3, padding=1)
        self.output_activation = nn.Tanh()  # Output range [-1, 1]
        
        # Register hooks for gating (optional)
        self.gating_state: Optional[GatingState] = None
        
        self._count_parameters()
        
    def _count_parameters(self):
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        logger.info(f"MoebiusTiny initialized: Total params={total_params:,}, Trainable={trainable_params:,}")
        if total_params > 15_000_000:
            logger.warning(f"MoebiusTiny exceeds 15M params limit: {total_params:,}")
        
    def forward(self, x: torch.Tensor, rank_modulation: Optional[float] = None) -> InferenceResult:
        """
        Forward pass with optional rank modulation.
        
        Args:
            x: Input tensor (B, 4, H, W) - RGB + Mask
            rank_modulation: Scalar in [1.0, 5.0] from gating head. 
                             If None, uses full rank.
            
        Returns:
            InferenceResult containing reconstructed image and metadata.
        """
        # Set gating state if modulation provided
        if rank_modulation is not None:
            self.gating_state = GatingState(rank=rank_modulation)
        
        # Store skip connections
        skips = []
        
        # Encoder
        x = F.silu(self.initial_conv(x))
        skips.append(x)
        
        x = self.enc1(x)
        skips.append(x)
        
        x = self.enc2(x)
        skips.append(x)
        
        x = self.enc3(x)
        skips.append(x)
        
        x = self.enc4(x)
        skips.append(x)
        
        # Bottleneck
        x = self.bottleneck(x)
        
        # Decoder
        x = self.dec1(x, skips[-1])
        x = self.dec2(x, skips[-2])
        x = self.dec3(x, skips[-3])
        x = self.dec4(x, skips[-4])
        
        # Output
        out = self.output_activation(self.output_conv(x))
        
        return InferenceResult(
            image=out,
            gating_state=self.gating_state,
            metadata={
                "input_shape": x.shape,
                "modulation_applied": rank_modulation is not None
            }
        )
    
    def set_rank_modulation(self, rank: float):
        """
        Convenience method to set rank modulation externally.
        
        Args:
            rank: Float in [1.0, 5.0] representing complexity score.
        """
        self.gating_state = GatingState(rank=rank)
        
    def get_parameter_count(self) -> int:
        """Returns total parameter count."""
        return sum(p.numel() for p in self.parameters())

def create_moebius_tiny(pretrained_path: Optional[str] = None) -> MoebiusTiny:
    """
    Factory function to create a MoebiusTiny instance.
    
    Args:
        pretrained_path: Optional path to pretrained weights.
        
    Returns:
        Initialized MoebiusTiny model.
    """
    model = MoebiusTiny()
    
    if pretrained_path and pretrained_path.exists():
        logger.info(f"Loading pretrained weights from {pretrained_path}")
        state_dict = torch.load(pretrained_path, map_location='cpu', weights_only=True)
        model.load_state_dict(state_dict)
    else:
        logger.info("Initializing MoebiusTiny with random weights")
        
    return model

def main():
    """
    CLI entry point for testing MoebiusTiny.
    Runs a forward pass with a dummy input and reports parameter count.
    """
    logger.info("Running MoebiusTiny self-test...")
    
    # Create model
    model = create_moebius_tiny()
    model.eval()
    
    # Create dummy input (batch_size=2, channels=4, H=256, W=256)
    dummy_input = torch.randn(2, 4, 256, 256)
    
    # Forward pass
    with torch.no_grad():
        result = model(dummy_input)
    
    logger.info(f"Forward pass successful.")
    logger.info(f"Input shape: {dummy_input.shape}")
    logger.info(f"Output shape: {result.image.shape}")
    logger.info(f"Total parameters: {model.get_parameter_count():,}")
    
    # Test with rank modulation
    model.set_rank_modulation(2.5)
    with torch.no_grad():
        result_mod = model(dummy_input, rank_modulation=2.5)
    
    logger.info(f"Forward pass with modulation successful.")
    logger.info(f"Gating state: {result_mod.gating_state}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
