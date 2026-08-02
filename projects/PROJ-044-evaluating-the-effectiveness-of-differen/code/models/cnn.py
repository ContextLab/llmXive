"""
Small CNN model entity for FEMNIST in Federated Learning experiments.

This module defines a compact Convolutional Neural Network architecture
suitable for the FEMNIST dataset (62 classes: 0-9, a-z, A-Z).
The architecture is designed to be lightweight for federated learning
scenarios while maintaining reasonable accuracy.

Attributes:
    FEMNIST_NUM_CLASSES (int): Number of output classes (62 for FEMNIST).
    FEMNIST_IMAGE_SIZE (int): Input image size (28x28 for FEMNIST).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

# FEMNIST specific constants
FEMNIST_NUM_CLASSES = 62  # 0-9, a-z, A-Z
FEMNIST_IMAGE_SIZE = 28


class SmallCNN(nn.Module):
    """
    A small Convolutional Neural Network for FEMNIST classification.
    
    Architecture:
    - Conv1: 1 -> 32 channels, 3x3 kernel
    - Conv2: 32 -> 64 channels, 3x3 kernel
    - Two fully connected layers with dropout
    - Output layer for 62 classes
    
    Args:
        num_classes (int, optional): Number of output classes. Defaults to FEMNIST_NUM_CLASSES.
        input_size (int, optional): Input image size. Defaults to FEMNIST_IMAGE_SIZE.
    
    Example:
        >>> model = SmallCNN()
        >>> x = torch.randn(32, 1, 28, 28)  # batch of 32 images
        >>> output = model(x)
        >>> print(output.shape)
        torch.Size([32, 62])
    """
    
    def __init__(self, num_classes: int = FEMNIST_NUM_CLASSES, input_size: int = FEMNIST_IMAGE_SIZE):
        super(SmallCNN, self).__init__()
        self.num_classes = num_classes
        self.input_size = input_size
        
        # Convolutional layers
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        
        # Calculate feature map size after convolutions and pooling
        # Input: 28x28
        # After conv1 + pool: 14x14
        # After conv2 + pool: 7x7
        self.feature_dim = 64 * 7 * 7
        
        # Fully connected layers
        self.fc1 = nn.Linear(self.feature_dim, 128)
        self.fc2 = nn.Linear(128, num_classes)
        
        # Dropout for regularization
        self.dropout = nn.Dropout(0.5)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize weights using He initialization for conv layers and Xavier for FC layers."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.
        
        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, 1, 28, 28)
        
        Returns:
            torch.Tensor: Output logits of shape (batch_size, num_classes)
        """
        # Ensure input is 4D (batch, channels, height, width)
        if x.dim() == 3:
            x = x.unsqueeze(1)  # Add channel dimension if missing
        
        # Convolutional blocks
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2)  # 28x28 -> 14x14
        
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2)  # 14x14 -> 7x7
        
        # Flatten
        x = x.view(x.size(0), -1)
        
        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        
        return x


class SmallMLP(nn.Module):
    """
    A small Multi-Layer Perceptron for FEMNIST classification.
    
    This is a simpler alternative to the CNN, useful for ablation studies
    or when computational resources are extremely limited.
    
    Architecture:
    - Input: 784 flattened pixels
    - Hidden layers: 256 -> 128 neurons
    - Output: 62 classes
    
    Args:
        num_classes (int, optional): Number of output classes. Defaults to FEMNIST_NUM_CLASSES.
        input_size (int, optional): Input image size. Defaults to FEMNIST_IMAGE_SIZE.
    
    Example:
        >>> model = SmallMLP()
        >>> x = torch.randn(32, 1, 28, 28)
        >>> output = model(x)
        >>> print(output.shape)
        torch.Size([32, 62])
    """
    
    def __init__(self, num_classes: int = FEMNIST_NUM_CLASSES, input_size: int = FEMNIST_IMAGE_SIZE):
        super(SmallMLP, self).__init__()
        self.num_classes = num_classes
        self.input_size = input_size
        
        input_dim = input_size * input_size  # 784 for 28x28 images
        
        # Fully connected layers
        self.fc1 = nn.Linear(input_dim, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(0.5)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize weights using Xavier initialization."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.
        
        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, 1, 28, 28) or (batch_size, 784)
        
        Returns:
            torch.Tensor: Output logits of shape (batch_size, num_classes)
        """
        # Flatten if needed
        if x.dim() > 2:
            x = x.view(x.size(0), -1)
        
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x


def get_model(model_type: str = "cnn", **kwargs) -> nn.Module:
    """
    Factory function to create model instances.
    
    Args:
        model_type (str): Type of model to create. Options: "cnn", "mlp".
        **kwargs: Additional arguments passed to the model constructor.
    
    Returns:
        nn.Module: Instantiated model.
    
    Raises:
        ValueError: If model_type is not recognized.
    
    Example:
        >>> model = get_model("cnn")
        >>> model = get_model("mlp", num_classes=10)
    """
    model_type = model_type.lower()
    
    if model_type == "cnn":
        return SmallCNN(**kwargs)
    elif model_type == "mlp":
        return SmallMLP(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}. Supported types: 'cnn', 'mlp'")

def get_model_info(model: nn.Module) -> dict:
    """
    Get information about a model's architecture.
    
    Args:
        model (nn.Module): The model to inspect.
    
    Returns:
        dict: Dictionary containing model information including:
            - name: Model class name
            - num_params: Total number of parameters
            - num_trainable_params: Number of trainable parameters
            - num_classes: Number of output classes
    """
    num_params = sum(p.numel() for p in model.parameters())
    num_trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    return {
        "name": model.__class__.__name__,
        "num_params": num_params,
        "num_trainable_params": num_trainable_params,
        "num_classes": model.num_classes if hasattr(model, 'num_classes') else None
    }
