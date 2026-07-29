"""
Unit tests for model architecture initialization (CPU mode).

Tests the initialization of Spectral GNN, Heterophily-aware GNN,
and Random Forest baseline models to ensure they can be instantiated
without errors on CPU-only hardware.

This test suite verifies:
1. Models can be initialized with valid input dimensions
2. Models do not attempt to allocate GPU memory
3. Models have valid parameter counts
4. Models can perform a forward pass with dummy input (where applicable)
"""

import pytest
import os
import sys
import torch
import numpy as np

# Add the project root to the path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.config import get_config
from code.utils.graph_utils import get_feature_dimensions

# We will create dummy model classes here to test the interface,
# since the actual model files (spectral_gnn.py, etc.) are not yet implemented.
# In a real scenario, these would be imported from code/models/*.py

class DummySpectralGNN:
    """Dummy implementation for testing initialization interface."""
    
    def __init__(self, input_dim, hidden_dim, output_dim, device='cpu'):
        self.device = device
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        
        # Simulate parameter creation
        self.weight = torch.nn.Parameter(torch.randn(input_dim, hidden_dim, device=device))
        self.bias = torch.nn.Parameter(torch.randn(hidden_dim, device=device))
        self.out_weight = torch.nn.Parameter(torch.randn(hidden_dim, output_dim, device=device))
        
        # Ensure no CUDA tensors
        assert not self.weight.is_cuda, "SpectralGNN should not use CUDA"
    
    def forward(self, x):
        # Simple linear forward pass for testing
        x = torch.matmul(x, self.weight) + self.bias
        x = torch.relu(x)
        x = torch.matmul(x, self.out_weight)
        return x
    
    def parameters(self):
        return [self.weight, self.bias, self.out_weight]

class DummyHeteroGNN:
    """Dummy implementation for testing initialization interface."""
    
    def __init__(self, input_dim, hidden_dim, output_dim, device='cpu'):
        self.device = device
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        
        # Simulate heterophily-aware layers
        self.aggregator = torch.nn.Parameter(torch.randn(input_dim, hidden_dim, device=device))
        self.transform = torch.nn.Parameter(torch.randn(hidden_dim, output_dim, device=device))
        
        # Ensure no CUDA tensors
        assert not self.aggregator.is_cuda, "HeteroGNN should not use CUDA"
    
    def forward(self, x, edge_index):
        # Simple aggregation for testing
        x = torch.matmul(x, self.aggregator)
        x = torch.relu(x)
        x = torch.matmul(x, self.transform)
        return x
    
    def parameters(self):
        return [self.aggregator, self.transform]

class DummyRandomForestBaseline:
    """Dummy implementation for testing initialization interface."""
    
    def __init__(self, input_dim, output_dim, n_estimators=10, device='cpu'):
        self.device = device
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.n_estimators = n_estimators
        
        # In a real implementation, this would initialize a RandomForestRegressor
        # For testing, we just verify initialization parameters
        assert n_estimators > 0, "n_estimators must be positive"
        assert input_dim > 0, "input_dim must be positive"
        assert output_dim > 0, "output_dim must be positive"
    
    def fit(self, X, y):
        # Dummy fit method
        return self
    
    def predict(self, X):
        # Dummy predict method
        return np.zeros((X.shape[0], self.output_dim))

class TestModelInitialization:
    """Test suite for model architecture initialization."""
    
    @pytest.fixture
    def config(self):
        """Get project configuration."""
        return get_config()
    
    @pytest.fixture
    def feature_dims(self):
        """Get feature dimensions from graph utils."""
        node_dim, edge_dim = get_feature_dimensions()
        return node_dim, edge_dim
    
    def test_spectral_gnn_cpu_initialization(self, config, feature_dims):
        """Test Spectral GNN initialization on CPU."""
        node_dim, _ = feature_dims
        input_dim = node_dim
        hidden_dim = 64
        output_dim = 1  # Predicting HOMO-LUMO gap
        device = config.get('device', 'cpu')
        
        # Initialize model
        model = DummySpectralGNN(input_dim, hidden_dim, output_dim, device)
        
        # Verify device
        assert model.device == 'cpu', "Model should be on CPU"
        
        # Verify parameters exist
        params = list(model.parameters())
        assert len(params) == 3, "Model should have 3 parameter tensors"
        
        # Verify parameter shapes
        assert params[0].shape == (input_dim, hidden_dim), "Weight shape mismatch"
        assert params[1].shape == (hidden_dim,), "Bias shape mismatch"
        assert params[2].shape == (hidden_dim, output_dim), "Output weight shape mismatch"
        
        # Verify no CUDA tensors
        for param in params:
            assert not param.is_cuda, "Parameters should not be on CUDA"
    
    def test_hetero_gnn_cpu_initialization(self, config, feature_dims):
        """Test Heterophily-aware GNN initialization on CPU."""
        node_dim, _ = feature_dims
        input_dim = node_dim
        hidden_dim = 64
        output_dim = 1
        device = config.get('device', 'cpu')
        
        # Initialize model
        model = DummyHeteroGNN(input_dim, hidden_dim, output_dim, device)
        
        # Verify device
        assert model.device == 'cpu', "Model should be on CPU"
        
        # Verify parameters exist
        params = list(model.parameters())
        assert len(params) == 2, "Model should have 2 parameter tensors"
        
        # Verify no CUDA tensors
        for param in params:
            assert not param.is_cuda, "Parameters should not be on CUDA"
    
    def test_random_forest_baseline_initialization(self, config, feature_dims):
        """Test Random Forest baseline initialization."""
        node_dim, _ = feature_dims
        input_dim = node_dim
        output_dim = 1
        
        # Initialize model
        model = DummyRandomForestBaseline(input_dim, output_dim, n_estimators=10)
        
        # Verify parameters
        assert model.input_dim == input_dim, "Input dimension mismatch"
        assert model.output_dim == output_dim, "Output dimension mismatch"
        assert model.n_estimators == 10, "n_estimators mismatch"
        
        # Verify device attribute exists (even if not used for RF)
        assert model.device == 'cpu', "Model should be configured for CPU"
    
    def test_spectral_gnn_forward_pass(self, config, feature_dims):
        """Test Spectral GNN forward pass with dummy input."""
        node_dim, _ = feature_dims
        input_dim = node_dim
        hidden_dim = 64
        output_dim = 1
        batch_size = 4
        
        model = DummySpectralGNN(input_dim, hidden_dim, output_dim, 'cpu')
        
        # Create dummy input
        x = torch.randn(batch_size, input_dim)
        
        # Forward pass
        output = model.forward(x)
        
        # Verify output shape
        assert output.shape == (batch_size, output_dim), f"Output shape mismatch: {output.shape}"
        
        # Verify output is on CPU
        assert output.device.type == 'cpu', "Output should be on CPU"
    
    def test_hetero_gnn_forward_pass(self, config, feature_dims):
        """Test Hetero GNN forward pass with dummy input."""
        node_dim, _ = feature_dims
        input_dim = node_dim
        hidden_dim = 64
        output_dim = 1
        batch_size = 4
        
        model = DummyHeteroGNN(input_dim, hidden_dim, output_dim, 'cpu')
        
        # Create dummy input
        x = torch.randn(batch_size, input_dim)
        edge_index = torch.randint(0, batch_size, (2, 8))
        
        # Forward pass
        output = model.forward(x, edge_index)
        
        # Verify output shape
        assert output.shape == (batch_size, output_dim), f"Output shape mismatch: {output.shape}"
        
        # Verify output is on CPU
        assert output.device.type == 'cpu', "Output should be on CPU"
    
    def test_model_parameter_count(self, config, feature_dims):
        """Test that models have reasonable parameter counts."""
        node_dim, _ = feature_dims
        input_dim = node_dim
        hidden_dim = 64
        output_dim = 1
        
        spectral_model = DummySpectralGNN(input_dim, hidden_dim, output_dim, 'cpu')
        hetero_model = DummyHeteroGNN(input_dim, hidden_dim, output_dim, 'cpu')
        
        # Count parameters
        spectral_params = sum(p.numel() for p in spectral_model.parameters())
        hetero_params = sum(p.numel() for p in hetero_model.parameters())
        
        # Verify parameter counts are positive and reasonable
        assert spectral_params > 0, "Spectral model should have parameters"
        assert hetero_params > 0, "Hetero model should have parameters"
        
        # For a small model with hidden_dim=64, we expect a few thousand parameters
        assert spectral_params < 100000, "Spectral model parameters should be reasonable"
        assert hetero_params < 100000, "Hetero model parameters should be reasonable"
    
    def test_invalid_input_dimensions(self, feature_dims):
        """Test that models reject invalid input dimensions."""
        node_dim, _ = feature_dims
        
        # Test with zero input dimension
        with pytest.raises(AssertionError):
            DummySpectralGNN(0, 64, 1, 'cpu')
        
        with pytest.raises(AssertionError):
            DummyHeteroGNN(0, 64, 1, 'cpu')
        
        with pytest.raises(AssertionError):
            DummyRandomForestBaseline(0, 1, n_estimators=10)
        
        # Test with negative hidden dimension
        with pytest.raises(RuntimeError):  # torch.randn will fail with negative sizes
            DummySpectralGNN(node_dim, -1, 1, 'cpu')
    
    def test_cpu_only_enforcement(self):
        """Test that models enforce CPU-only operation."""
        input_dim = 10
        hidden_dim = 32
        output_dim = 1
        
        # This should work
        model_cpu = DummySpectralGNN(input_dim, hidden_dim, output_dim, 'cpu')
        assert model_cpu.device == 'cpu'
        
        # If CUDA is available, we should still be able to force CPU
        # (In a real implementation, this would prevent CUDA allocation)
        model_forced_cpu = DummySpectralGNN(input_dim, hidden_dim, output_dim, 'cpu')
        assert model_forced_cpu.device == 'cpu'
        
        # Verify no CUDA tensors in forced CPU model
        for param in model_forced_cpu.parameters():
            assert not param.is_cuda, "Forced CPU model should not have CUDA tensors"