"""
Unit tests for Microcircuit layers and column structure.
"""
import pytest
import torch
import torch.nn as nn
import json
import os
import tempfile

from src.models.microcircuit import (
    L23Layer, L4Layer, L5Layer, L6Layer,
    MicrocircuitColumn, generate_laminar_connectivity_mask,
    verify_connectivity_constraints, LayerConfig
)


class DummyModel(nn.Module):
    """Simple dummy model for testing."""
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 10)

    def forward(self, x):
        return self.fc(x)


class TestLayerDefinitions:
    """Tests for individual layer classes (T007a)."""

    def test_l4_layer_creation(self):
        """Verify L4 layer instantiation and forward pass."""
        layer = L4Layer(input_dim=64, output_dim=128)
        x = torch.randn(2, 64)
        out = layer(x)
        assert out.shape == (2, 128), f"Expected (2, 128), got {out.shape}"

    def test_l23_layer_creation(self):
        """Verify L2/3 layer instantiation and forward pass."""
        layer = L23Layer(input_dim=128, output_dim=128)
        x = torch.randn(2, 128)
        out = layer(x)
        assert out.shape == (2, 128)

    def test_l5_layer_creation(self):
        """Verify L5 layer instantiation and forward pass."""
        layer = L5Layer(input_dim=128, output_dim=128)
        x = torch.randn(2, 128)
        out = layer(x)
        assert out.shape == (2, 128)

    def test_l6_layer_creation(self):
        """Verify L6 layer instantiation and forward pass."""
        layer = L6Layer(input_dim=128, output_dim=128)
        x = torch.randn(2, 128)
        out = layer(x)
        assert out.shape == (2, 128)

    def test_layer_weight_initialization(self):
        """Verify weights are initialized within normalized range."""
        layer = L4Layer(input_dim=64, output_dim=64)
        weights = layer.linear.weight.data
        assert weights.min() >= -1.0, "Weights below lower bound"
        assert weights.max() <= 1.0, "Weights above upper bound"


class TestMicrocircuitColumn:
    """Tests for the full column integration."""

    def test_column_forward_pass(self):
        """Verify the full column forward pass works."""
        col = MicrocircuitColumn(input_dim=64, hidden_dim=128)
        x = torch.randn(4, 64)
        out = col(x)
        assert out.shape == (4, 128), f"Expected (4, 128), got {out.shape}"

    def test_connectivity_mask_generation(self):
        """Verify the laminar connectivity mask matches topology."""
        dims = [128, 128, 128, 128]
        mask = generate_laminar_connectivity_mask(dims)
        assert mask.shape == (4, 4)
        assert verify_connectivity_constraints(mask), "Connectivity mask does not match expected topology"

    def test_column_parameter_count(self):
        """Verify the column has parameters."""
        col = MicrocircuitColumn(input_dim=64, hidden_dim=128)
        param_count = sum(p.numel() for p in col.parameters())
        assert param_count > 0, "Column has no parameters"


def test_epoch_scaling():
    """
    Placeholder test for epoch-level scaling logic (T008c dependency).
    This test ensures the structure exists for T008c to hook into.
    """
    col = MicrocircuitColumn(input_dim=64, hidden_dim=128)
    x = torch.randn(2, 64)
    y = col(x)
    assert y is not None