"""
Unit tests for CNN model definition (T018).
"""
import pytest
import torch
import os

# Ensure we can import from code/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.cnn import MaterialStrengthCNN, get_model, count_parameters


class TestMaterialStrengthCNN:
    """Tests for the MaterialStrengthCNN class."""

    @pytest.mark.parametrize("backbone", ["mobilenet_v2", "resnet18"])
    def test_model_creation(self, backbone):
        """Test that models can be instantiated."""
        model = MaterialStrengthCNN(backbone_name=backbone)
        assert model is not None
        assert model.backbone_name == backbone

    @pytest.mark.parametrize("backbone", ["mobilenet_v2", "resnet18"])
    def test_forward_pass(self, backbone):
        """Test that forward pass produces correct output shape."""
        model = MaterialStrengthCNN(backbone_name=backbone)
        batch_size = 4
        # Input: (B, C, H, W) = (4, 3, 224, 224)
        x = torch.randn(batch_size, 3, 224, 224)

        model.eval()
        with torch.no_grad():
            output = model(x)

        assert output.shape == (batch_size, 1), f"Expected shape (4, 1), got {output.shape}"

    @pytest.mark.parametrize("backbone", ["mobilenet_v2", "resnet18"])
    def test_freeze_backbone(self, backbone):
        """Test that backbone parameters are frozen when requested."""
        model = MaterialStrengthCNN(backbone_name=backbone, freeze_backbone=True)

        # Check that backbone parameters require_grad is False
        for name, param in model.backbone.named_parameters():
            assert not param.requires_grad, f"Parameter {name} should be frozen"

        # Check that regressor parameters require_grad is True
        for name, param in model.regressor.named_parameters():
            assert param.requires_grad, f"Parameter {name} in regressor should be trainable"

    def test_invalid_backbone(self):
        """Test that invalid backbone name raises ValueError."""
        with pytest.raises(ValueError):
            MaterialStrengthCNN(backbone_name="invalid_backbone")

    @pytest.mark.parametrize("backbone", ["mobilenet_v2", "resnet18"])
    def test_count_parameters(self, backbone):
        """Test parameter counting logic."""
        model = MaterialStrengthCNN(backbone_name=backbone, freeze_backbone=True)
        total, trainable = count_parameters(model)

        assert total > 0
        assert trainable > 0
        # For frozen backbone, trainable should be significantly less than total
        # (specifically, just the regressor parameters)
        assert trainable < total


class TestGetModel:
    """Tests for the get_model factory function."""

    def test_get_model_default(self):
        """Test get_model with default arguments."""
        model, feature_dim = get_model()
        assert model is not None
        assert feature_dim == 1280  # MobileNetV2 default

    def test_get_model_resnet(self):
        """Test get_model with ResNet18."""
        model, feature_dim = get_model(backbone_name="resnet18")
        assert model is not None
        assert feature_dim == 512

    def test_get_model_seed(self):
        """Test that get_model accepts a seed argument."""
        model, _ = get_model(seed=42)
        assert model is not None