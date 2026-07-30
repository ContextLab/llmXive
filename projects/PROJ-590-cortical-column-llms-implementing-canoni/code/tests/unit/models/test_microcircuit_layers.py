"""
Unit tests for Microcircuit Layer definitions (T007a).
Verifies that L23Layer, L4Layer, L5Layer, L6Layer inherit from nn.Module
and implement forward(x) correctly.
"""
import pytest
import torch
import torch.nn as nn
from src.models.microcircuit import L23Layer, L4Layer, L5Layer, L6Layer, LayerConfig


class TestL23Layer:
    def test_inheritance(self):
        config = LayerConfig(name="L23", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L23Layer(config)
        assert isinstance(layer, nn.Module)

    def test_forward_shape(self):
        config = LayerConfig(name="L23", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L23Layer(config)
        x = torch.randn(4, 10)  # batch=4, dim=10
        out = layer(x)
        assert out.shape == (4, 20)

    def test_forward_pass(self):
        config = LayerConfig(name="L23", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L23Layer(config)
        x = torch.ones(2, 10)
        out = layer(x)
        assert out is not None
        assert not torch.isnan(out).any()


class TestL4Layer:
    def test_inheritance(self):
        config = LayerConfig(name="L4", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L4Layer(config)
        assert isinstance(layer, nn.Module)

    def test_forward_shape(self):
        config = LayerConfig(name="L4", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L4Layer(config)
        x = torch.randn(4, 10)
        out = layer(x)
        assert out.shape == (4, 20)


class TestL5Layer:
    def test_inheritance(self):
        config = LayerConfig(name="L5", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L5Layer(config)
        assert isinstance(layer, nn.Module)

    def test_forward_shape(self):
        config = LayerConfig(name="L5", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L5Layer(config)
        x = torch.randn(4, 10)
        out = layer(x)
        assert out.shape == (4, 20)


class TestL6Layer:
    def test_inheritance(self):
        config = LayerConfig(name="L6", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L6Layer(config)
        assert isinstance(layer, nn.Module)

    def test_forward_shape(self):
        config = LayerConfig(name="L6", input_dim=10, output_dim=20, hidden_dim=20)
        layer = L6Layer(config)
        x = torch.randn(4, 10)
        out = layer(x)
        assert out.shape == (4, 20)


class TestLayerConfigs:
    def test_config_defaults(self):
        config = LayerConfig(name="Test", input_dim=10, output_dim=20, hidden_dim=20)
        assert config.activation == "relu"
        assert config.use_bias is True
        assert config.dropout_rate == 0.0
        assert config.exc_ratio == 0.8

    def test_invalid_activation(self):
        with pytest.raises(ValueError):
            LayerConfig(name="Test", input_dim=10, output_dim=20, hidden_dim=20, activation="invalid")