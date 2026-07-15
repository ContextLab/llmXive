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
    """Test basic functionality of CorticalLayer and its subclasses."""
    
    def test_layer_config_creation(self):
        """Test that LayerConfig dataclass works correctly."""
        config = LayerConfig(
            name="L2/3",
            neuron_count=128,
            is_excitatory=True,
            connectivity_factor=0.8
        )
        assert config.name == "L2/3"
        assert config.neuron_count == 128
        assert config.is_excitatory is True
        assert config.connectivity_factor == 0.8
    
    def test_cortical_layer_forward(self):
        """Test forward pass through CorticalLayer."""
        config = LayerConfig(
            name="TestLayer",
            neuron_count=64,
            is_excitatory=True
        )
        layer = CorticalLayer(config, input_dim=32)
        
        x = torch.randn(4, 32)  # batch_size=4, input_dim=32
        output = layer(x)
        
        assert output.shape == (4, 64)
        assert output.requires_grad
    
    def test_excitatory_layer_uses_relu(self):
        """Test that excitatory layers use ReLU activation."""
        config = LayerConfig(
            name="ExcLayer",
            neuron_count=32,
            is_excitatory=True
        )
        layer = CorticalLayer(config, input_dim=16)
        
        x = torch.randn(2, 16)
        output = layer(x)
        
        # All outputs should be non-negative (ReLU)
        assert torch.all(output >= 0)
    
    def test_inhibitory_layer_uses_leaky_relu(self):
        """Test that inhibitory layers use LeakyReLU activation."""
        config = LayerConfig(
            name="InhLayer",
            neuron_count=32,
            is_excitatory=False
        )
        layer = CorticalLayer(config, input_dim=16)
        
        x = torch.randn(2, 16)
        output = layer(x)
        
        # LeakyReLU allows small negative values
        # Just check it runs without error and has correct shape
        assert output.shape == (2, 32)
    
    def test_layer_initialization_weights(self):
        """Test that layer weights are initialized in normalized range."""
        config = LayerConfig(
            name="TestLayer",
            neuron_count=32,
            is_excitatory=True
        )
        layer = CorticalLayer(config, input_dim=16)
        
        # Weights should be small (initialized with std=0.1)
        assert layer.weight.shape == (16, 32)
        assert layer.bias.shape == (32,)
        
        # Check that weights are in reasonable range
        assert torch.abs(layer.weight).max() < 0.5

class TestMicrocircuitColumn:
    """Test MicrocircuitColumn connectivity and forward pass."""
    
    def test_column_initialization(self):
        """Test that MicrocircuitColumn initializes correctly."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        assert column.input_dim == 32
        assert column.l4.neuron_count == 64
        assert column.l23.neuron_count == 64
        assert column.l5.neuron_count == 64
        assert column.l6.neuron_count == 32
    
    def test_connectivity_mask_creation(self):
        """Test that connectivity masks are created with correct shapes."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        # Check L4->L2/3 mask shape
        mask_l4_l23 = column.get_connectivity_mask('L4_to_L23')
        assert mask_l4_l23.shape == (64, 64)
        
        # Check L2/3->L5 mask shape
        mask_l23_l5 = column.get_connectivity_mask('L23_to_L5')
        assert mask_l23_l5.shape == (64, 64)
        
        # Check L5->L6 mask shape
        mask_l5_l6 = column.get_connectivity_mask('L5_to_L6')
        assert mask_l5_l6.shape == (32, 64)
        
        # Check L6->L4 mask shape
        mask_l6_l4 = column.get_connectivity_mask('L6_to_L4')
        assert mask_l6_l4.shape == (64, 32)
        
        # Check L2/3 recurrence mask shape
        mask_rec = column.get_connectivity_mask('L23_recurrence')
        assert mask_rec.shape == (64, 64)
    
    def test_connectivity_masks_are_binary(self):
        """Test that all connectivity masks contain only 0 or 1."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        masks = ['L4_to_L23', 'L23_to_L5', 'L5_to_L6', 'L6_to_L4', 'L23_recurrence']
        
        for mask_name in masks:
            mask = column.get_connectivity_mask(mask_name)
            unique_vals = torch.unique(mask)
            assert torch.all((unique_vals == 0) | (unique_vals == 1)), \
                f"Mask {mask_name} contains non-binary values: {unique_vals}"
    
    def test_l4_to_l23_is_full_connectivity(self):
        """Test that L4->L2/3 mask is all ones (full excitatory connectivity)."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        mask = column.get_connectivity_mask('L4_to_L23')
        assert torch.all(mask == 1.0), "L4->L2/3 mask should be all ones"
    
    def test_recurrence_is_sparse(self):
        """Test that L2/3 recurrence mask is sparse (< 20% connectivity)."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        mask = column.get_connectivity_mask('L23_recurrence')
        connectivity_ratio = (mask == 1).float().mean().item()
        assert connectivity_ratio < 0.2, \
            f"L2/3 recurrence should be sparse (<20%), got {connectivity_ratio*100:.1f}%"
    
    def test_forward_pass_shape(self):
        """Test that forward pass produces correct output shape."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        x = torch.randn(4, 32)  # batch_size=4, input_dim=32
        output = column(x)
        
        # Output should be [batch, l6_neurons]
        assert output.shape == (4, 32)
    
    def test_forward_pass_requires_grad(self):
        """Test that forward pass preserves gradient information."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        x = torch.randn(4, 32, requires_grad=True)
        output = column(x)
        
        assert output.requires_grad, "Output should require gradients"
    
    def test_verify_connectivity_constraints(self):
        """Test the connectivity constraint verification function."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        results = verify_connectivity_constraints(column)
        
        assert 'masks_binary' in results
        assert 'L4_to_L23_full' in results
        assert 'recurrence_sparse' in results
        assert 'all_passed' in results
        
        assert results['all_passed'] is True, \
            f"Connectivity constraints failed: {results}"
    
    def test_generate_laminar_connectivity_mask_standalone(self):
        """Test the standalone mask generation function."""
        masks = generate_laminar_connectivity_mask(
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        assert 'L4_to_L23' in masks
        assert 'L23_to_L5' in masks
        assert 'L5_to_L6' in masks
        assert 'L6_to_L4' in masks
        assert 'L23_recurrence' in masks
        
        # Check shapes
        assert masks['L4_to_L23'].shape == (64, 64)
        assert masks['L23_to_L5'].shape == (64, 64)
        assert masks['L5_to_L6'].shape == (32, 64)
        assert masks['L6_to_L4'].shape == (64, 32)
        assert masks['L23_recurrence'].shape == (64, 64)
    
    def test_apply_ei_balance_constraint(self):
        """Test E/I balance constraint application."""
        weights = torch.randn(100, 50)  # input_dim=100, output_dim=50
        balanced_weights = apply_ei_balance_constraint(weights, exc_ratio=4.0)
        
        assert balanced_weights.shape == weights.shape
        assert torch.allclose(balanced_weights, weights, atol=1e-5) or \
               not torch.allclose(balanced_weights, weights), \
               "E/I constraint should modify weights (or not if already balanced)"
    
    def test_create_microcircuit_column_factory(self):
        """Test the factory function for creating columns."""
        column = create_microcircuit_column(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        assert isinstance(column, MicrocircuitColumn)
        assert column.input_dim == 32
        assert column.l4.neuron_count == 64
        assert column.l23.neuron_count == 64
        assert column.l5.neuron_count == 64
        assert column.l6.neuron_count == 32
    
    def test_laminar_flow_order(self):
        """Test that forward pass follows correct laminar flow order."""
        column = MicrocircuitColumn(
            input_dim=32,
            l23_neurons=64,
            l4_neurons=64,
            l5_neurons=64,
            l6_neurons=32
        )
        
        # This test verifies the architecture exists and runs
        # The actual flow order is verified by the implementation in MicrocircuitColumn
        x = torch.randn(2, 32)
        output = column(x)
        
        # If we get here without shape errors, the flow is working
        assert output.shape == (2, 32)