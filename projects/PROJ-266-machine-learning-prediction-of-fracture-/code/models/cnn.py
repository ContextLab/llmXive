"""
Multi-block CNN architecture for fracture toughness prediction.
Architecture: Conv-ReLU-BN-MaxPool repeated blocks.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional

class CNN(nn.Module):
    """
    Convolutional Neural Network for predicting fracture toughness (K_IC)
    from microstructure images.

    Architecture:
    - Input: Grayscale images (1 channel), resized to 128x128
    - Blocks: [Conv -> ReLU -> BatchNorm -> MaxPool] x 4
    - Head: Flatten -> Linear -> ReLU -> Dropout -> Linear (Regression)

    Output: Single float value representing predicted K_IC.
    """

    def __init__(
        self,
        input_channels: int = 1,
        input_size: Tuple[int, int] = (128, 128),
        base_filters: int = 32,
        dropout_rate: float = 0.5
    ):
        """
        Initialize the CNN.

        Args:
            input_channels: Number of input channels (1 for grayscale).
            input_size: Expected input image size (height, width).
            base_filters: Number of filters in the first convolutional layer.
            dropout_rate: Dropout probability for regularization.
        """
        super(CNN, self).__init__()

        self.input_size = input_size
        self.base_filters = base_filters

        # Block 1: 128x128 -> 64x64
        self.block1 = nn.Sequential(
            nn.Conv2d(input_channels, base_filters, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(base_filters),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Block 2: 64x64 -> 32x32
        self.block2 = nn.Sequential(
            nn.Conv2d(base_filters, base_filters * 2, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(base_filters * 2),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Block 3: 32x32 -> 16x16
        self.block3 = nn.Sequential(
            nn.Conv2d(base_filters * 2, base_filters * 4, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(base_filters * 4),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Block 4: 16x16 -> 8x8
        self.block4 = nn.Sequential(
            nn.Conv2d(base_filters * 4, base_filters * 8, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(base_filters * 8),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Calculate flattened size
        # After 4 maxpool layers (2^4 = 16 reduction): 128/16 = 8
        self.feature_dim = base_filters * 8 * 8 * 8  # filters * height * width

        # Fully connected head
        self.fc1 = nn.Linear(self.feature_dim, 256)
        self.fc2 = nn.Linear(256, 64)
        self.fc3 = nn.Linear(64, 1)  # Regression output

        self.dropout = nn.Dropout(dropout_rate)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch_size, channels, height, width).

        Returns:
            Tensor of shape (batch_size, 1) containing predicted K_IC values.
        """
        # Ensure input is 4D
        if x.dim() == 3:
            x = x.unsqueeze(0)  # Add batch dimension if missing

        # Convolutional blocks
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)

        # Flatten
        x = x.view(x.size(0), -1)

        # Fully connected layers with dropout
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)

        return x

    def get_feature_map(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract feature maps from the last convolutional layer (before flattening).
        Useful for Grad-CAM or other attribution methods.

        Args:
            x: Input tensor.

        Returns:
            Feature map tensor of shape (batch_size, filters, height, width).
        """
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        return x