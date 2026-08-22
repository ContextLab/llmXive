"""
Unit tests for Microcircuit Layer definitions (T009d).
"""
import pytest
import torch
import torch.nn as nn
from src.models.microcircuit import (
    L23Layer, L4Layer, L5Layer, L6Layer, 
    LayerConfig, MicrocircuitColumnConfig,
    MicrocircuitColumn, generate_laminar_connectivity_mask,
    verify_connectivity_constraints
)

class TestL4Layer:
    def test_init(self):
        config = LayerConfig(
            name="L4",
            input_dim=10,
            hidden_dim=20,
            output_dim=20,
            is_excitatory=True
        )
        layer = L4Layer(config)
        assert layer.name == "L4"
        assert layer.is_excitatory is True
        assert isinstance(layer.linear, nn.Linear)
        assert layer.linear.in_features == 10
        assert layer.linear.out_features == 20

    def test_forward(self):
        config = LayerConfig(
            name="L4",
            input_dim=10,
            hidden_dim=20,
            output_dim=20
        )
        layer = L4Layer(config)
        x = torch.randn(2, 10)
        out = layer(x)
        assert out.shape == (2, 20)

class TestL23Layer:
    def test_init(self):
        config = LayerConfig(
            name="L23",
            input_dim=20,
            hidden_dim=30,
            output_dim=30,
            is_excitatory=True
        )
        layer = L23Layer(config)
        assert layer.name == "L23"
        assert layer.is_excitatory is True

    def test_forward(self):
        config = LayerConfig(
            name="L23",
            input_dim=20,
            hidden_dim=30,
            output_dim=30
        )
        layer = L23Layer(config)
        x = torch.randn(4, 20)
        out = layer(x)
        assert out.shape == (4, 30)

class TestL5Layer:
    def test_init(self):
        config = LayerConfig(
            name="L5",
            input_dim=30,
            hidden_dim=40,
            output_dim=40,
            is_excitatory=True
        )
        layer = L5Layer(config)
        assert layer.name == "L5"

    def test_forward(self):
        config = LayerConfig(
            name="L5",
            input_dim=30,
            hidden_dim=40,
            output_dim=40
        )
        layer = L5Layer(config)
        x = torch.randn(2, 30)
        out = layer(x)
        assert out.shape == (2, 40)

class TestL6Layer:
    def test_init(self):
        config = LayerConfig(
            name="L6",
            input_dim=40,
            hidden_dim=50,
            output_dim=50,
            is_excitatory=True
        )
        layer = L6Layer(config)
        assert layer.name == "L6"

    def test_forward(self):
        config = LayerConfig(
            name="L6",
            input_dim=40,
            hidden_dim=50,
            output_dim=50
        )
        layer = L6Layer(config)
        x = torch.randn(3, 40)
        out = layer(x)
        assert out.shape == (3, 50)

class TestLayerConfigs:
    def test_microcircuit_column_config(self):
        config = MicrocircuitColumnConfig(
            input_dim=10,
            hidden_dim=32,
            output_dim=10,
            ei_ratio=4.0
        )
        assert config.input_dim == 10
        assert config.hidden_dim == 32
        assert config.ei_ratio == 4.0

    def test_generate_connectivity_mask(self):
        config = MicrocircuitColumnConfig(
            input_dim=10,
            hidden_dim=32,
            output_dim=10
        )
        masks = generate_laminar_connectivity_mask(config)
        
        # Check expected keys exist
        expected_keys = ["L4_L23", "L4_L5", "L23_L5", "L23_L6", "L5_L6", "L6_L4"]
        for key in expected_keys:
            assert key in masks, f"Missing mask key: {key}"
            assert isinstance(masks[key], torch.Tensor)
            assert masks[key].dtype == torch.bool

    def test_verify_connectivity_constraints(self):
        config = MicrocircuitColumnConfig(
            input_dim=10,
            hidden_dim=32,
            output_dim=10
        )
        masks = generate_laminar_connectivity_mask(config)
        assert verify_connectivity_constraints(masks, config) is True

class TestMicrocircuitColumnIntegration:
    def test_column_initialization(self):
        config = MicrocircuitColumnConfig(
            input_dim=10,
            hidden_dim=32,
            output_dim=10
        )
        column = MicrocircuitColumn(config)
        
        # Check layers exist
        assert hasattr(column, 'l4')
        assert hasattr(column, 'l23')
        assert hasattr(column, 'l5')
        assert hasattr(column, 'l6')
        
        # Check connectivity masks
        assert hasattr(column, 'connectivity_masks')
        assert len(column.connectivity_masks) > 0

    def test_column_forward(self):
        config = MicrocircuitColumnConfig(
            input_dim=10,
            hidden_dim=32,
            output_dim=10
        )
        column = MicrocircuitColumn(config)
        x = torch.randn(2, 10)
        
        # Should not raise
        out = column(x)
        assert out.shape[0] == 2
        # Output dimension depends on implementation, but should be consistent
        # In the current impl, it returns L5 output which is hidden_dim
        assert out.shape[1] == 32