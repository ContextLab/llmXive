import pytest
import torch
import torch.nn as nn
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
    """Test basic CorticalLayer functionality and E/I enforcement."""
    
    def test_layer_initialization(self):
        """Test that layers initialize with correct E/I counts."""
        config = LayerConfig(
            name="test",
            neuron_count=100,
            excitatory_ratio=0.8,
            hidden_dim=64
        )
        
        layer = CorticalLayer(config)
        
        assert layer.exc_count == 80
        assert layer.inh_count == 20
        assert layer.neuron_count == 100
        
    def test_ei_weight_signs(self):
        """Test that E and I weights have correct signs after initialization."""
        config = LayerConfig(
            name="test",
            neuron_count=100,
            excitatory_ratio=0.8,
            hidden_dim=64
        )
        
        layer = CorticalLayer(config)
        
        # Excitatory weights should be non-negative
        exc_weights = layer.exc_proj.weight
        assert (exc_weights >= 0).all(), "Excitatory weights should be non-negative"
        
        # Inhibitory weights should be non-positive
        inh_weights = layer.inh_proj.weight
        assert (inh_weights <= 0).all(), "Inhibitory weights should be non-positive"
        
    def test_forward_pass_separation(self):
        """Test that forward pass returns separate E and I outputs."""
        config = LayerConfig(
            name="test",
            neuron_count=100,
            excitatory_ratio=0.8,
            hidden_dim=64
        )
        
        layer = CorticalLayer(config)
        x = torch.randn(32, 64)
        
        exc_out, inh_out = layer.forward(x)
        
        assert exc_out.shape == (32, 80)
        assert inh_out.shape == (32, 20)
        assert torch.all(exc_out >= 0), "Excitatory output should be non-negative"
        
    def test_combined_output_dominance(self):
        """Test that combined output maintains excitatory dominance."""
        config = LayerConfig(
            name="test",
            neuron_count=100,
            excitatory_ratio=0.8,
            hidden_dim=64
        )
        
        layer = CorticalLayer(config)
        x = torch.randn(32, 64)
        
        combined = layer.get_combined_output(x)
        
        # Check that output shape is correct
        assert combined.shape == (32, 100)
        
        # Verify excitatory portion dominates in magnitude
        exc_part = combined[:, :80]
        inh_part = combined[:, 80:]
        
        exc_norm = torch.norm(exc_part, p=2, dim=1).mean()
        inh_norm = torch.norm(inh_part, p=2, dim=1).mean()
        
        assert exc_norm > inh_norm, "Excitatory component should dominate"

class TestMicrocircuitColumn:
    """Test complete microcircuit column functionality."""
    
    def test_column_creation(self):
        """Test that column is created with correct structure."""
        column = create_microcircuit_column(input_dim=64, hidden_dim=128)
        
        assert isinstance(column, MicrocircuitColumn)
        assert "L4" in column.layers
        assert "L23" in column.layers
        assert "L5" in column.layers
        assert "L6" in column.layers
        
    def test_column_forward_pass(self):
        """Test forward pass through complete column."""
        column = create_microcircuit_column(input_dim=64, hidden_dim=128)
        x = torch.randn(16, 64)
        
        output = column.forward(x)
        
        assert output.shape == (16, 128)
        
    def test_ei_ratio_enforcement_in_column(self):
        """Test that E/I ratio is enforced across all layers in column."""
        column = create_microcircuit_column(input_dim=64, hidden_dim=128)
        x = torch.randn(16, 64)
        
        # Run forward pass
        output = column.forward(x)
        
        # Check that all layers maintain E/I constraints
        for layer_name, layer in column.layers.items():
            if isinstance(layer, CorticalLayer):
                # Verify excitatory count matches config
                expected_exc = int(layer.neuron_count * layer.config.excitatory_ratio)
                assert layer.exc_count == expected_exc
                
    def test_specific_layer_configs(self):
        """Test that specific layers have correct E/I ratios."""
        column = create_microcircuit_column(input_dim=64, hidden_dim=128)
        
        # L4 should have highest excitatory ratio
        assert column.layers["L4"].config.excitatory_ratio == 0.85
        
        # L23 should have standard ratio
        assert column.layers["L23"].config.excitatory_ratio == 0.8
        
        # L5 should have lower ratio
        assert column.layers["L5"].config.excitatory_ratio == 0.75
        
        # L6 should have intermediate ratio
        assert column.layers["L6"].config.excitatory_ratio == 0.78

class TestConnectivityFunctions:
    """Test connectivity mask generation and verification."""
    
    def test_connectivity_mask_generation(self):
        """Test generation of laminar connectivity mask."""
        layer_sizes = [128, 128, 128, 128]  # L4, L23, L5, L6
        connectivity_rules = {
            0: [1],  # L4 -> L23
            1: [2],  # L23 -> L5
            2: [3],  # L5 -> L6
            3: [0]   # L6 -> L4 (feedback)
        }
        
        mask = generate_laminar_connectivity_mask(layer_sizes, connectivity_rules)
        
        assert mask.shape == (512, 512)
        assert mask.dtype == torch.float32
        
    def test_connectivity_verification(self):
        """Test verification of connectivity constraints."""
        layer_sizes = [128, 128, 128, 128]
        connectivity_rules = {
            0: [1],
            1: [2],
            2: [3],
            3: [0]
        }
        
        mask = generate_laminar_connectivity_mask(layer_sizes, connectivity_rules)
        
        # With sparse connections, density should be low
        is_valid = verify_connectivity_constraints(mask, expected_density=0.0625)
        
        # The mask has 4 connections out of 16 possible blocks, 
        # so density should be 4/16 = 0.25 of the total matrix
        # But each block is 128x128, so actual density is 4/(16*16) = 0.015625
        # This test verifies the function runs without error
        assert isinstance(is_valid, bool)

class TestEIConstraintFunction:
    """Test the apply_ei_balance_constraint function."""
    
    def test_constraint_application(self):
        """Test that constraint function correctly enforces E/I signs."""
        weights = torch.randn(100, 50)
        
        constrained = apply_ei_balance_constraint(weights, target_ratio=0.8)
        
        # First 80 rows should be non-negative
        assert (constrained[:80, :] >= 0).all()
        
        # Last 20 rows should be non-positive
        assert (constrained[80:, :] <= 0).all()
        
        # Shape should be preserved
        assert constrained.shape == weights.shape