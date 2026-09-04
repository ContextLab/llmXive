"""
Baseline CNN Encoder for raw pixel input.

Implements a simple, limited-depth CNN to process downsampled (224x224) images
and produce a fixed-size feature vector. This serves as the pixel-based
baseline for comparison against the RF token extractor.

Constraints (FR-004, Plan Phase 0 Step 3):
- Input: 3-channel RGB image, 224x224.
- Depth: Limited (no ResNet-style residual blocks, max 4 conv blocks).
- Output: Fixed-size embedding vector (512 dim) to match AR model input expectations.
- No pre-trained weights (trained from scratch on PubLayNet).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple, List
import logging

from config import get_config_dict

logger = logging.getLogger(__name__)


class SimpleCNNBaseline(nn.Module):
    """
    A lightweight CNN encoder for raw pixel inputs.
    
    Architecture:
    - 4 Convolutional Blocks (Conv -> BatchNorm -> ReLU -> MaxPool)
    - Global Average Pooling
    - Fully Connected projection to embedding_dim
    """
    def __init__(
        self,
        input_channels: int = 3,
        input_size: int = 224,
        embedding_dim: int = 512,
        base_filters: int = 32,
        max_filters: int = 256
    ):
        super().__init__()
        self.input_size = input_size
        self.embedding_dim = embedding_dim

        # Calculate expected size after pooling to ensure FC layer fits
        # 224 -> 112 -> 56 -> 28 -> 14 (after 4 pools of 2)
        self.pool_depth = 4
        self.feature_map_size = input_size // (2 ** self.pool_depth)
        
        layers = []
        current_filters = base_filters
        
        # Block 1: 224x224 -> 112x112
        layers.append(nn.Conv2d(input_channels, current_filters, kernel_size=3, stride=1, padding=1))
        layers.append(nn.BatchNorm2d(current_filters))
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.MaxPool2d(kernel_size=2, stride=2))
        
        # Block 2: 112x112 -> 56x56
        current_filters = min(current_filters * 2, max_filters)
        layers.append(nn.Conv2d(current_filters // 2, current_filters, kernel_size=3, stride=1, padding=1))
        layers.append(nn.BatchNorm2d(current_filters))
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.MaxPool2d(kernel_size=2, stride=2))
        
        # Block 3: 56x56 -> 28x28
        prev_filters = current_filters
        current_filters = min(current_filters * 2, max_filters)
        layers.append(nn.Conv2d(prev_filters, current_filters, kernel_size=3, stride=1, padding=1))
        layers.append(nn.BatchNorm2d(current_filters))
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.MaxPool2d(kernel_size=2, stride=2))
        
        # Block 4: 28x28 -> 14x14
        prev_filters = current_filters
        current_filters = min(current_filters * 2, max_filters)
        layers.append(nn.Conv2d(prev_filters, current_filters, kernel_size=3, stride=1, padding=1))
        layers.append(nn.BatchNorm2d(current_filters))
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.MaxPool2d(kernel_size=2, stride=2))
        
        self.feature_extractor = nn.Sequential(*layers)
        
        # Calculate flattened size
        flat_size = current_filters * self.feature_map_size * self.feature_map_size
        
        # Projection to embedding_dim
        self.projection = nn.Sequential(
            nn.Linear(flat_size, embedding_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (B, C, H, W). Expected H=W=224.
        
        Returns:
            Tensor of shape (B, embedding_dim).
        """
        if x.shape[-1] != self.input_size or x.shape[-2] != self.input_size:
            logger.warning(f"Input image size {x.shape[-2:]} does not match expected {self.input_size}x{self.input_size}. "
                         "This may cause dimension mismatch errors in the projection layer.")
        
        # Extract features
        features = self.feature_extractor(x)
        
        # Flatten: (B, C, H, W) -> (B, C*H*W)
        batch_size = features.size(0)
        features = features.view(batch_size, -1)
        
        # Project to embedding
        embeddings = self.projection(features)
        
        return embeddings


def get_default_config() -> Dict[str, Any]:
    """Returns default configuration for the baseline model."""
    return {
        "input_channels": 3,
        "input_size": 224,
        "embedding_dim": 512,
        "base_filters": 32,
        "max_filters": 256
    }


def create_baseline_model(config: Optional[Dict[str, Any]] = None) -> SimpleCNNBaseline:
    """
    Factory function to create a SimpleCNNBaseline model.
    
    Args:
        config: Optional dictionary of hyperparameters. If None, uses defaults.
    
    Returns:
        Initialized SimpleCNNBaseline model.
    """
    cfg = config if config else get_default_config()
    model = SimpleCNNBaseline(
        input_channels=cfg.get("input_channels", 3),
        input_size=cfg.get("input_size", 224),
        embedding_dim=cfg.get("embedding_dim", 512),
        base_filters=cfg.get("base_filters", 32),
        max_filters=cfg.get("max_filters", 256)
    )
    logger.info(f"Created Baseline CNN Model with {sum(p.numel() for p in model.parameters()):,} parameters")
    return model


def main():
    """
    Simple verification script to instantiate the model and check forward pass.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    config = get_default_config()
    
    # Create model
    model = create_baseline_model(config)
    
    # Create dummy input (Batch=1, Channels=3, H=224, W=224)
    dummy_input = torch.randn(1, 3, 224, 224)
    
    # Forward pass
    model.eval()
    with torch.no_grad():
        output = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Expected output shape: (1, {config['embedding_dim']})")
    
    assert output.shape == (1, config['embedding_dim']), "Output dimension mismatch!"
    print("Baseline model verification PASSED.")


if __name__ == "__main__":
    main()