"""
CNN model architecture for stiffness prediction.

Implements a shallow convolutional neural network optimized for CPU training.
"""
import torch
import torch.nn as nn

class StiffnessPredictorCNN(nn.Module):
    """
    Shallow CNN for predicting effective stiffness from microstructure images.
    
    Architecture:
    - 2 Convolutional layers with ReLU activation
    - Global average pooling
    - Fully connected output layer
    """
    def __init__(self, input_size: int = 128, output_dim: int = 4):
        """
        Initialize the model.
        
        Args:
            input_size: Size of input image (default 128)
            output_dim: Dimension of output stiffness tensor (default 4 for plane strain)
        """
        super(StiffnessPredictorCNN, self).__init__()
        
        # Convolutional layers
        self.conv_layers = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        
        # Calculate feature size after pooling
        # 128 -> 64 -> 32
        feature_size = 32 * 32 * 32
        
        # Fully connected layers
        self.fc_layers = nn.Sequential(
            nn.Linear(feature_size, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, output_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, 1, 128, 128)
            
        Returns:
            Output tensor of shape (batch_size, output_dim)
        """
        # Convolutional layers
        x = self.conv_layers(x)
        
        # Global average pooling (flatten)
        x = x.view(x.size(0), -1)
        
        # Fully connected layers
        x = self.fc_layers(x)
        
        return x

def create_model(
    input_size: int = 128,
    output_dim: int = 4,
    device: str = 'cpu'
) -> StiffnessPredictorCNN:
    """
    Factory function to create and initialize the model.
    
    Args:
        input_size: Size of input image
        output_dim: Dimension of output
        device: Device to place model on ('cpu' or 'cuda')
        
    Returns:
        Initialized StiffnessPredictorCNN model
    """
    model = StiffnessPredictorCNN(input_size=input_size, output_dim=output_dim)
    model = model.to(device)
    return model

if __name__ == "__main__":
    # Simple test
    model = create_model()
    dummy_input = torch.randn(1, 1, 128, 128)
    output = model(dummy_input)
    print(f"Model output shape: {output.shape}")
    print("Model architecture test passed.")
