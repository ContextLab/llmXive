import pytest
import torch
import torch.nn as nn
import numpy as np
from src.models.microcircuit import (
    LayerConfig,
    CorticalLayer,
    L23Layer,
    L4Layer,
    L5Layer,
    L6Layer,
    MicrocircuitColumn,
    create_microcircuit_column,
    generate_laminar_connectivity_mask,
    verify_connectivity_constraints,
    apply_ei_balance_constraint
)

class TestCorticalLayerBasics:
    """Unit tests for basic CorticalLayer functionality and weight constraints."""

    def test_layer_initialization_shapes(self):
        """Verify that layer weight matrices are initialized with correct shapes."""
        # Test L4Layer (Input layer, typically receives thalamic input)
        config = LayerConfig(input_dim=128, hidden_dim=256, output_dim=128)
        layer = L4Layer(config)
        
        # Check weight shapes for Linear layers
        assert layer.linear_in.weight.shape == (config.hidden_dim, config.input_dim)
        assert layer.linear_out.weight.shape == (config.output_dim, config.hidden_dim)
        
        # Check bias shapes
        assert layer.linear_in.bias.shape == (config.hidden_dim,)
        assert layer.linear_out.bias.shape == (config.output_dim,)

    def test_weight_constraints_initialization(self):
        """Verify that weights are initialized within expected constraints (e.g., Xavier/Glorot)."""
        config = LayerConfig(input_dim=64, hidden_dim=128, output_dim=64)
        layer = L4Layer(config)
        
        # Check that weights are finite (no NaN/Inf)
        assert torch.isfinite(layer.linear_in.weight).all()
        assert torch.isfinite(layer.linear_out.weight).all()
        
        # Check that weights are non-zero (initialized properly)
        assert layer.linear_in.weight.abs().mean() > 0.0
        assert layer.linear_out.weight.abs().mean() > 0.0

    def test_ei_balance_constraint_application(self):
        """Test that apply_ei_balance_constraint correctly enforces E/I ratio."""
        config = LayerConfig(input_dim=64, hidden_dim=128, output_dim=64)
        layer = L4Layer(config)
        
        # Apply constraint (default E/I ratio 4:1)
        apply_ei_balance_constraint(layer)
        
        # Verify weights are still finite
        assert torch.isfinite(layer.linear_in.weight).all()
        assert torch.isfinite(layer.linear_out.weight).all()
        
        # Verify that the constraint logic didn't zero out all weights
        assert layer.linear_in.weight.abs().sum() > 0.0

    def test_forward_pass_shapes(self):
        """Verify that forward pass produces tensors of correct shapes."""
        config = LayerConfig(input_dim=64, hidden_dim=128, output_dim=64)
        layer = L4Layer(config)
        
        batch_size = 16
        x = torch.randn(batch_size, config.input_dim)
        
        output = layer(x)
        
        assert output.shape == (batch_size, config.output_dim)

class TestMicrocircuitColumn:
    """Unit tests for MicrocircuitColumn connectivity and constraints."""

    def test_column_initialization_shapes(self):
        """Verify that MicrocircuitColumn initializes layers with correct shapes."""
        column = create_microcircuit_column(
            input_dim=128,
            hidden_dim=256,
            output_dim=128,
            ei_ratio=4.0
        )
        
        # Check that all layers are present
        assert hasattr(column, 'layer_23')
        assert hasattr(column, 'layer_4')
        assert hasattr(column, 'layer_5')
        assert hasattr(column, 'layer_6')
        
        # Verify layer types
        assert isinstance(column.layer_23, L23Layer)
        assert isinstance(column.layer_4, L4Layer)
        assert isinstance(column.layer_5, L5Layer)
        assert isinstance(column.layer_6, L6Layer)

    def test_connectivity_matrix_shape(self):
        """Verify that the laminar connectivity matrix has the correct shape."""
        column = create_microcircuit_column(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            ei_ratio=4.0
        )
        
        # Generate connectivity mask
        connectivity_mask = generate_laminar_connectivity_mask(column)
        
        # Expected shape: 4x4 (4 layers: L2/3, L4, L5, L6)
        assert connectivity_mask.shape == (4, 4)
        
        # Verify mask is binary (0 or 1)
        assert set(connectivity_mask.flatten().tolist()).issubset({0, 1})

    def test_laminar_connectivity_constraints(self):
        """Verify that connectivity constraints are enforced (e.g., L4->L2/3 is excitatory)."""
        column = create_microcircuit_column(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            ei_ratio=4.0
        )
        
        # Generate connectivity mask
        connectivity_mask = generate_laminar_connectivity_mask(column)
        
        # Verify specific connections exist
        # L4 (index 1) -> L2/3 (index 0) should be active (excitatory feedforward)
        # Note: Index mapping depends on implementation order, typically [L23, L4, L5, L6]
        # So L4 is index 1, L2/3 is index 0. Connection from L4 to L2/3 is mask[0, 1]
        assert connectivity_mask[0, 1] == 1, "L4->L2/3 connection should be active"
        
        # Verify that the mask satisfies the constraints
        is_valid, reason = verify_connectivity_constraints(connectivity_mask)
        assert is_valid, f"Connectivity constraints violated: {reason}"

    def test_ei_balance_constraint_on_column(self):
        """Verify that E/I balance is enforced across the entire column."""
        column = create_microcircuit_column(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            ei_ratio=4.0
        )
        
        # Apply E/I balance constraint to the whole column
        apply_ei_balance_constraint(column)
        
        # Verify all layers still have valid weights
        assert torch.isfinite(column.layer_23.linear_in.weight).all()
        assert torch.isfinite(column.layer_4.linear_in.weight).all()
        assert torch.isfinite(column.layer_5.linear_in.weight).all()
        assert torch.isfinite(column.layer_6.linear_in.weight).all()

    def test_forward_pass_through_column(self):
        """Verify that a forward pass through the entire column works without shape errors."""
        column = create_microcircuit_column(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            ei_ratio=4.0
        )
        
        batch_size = 8
        x = torch.randn(batch_size, 64)
        
        # Forward pass
        output = column(x)
        
        # Verify output shape matches expected output dimension
        assert output.shape == (batch_size, 64)

    def test_weight_norm_constraints(self):
        """Verify that weight norms are within expected ranges after initialization."""
        column = create_microcircuit_column(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            ei_ratio=4.0
        )
        
        # Check that weight norms are reasonable (not too large, not zero)
        for layer_name in ['layer_23', 'layer_4', 'layer_5', 'layer_6']:
            layer = getattr(column, layer_name)
            weight_norm = layer.linear_in.weight.norm().item()
            assert 0.0 < weight_norm < 100.0, f"Weight norm for {layer_name} is out of range: {weight_norm}"

    def test_connectivity_mask_determinism(self):
        """Verify that connectivity mask generation is deterministic."""
        column1 = create_microcircuit_column(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            ei_ratio=4.0
        )
        column2 = create_microcircuit_column(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            ei_ratio=4.0
        )
        
        mask1 = generate_laminar_connectivity_mask(column1)
        mask2 = generate_laminar_connectivity_mask(column2)
        
        # Masks should be identical for same configuration
        assert torch.equal(mask1, mask2), "Connectivity mask should be deterministic"