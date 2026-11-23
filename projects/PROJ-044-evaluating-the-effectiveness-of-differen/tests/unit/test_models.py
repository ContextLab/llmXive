"""
Unit tests for model entities in code/models/cnn.py.

These tests verify:
1. Model instantiation with default and custom parameters
2. Forward pass produces correct output shapes
3. Model initialization is deterministic
4. Factory function works correctly
5. Model info extraction works correctly
"""

import pytest
import torch
import torch.nn as nn
from code.models.cnn import (
    SmallCNN,
    SmallMLP,
    get_model,
    get_model_info,
    FEMNIST_NUM_CLASSES,
    FEMNIST_IMAGE_SIZE
)


class TestSmallCNN:
    """Tests for the SmallCNN model."""
    
    def test_default_initialization(self):
        """Test that SmallCNN initializes with default parameters."""
        model = SmallCNN()
        assert model.num_classes == FEMNIST_NUM_CLASSES
        assert model.input_size == FEMNIST_IMAGE_SIZE
        assert isinstance(model, nn.Module)
    
    def test_custom_initialization(self):
        """Test that SmallCNN can be initialized with custom parameters."""
        model = SmallCNN(num_classes=10, input_size=32)
        assert model.num_classes == 10
        assert model.input_size == 32
    
    def test_forward_pass_default(self):
        """Test forward pass with default parameters."""
        model = SmallCNN()
        batch_size = 32
        x = torch.randn(batch_size, 1, FEMNIST_IMAGE_SIZE, FEMNIST_IMAGE_SIZE)
        output = model(x)
        assert output.shape == (batch_size, FEMNIST_NUM_CLASSES)
    
    def test_forward_pass_custom(self):
        """Test forward pass with custom parameters."""
        model = SmallCNN(num_classes=10, input_size=32)
        batch_size = 16
        x = torch.randn(batch_size, 1, 32, 32)
        output = model(x)
        assert output.shape == (batch_size, 10)
    
    def test_forward_pass_3d_input(self):
        """Test forward pass with 3D input (missing batch dimension)."""
        model = SmallCNN()
        x = torch.randn(1, FEMNIST_IMAGE_SIZE, FEMNIST_IMAGE_SIZE)  # 3D input
        output = model(x)
        assert output.shape == (1, FEMNIST_NUM_CLASSES)
    
    def test_model_parameters_count(self):
        """Test that the model has a reasonable number of parameters."""
        model = SmallCNN()
        num_params = sum(p.numel() for p in model.parameters())
        # SmallCNN should have a reasonable number of parameters (not too many)
        assert 10000 < num_params < 500000
    
    def test_model_weight_initialization(self):
        """Test that model weights are properly initialized."""
        model1 = SmallCNN()
        model2 = SmallCNN()
        
        # Weights should be different between two instances
        for (name1, param1), (name2, param2) in zip(
            model1.named_parameters(), model2.named_parameters()
        ):
            assert name1 == name2
            # Check that weights are not identical (random initialization)
            if not torch.allclose(param1, param2, atol=1e-6):
                continue
            else:
                # If they are very close, it's extremely unlikely with random init
                # This is just a sanity check
                assert torch.allclose(param1, param2, atol=1e-6) is False
    
    def test_model_deterministic_with_seed(self):
        """Test that model initialization is deterministic with a fixed seed."""
        torch.manual_seed(42)
        model1 = SmallCNN()
        
        torch.manual_seed(42)
        model2 = SmallCNN()
        
        # Weights should be identical with same seed
        for (name1, param1), (name2, param2) in zip(
            model1.named_parameters(), model2.named_parameters()
        ):
            assert torch.allclose(param1, param2)
    
    def test_model_training_mode(self):
        """Test that model works in training and evaluation modes."""
        model = SmallCNN()
        x = torch.randn(8, 1, FEMNIST_IMAGE_SIZE, FEMNIST_IMAGE_SIZE)
        
        model.train()
        output_train = model(x)
        assert output_train.shape == (8, FEMNIST_NUM_CLASSES)
        
        model.eval()
        output_eval = model(x)
        assert output_eval.shape == (8, FEMNIST_NUM_CLASSES)
    
    def test_model_gradient_flow(self):
        """Test that gradients flow through the model."""
        model = SmallCNN()
        x = torch.randn(8, 1, FEMNIST_IMAGE_SIZE, FEMNIST_IMAGE_SIZE, requires_grad=True)
        output = model(x)
        loss = output.sum()
        loss.backward()
        
        # Check that gradients exist
        for param in model.parameters():
            assert param.grad is not None
            assert param.grad.shape == param.shape


class TestSmallMLP:
    """Tests for the SmallMLP model."""
    
    def test_default_initialization(self):
        """Test that SmallMLP initializes with default parameters."""
        model = SmallMLP()
        assert model.num_classes == FEMNIST_NUM_CLASSES
        assert model.input_size == FEMNIST_IMAGE_SIZE
        assert isinstance(model, nn.Module)
    
    def test_custom_initialization(self):
        """Test that SmallMLP can be initialized with custom parameters."""
        model = SmallMLP(num_classes=10, input_size=32)
        assert model.num_classes == 10
        assert model.input_size == 32
    
    def test_forward_pass_default(self):
        """Test forward pass with default parameters."""
        model = SmallMLP()
        batch_size = 32
        x = torch.randn(batch_size, 1, FEMNIST_IMAGE_SIZE, FEMNIST_IMAGE_SIZE)
        output = model(x)
        assert output.shape == (batch_size, FEMNIST_NUM_CLASSES)
    
    def test_forward_pass_flattened_input(self):
        """Test forward pass with flattened input."""
        model = SmallMLP()
        batch_size = 32
        x = torch.randn(batch_size, FEMNIST_IMAGE_SIZE * FEMNIST_IMAGE_SIZE)
        output = model(x)
        assert output.shape == (batch_size, FEMNIST_NUM_CLASSES)
    
    def test_model_parameters_count(self):
        """Test that the model has a reasonable number of parameters."""
        model = SmallMLP()
        num_params = sum(p.numel() for p in model.parameters())
        # SmallMLP should have a reasonable number of parameters
        assert 5000 < num_params < 500000
    
    def test_model_gradient_flow(self):
        """Test that gradients flow through the model."""
        model = SmallMLP()
        x = torch.randn(8, 1, FEMNIST_IMAGE_SIZE, FEMNIST_IMAGE_SIZE, requires_grad=True)
        output = model(x)
        loss = output.sum()
        loss.backward()
        
        # Check that gradients exist
        for param in model.parameters():
            assert param.grad is not None
            assert param.grad.shape == param.shape


class TestGetModel:
    """Tests for the get_model factory function."""
    
    def test_get_cnn_model(self):
        """Test that get_model creates a SmallCNN instance."""
        model = get_model("cnn")
        assert isinstance(model, SmallCNN)
    
    def test_get_mlp_model(self):
        """Test that get_model creates a SmallMLP instance."""
        model = get_model("mlp")
        assert isinstance(model, SmallMLP)
    
    def test_get_model_with_custom_params(self):
        """Test that get_model passes custom parameters correctly."""
        model = get_model("cnn", num_classes=10)
        assert model.num_classes == 10
        assert isinstance(model, SmallCNN)
    
    def test_get_model_invalid_type(self):
        """Test that get_model raises ValueError for invalid model type."""
        with pytest.raises(ValueError, match="Unknown model type"):
            get_model("invalid_type")
    
    def test_get_model_case_insensitive(self):
        """Test that get_model is case insensitive."""
        model1 = get_model("CNN")
        model2 = get_model("cnn")
        assert isinstance(model1, SmallCNN)
        assert isinstance(model2, SmallCNN)

class TestGetModelInfo:
    """Tests for the get_model_info function."""
    
    def test_get_cnn_info(self):
        """Test that get_model_info returns correct info for SmallCNN."""
        model = SmallCNN()
        info = get_model_info(model)
        
        assert info["name"] == "SmallCNN"
        assert info["num_classes"] == FEMNIST_NUM_CLASSES
        assert "num_params" in info
        assert "num_trainable_params" in info
        assert info["num_params"] > 0
        assert info["num_trainable_params"] > 0
    
    def test_get_mlp_info(self):
        """Test that get_model_info returns correct info for SmallMLP."""
        model = SmallMLP()
        info = get_model_info(model)
        
        assert info["name"] == "SmallMLP"
        assert info["num_classes"] == FEMNIST_NUM_CLASSES
        assert "num_params" in info
        assert "num_trainable_params" in info
        assert info["num_params"] > 0
        assert info["num_trainable_params"] > 0
    
    def test_info_param_consistency(self):
        """Test that num_params matches actual parameter count."""
        model = SmallCNN()
        info = get_model_info(model)
        actual_params = sum(p.numel() for p in model.parameters())
        assert info["num_params"] == actual_params
        assert info["num_trainable_params"] == actual_params  # All params are trainable by default