"""
CNN Model Definitions for Material Strength Prediction.

Implements MobileNetV2 and ResNet-18 backbones with frozen weights
for transfer learning, adapted for scalar yield strength regression.
"""
import torch
import torch.nn as nn
import torchvision.models as models
from typing import Optional, Tuple

from utils.config import get_seed


class MaterialStrengthCNN(nn.Module):
    """
    Regression model for predicting yield strength from microstructure images.

    Uses a pre-trained backbone (MobileNetV2 or ResNet-18) where the
    feature extractor is frozen. A custom regression head is added
    on top to map features to a scalar yield strength value.

    Args:
        backbone_name: 'mobilenet_v2' or 'resnet18'.
        freeze_backbone: If True, gradients are not computed for backbone weights.
        input_size: Expected image size (default 224).
    """

    BACKBONES = {"mobilenet_v2", "resnet18"}

    def __init__(
        self,
        backbone_name: str = "mobilenet_v2",
        freeze_backbone: bool = True,
        input_size: int = 224,
    ):
        super().__init__()

        if backbone_name not in self.BACKBONES:
            raise ValueError(f"Unsupported backbone: {backbone_name}. Choose from {self.BACKBONES}")

        self.backbone_name = backbone_name
        self.input_size = input_size

        # Initialize backbone
        if backbone_name == "mobilenet_v2":
            # MobileNetV2 expects 1280 features in its classifier
            self.backbone = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
            num_ftrs = self.backbone.classifier[1].in_features
            # Replace final layer with Identity to extract features
            self.backbone.classifier = nn.Identity()
        elif backbone_name == "resnet18":
            # ResNet18 expects 512 features
            self.backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
            num_ftrs = self.backbone.fc.in_features
            # Replace final layer with Identity
            self.backbone.fc = nn.Identity()

        # Freeze backbone if requested
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

        # Regression Head
        # Simple MLP: Features -> Hidden -> Output (1 scalar)
        self.regressor = nn.Sequential(
            nn.Linear(num_ftrs, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.3),
            nn.Linear(256, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Tensor of shape (B, C, H, W).

        Returns:
            Tensor of shape (B, 1) containing predicted yield strength.
        """
        features = self.backbone(x)
        # features shape: (B, num_ftrs)
        predictions = self.regressor(features)
        return predictions

    def get_feature_dim(self) -> int:
        """Returns the dimensionality of the feature vector before the regressor."""
        if self.backbone_name == "mobilenet_v2":
            return 1280
        elif self.backbone_name == "resnet18":
            return 512
        return 0


def get_model(
    backbone_name: str = "mobilenet_v2",
    freeze_backbone: bool = True,
    seed: Optional[int] = None,
) -> Tuple[MaterialStrengthCNN, int]:
    """
    Factory function to instantiate the model.

    Args:
        backbone_name: Name of the backbone architecture.
        freeze_backbone: Whether to freeze backbone weights.
        seed: Optional seed for reproducibility (passed to config).

    Returns:
        Tuple of (Model instance, feature_dim).
    """
    if seed is not None:
        from utils.config import set_seed
        set_seed(seed)

    model = MaterialStrengthCNN(
        backbone_name=backbone_name,
        freeze_backbone=freeze_backbone
    )

    return model, model.get_feature_dim()


def count_parameters(model: MaterialStrengthCNN) -> Tuple[int, int]:
    """
    Counts total and trainable parameters in the model.

    Args:
        model: The MaterialStrengthCNN instance.

    Returns:
        Tuple of (total_params, trainable_params).
    """
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable
