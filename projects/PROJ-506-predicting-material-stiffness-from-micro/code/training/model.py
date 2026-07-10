"""
Shallow CNN architecture for stiffness prediction.
CPU-optimized model definition.
"""
import torch
import torch.nn as nn

class StiffnessPredictorCNN(nn.Module):
    """
    Shallow CNN for predicting effective stiffness from microstructure images.
    
    Architecture:
    - 2 Conv layers with ReLU
    - Global Average Pooling
    - Fully connected output
    """
    def __init__(self, input_size: int = 128, output_dim: int = 6):
        super(StiffnessPredictorCNN, self).__init__()
        
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=7, stride=2, padding=3),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
            nn.Conv2d(16, 32, kernel_size=5, stride=2, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
        )
        
        # Calculate feature map size after pooling
        # 128 -> 64 -> 32 -> 16 -> 8 -> 4
        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, output_dim)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.avg_pool(x)
        x = self.classifier(x)
        return x

def create_model(input_size: int = 128) -> StiffnessPredictorCNN:
    """Factory function to create model instance."""
    return StiffnessPredictorCNN(input_size=input_size)

if __name__ == "__main__":
    # Simple test
    model = create_model()
    dummy_input = torch.randn(1, 1, 128, 128)
    output = model(dummy_input)
    print(f"Model output shape: {output.shape}")
