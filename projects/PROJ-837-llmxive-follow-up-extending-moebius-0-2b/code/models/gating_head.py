"""
Gating Head for Moebius-Dynamic.

A lightweight convolutional head designed to output a scalar complexity score
from an image (or feature map). Strictly constrained to <= 5M parameters.
"""
import torch
import torch.nn as nn
import math
from typing import Tuple, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration for the gating head to ensure parameter budget compliance
# Target: <= 5,000,000 parameters
# Input expected: (B, C, H, W) where C is typically small (e.g., 3 for RGB or low-dim features)
# Output: (B, 1) scalar complexity score

class GatingHead(nn.Module):
    """
    Lightweight Gating Head.

    Architecture:
    - 3 Convolutional Blocks (Conv -> BN -> ReLU -> MaxPool)
    - Global Average Pooling
    - 2 Linear Layers (Bottleneck)
    - Output: Scalar [1, 5] (clamped in forward pass or via activation)

    Designed to run efficiently on CPU.
    """

    def __init__(
        self,
        in_channels: int = 3,
        out_channels_base: int = 32,
        hidden_dim: int = 128,
        out_dim: int = 1,
        max_params: int = 5_000_000
    ):
        super().__init__()
        self.in_channels = in_channels
        self.max_params = max_params

        # Feature Extractor (Lightweight)
        # Block 1: 3 -> 32
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels, out_channels_base, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(out_channels_base),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        # Block 2: 32 -> 64
        self.conv2 = nn.Sequential(
            nn.Conv2d(out_channels_base, out_channels_base * 2, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(out_channels_base * 2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        # Block 3: 64 -> 128
        self.conv3 = nn.Sequential(
            nn.Conv2d(out_channels_base * 2, out_channels_base * 4, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(out_channels_base * 4),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Calculate flattened size after 3 pooling layers (assuming 256x256 input -> 32x32)
        # 256 -> 128 -> 64 -> 32
        # If input is different, we compute dynamically in forward or assume standard size.
        # We use a dynamic calculation in forward to be safe, but define linear layers based on a standard.
        # Standard assumption: Input 256x256 -> 32x32 after 3 downsamplings (2*2*2 = 8).
        # 32 * 32 * 128 = 131,072 features.
        # To stay under 5M, we need to be careful here.
        # 131k * 128 (hidden) = ~16M params -> Too big.
        # Strategy: Use Global Average Pooling instead of Flatten + Linear to reduce params drastically.

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))

        # MLP Head
        # Input: 128 (from conv3 output channels)
        self.fc1 = nn.Linear(out_channels_base * 4, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, out_dim)

        self._verify_parameter_count()

    def _verify_parameter_count(self):
        total_params = sum(p.numel() for p in self.parameters())
        logger.info(f"GatingHead initialized with {total_params:,} parameters.")
        if total_params > self.max_params:
            raise ValueError(
                f"GatingHead parameter count ({total_params}) exceeds limit ({self.max_params}). "
                f"Adjust hidden_dim or out_channels_base."
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (B, C, H, W).

        Returns:
            Tensor of shape (B, 1) representing complexity score.
        """
        # Feature extraction
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)

        # Global Average Pooling to reduce spatial dims to 1x1
        x = self.global_pool(x)
        x = torch.flatten(x, 1)

        # MLP
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)

        # Optional: Clamp output to a reasonable range if needed by downstream logic
        # The task asks for a scalar complexity. We return raw float, 
        # but typically these are normalized 0-1 or 1-5. 
        # We will leave it as raw float for the loss function to handle scaling,
        # or apply a sigmoid if 0-1 is strictly required. 
        # Given the task "output scalar complexity", we return the raw value.
        return x


def create_gating_head(in_channels: int = 3) -> GatingHead:
    """
    Factory function to create a GatingHead instance.
    """
    return GatingHead(in_channels=in_channels)


def count_parameters(model: nn.Module) -> int:
    """
    Utility to count trainable parameters.
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def main():
    """
    CLI entry point to verify the gating head architecture and parameter count.
    """
    logger.info("Running GatingHead verification script...")
    
    # Test with standard input
    test_input = torch.randn(1, 3, 256, 256)
    
    try:
        head = create_gating_head(in_channels=3)
        output = head(test_input)
        
        params = count_parameters(head)
        logger.info(f"Model Parameters: {params:,}")
        logger.info(f"Output shape: {output.shape}")
        logger.info(f"Output value (sample): {output.item():.4f}")
        
        if params <= 5_000_000:
            logger.info("VERIFICATION PASSED: Parameter count is within 5M limit.")
        else:
            logger.error("VERIFICATION FAILED: Parameter count exceeds 5M limit.")
            raise SystemExit(1)
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()