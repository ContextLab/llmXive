import torch
import torch.nn as nn

class StiffnessPredictorCNN(nn.Module):
    """
    Shallow CNN architecture for predicting material stiffness from microstructure images.
    
    Architecture:
    - Input: 1x128x128 (grayscale microstructure image)
    - Conv Block 1: Conv2d(1, 16, 7) + ReLU + MaxPool2d(2) -> 16x64x64
    - Conv Block 2: Conv2d(16, 32, 5) + ReLU + MaxPool2d(2) -> 32x31x31
    - Conv Block 3: Conv2d(32, 64, 3) + ReLU + GlobalAvgPool -> 64x1x1
    - Output: Linear(64, 1) -> scalar stiffness value
    
    FR-003 Compliance:
    - Uses several convolutional layers
    - Uses ReLU activations
    - Uses Global Average Pooling
    - Designed for CPU optimization (shallow depth, moderate filter counts)
    """
    def __init__(self):
        super().__init__()
        
        # Convolutional layers with ReLU activations
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=16, kernel_size=7, stride=1, padding=3)
        self.conv2 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=5, stride=1, padding=2)
        self.conv3 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1)
        
        # Pooling layers
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Global Average Pooling
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Fully connected output layer
        self.fc = nn.Linear(in_features=64, out_features=1)
        
        # Initialize weights
        self._initialize_weights()

    def _initialize_weights(self):
        """Initialize weights using He initialization for ReLU activations."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # Convolutional block 1
        x = torch.relu(self.conv1(x))
        x = self.pool1(x)
        
        # Convolutional block 2
        x = torch.relu(self.conv2(x))
        x = self.pool2(x)
        
        # Convolutional block 3
        x = torch.relu(self.conv3(x))
        
        # Global Average Pooling
        x = self.global_pool(x)
        
        # Flatten
        x = x.view(x.size(0), -1)
        
        # Output layer
        x = self.fc(x)
        
        return x

def create_model():
    """
    Factory function to create and return a StiffnessPredictorCNN instance.
    
    Returns:
        StiffnessPredictorCNN: Initialized model ready for training or inference.
    """
    return StiffnessPredictorCNN()