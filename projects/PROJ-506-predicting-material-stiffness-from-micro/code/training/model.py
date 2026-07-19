"""
CNN Model Definitions for Stiffness Prediction.

Defines the shallow CNN architecture for predicting material stiffness.
"""

import torch
import torch.nn as nn

class StiffnessPredictorCNN(nn.Module):
    """
    Shallow Convolutional Neural Network for stiffness prediction.

    Architecture:
    - Conv2d -> ReLU -> MaxPool
    - Conv2d -> ReLU -> MaxPool
    - Global Average Pooling
    - Fully Connected -> Output
    """

    def __init__(self, input_channels: int = 1, output_dim: int = 1):
        super(StiffnessPredictorCNN, self).__init__()
        
        self.features = nn.Sequential(
            # Layer 1
            nn.Conv2d(input_channels, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            # Layer 2
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            # Layer 3
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1))  # Global Average Pooling
        )
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, output_dim)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

def create_model(input_channels: int = 1, output_dim: int = 1) -> StiffnessPredictorCNN:
    """
    Factory function to create the CNN model.

    Args:
        input_channels: Number of input channels (default 1 for grayscale).
        output_dim: Number of output dimensions (default 1 for scalar stiffness).

    Returns:
        Initialized StiffnessPredictorCNN model.
    """
    return StiffnessPredictorCNN(input_channels, output_dim)
