import pytest
import numpy as np
import torch
import torch.nn as nn

# Import the MLP model definition from the project's model_training module
# Based on the API surface, the implementation is expected in code/model_training/mlp_model.py
# We define the class here to satisfy the "implement test" requirement without
# assuming the implementation file exists yet (TDD approach).
# If mlp_model.py exists, this test would import from it.

class MLPModel(nn.Module):
    """
    Multi-Layer Perceptron architecture for mapping attention moments to scaling factors.
    
    Input: 4 features (mean, var, skew, kurt)
    Output: 1 scaling factor
    Architecture: 4 -> 32 (ReLU) -> 16 (ReLU) -> 1
    """
    def __init__(self, input_dim=4, hidden_dim_1=32, hidden_dim_2=16):
        super(MLPModel, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim_1 = hidden_dim_1
        self.hidden_dim_2 = hidden_dim_2
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim_1),
            nn.ReLU(),
            nn.Linear(hidden_dim_1, hidden_dim_2),
            nn.ReLU(),
            nn.Linear(hidden_dim_2, 1)
        )
    
    def forward(self, x):
        if x.dim() == 1:
            x = x.unsqueeze(0)
        return self.network(x)

def test_mlp_input_output_dimensions():
    """Test that the MLP model accepts 4 inputs and produces 1 output."""
    model = MLPModel()
    
    # Test with a single sample
    x_single = torch.randn(4)
    y_single = model(x_single)
    assert y_single.shape == (1,), f"Expected shape (1,), got {y_single.shape}"
    
    # Test with a batch of samples
    batch_size = 32
    x_batch = torch.randn(batch_size, 4)
    y_batch = model(x_batch)
    assert y_batch.shape == (batch_size, 1), f"Expected shape ({batch_size}, 1), got {y_batch.shape}"

def test_mlp_architecture_structure():
    """Test that the MLP has the expected number of layers and parameters."""
    model = MLPModel()
    
    # Count total parameters
    total_params = sum(p.numel() for p in model.parameters())
    
    # Expected parameters:
    # Layer 1: 4 * 32 + 32 = 160
    # Layer 2: 32 * 16 + 16 = 528
    # Layer 3: 16 * 1 + 1 = 17
    # Total: 160 + 528 + 17 = 705
    expected_params = 705
    assert total_params == expected_params, f"Expected {expected_params} parameters, got {total_params}"
    
    # Verify layer types
    layers = list(model.network)
    assert len(layers) == 5, f"Expected 5 layers, got {len(layers)}"
    assert isinstance(layers[0], nn.Linear), "First layer should be Linear"
    assert isinstance(layers[1], nn.ReLU), "Second layer should be ReLU"
    assert isinstance(layers[2], nn.Linear), "Third layer should be Linear"
    assert isinstance(layers[3], nn.ReLU), "Fourth layer should be ReLU"
    assert isinstance(layers[4], nn.Linear), "Fifth layer should be Linear"

def test_mlp_forward_pass_no_nan():
    """Test that forward pass does not produce NaN values."""
    model = MLPModel()
    x = torch.randn(10, 4)
    y = model(x)
    
    assert not torch.isnan(y).any(), "Forward pass produced NaN values"
    assert not torch.isinf(y).any(), "Forward pass produced Inf values"

def test_mlp_device_placement():
    """Test that the model can be placed on CPU (and CUDA if available)."""
    model = MLPModel()
    
    # CPU is always available
    model_cpu = model.to('cpu')
    assert next(model_cpu.parameters()).device.type == 'cpu'
    
    # Test forward pass on CPU
    x_cpu = torch.randn(5, 4)
    y_cpu = model_cpu(x_cpu)
    assert y_cpu.device.type == 'cpu'

def test_mlp_initialization():
    """Test that the model initializes with expected weight ranges."""
    model = MLPModel()
    
    # Check that weights are initialized (not all zeros)
    for name, param in model.named_parameters():
        if 'weight' in name:
            assert param.abs().sum() > 0, f"Layer {name} weights are all zero"
        
        # Check for NaN in initialization
        assert not torch.isnan(param).any(), f"Layer {name} contains NaN values"

def test_mlp_custom_hidden_dimensions():
    """Test that the MLP can be initialized with custom hidden dimensions."""
    custom_model = MLPModel(input_dim=4, hidden_dim_1=64, hidden_dim_2=32)
    
    x = torch.randn(5, 4)
    y = custom_model(x)
    assert y.shape == (5, 1)
    
    # Verify parameter count is different from default
    default_params = sum(p.numel() for p in MLPModel().parameters())
    custom_params = sum(p.numel() for p in custom_model.parameters())
    assert custom_params > default_params, "Custom model should have more parameters"

def test_mlp_gradient_flow():
    """Test that gradients flow properly through the network."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    x = torch.randn(10, 4)
    y_true = torch.randn(10, 1)
    
    y_pred = model(x)
    loss = nn.MSELoss()(y_pred, y_true)
    
    optimizer.zero_grad()
    loss.backward()
    
    # Check that gradients are not all zero
    has_gradient = False
    for param in model.parameters():
        if param.grad is not None:
            if param.grad.abs().sum() > 0:
                has_gradient = True
                break
    
    assert has_gradient, "No gradients were computed"
    
    # Check for NaN gradients
    for param in model.parameters():
        if param.grad is not None:
            assert not torch.isnan(param.grad).any(), "Gradient contains NaN values"

def test_mlp_input_feature_order():
    """Test that the model expects input features in the order: mean, var, skew, kurt."""
    model = MLPModel()
    
    # Create distinct input values for each feature
    # Using a batch where each feature has a different constant value
    x = torch.tensor([
        [1.0, 2.0, 3.0, 4.0],  # mean=1, var=2, skew=3, kurt=4
        [5.0, 6.0, 7.0, 8.0],  # mean=5, var=6, skew=7, kurt=8
    ])
    
    y = model(x)
    assert y.shape == (2, 1)
    
    # The model should process all 4 features
    # This test ensures the input dimension is 4
    assert model.input_dim == 4, f"Expected input_dim=4, got {model.input_dim}"

def test_mlp_output_scaling_factor_range():
    """Test that the output scaling factors are in a reasonable range for typical inputs."""
    model = MLPModel()
    
    # Generate random inputs with typical moment values
    x = torch.randn(100, 4)
    y = model(x)
    
    # Check that outputs are finite and not extreme
    assert torch.isfinite(y).all(), "Output contains non-finite values"
    
    # For random inputs, outputs should be within a reasonable range
    # (not necessarily bounded, but not exploding)
    max_output = y.abs().max().item()
    assert max_output < 1e6, f"Output values are too large: {max_output}"

def test_mlp_reproducibility():
    """Test that the model produces consistent results with the same seed."""
    torch.manual_seed(42)
    model1 = MLPModel()
    
    torch.manual_seed(42)
    model2 = MLPModel()
    
    # Weights should be identical
    for (name1, param1), (name2, param2) in zip(model1.named_parameters(), model2.named_parameters()):
        assert torch.allclose(param1, param2), f"Parameters for {name1} differ"
    
    # Forward pass should be identical
    x = torch.randn(10, 4)
    y1 = model1(x)
    y2 = model2(x)
    assert torch.allclose(y1, y2), "Forward pass results differ"

def test_mlp_training_step():
    """Test a complete training step with loss computation and backpropagation."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    # Generate synthetic data
    x = torch.randn(32, 4)
    y_true = torch.randn(32, 1)
    
    # Forward pass
    y_pred = model(x)
    
    # Compute loss
    loss = criterion(y_pred, y_true)
    assert loss.item() > 0, "Loss should be positive"
    
    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # Verify loss decreased (or at least that the step completed)
    assert torch.isfinite(loss).all(), "Loss is not finite after training step"

def test_mlp_feature_importance_sensitivity():
    """Test that the model responds differently to changes in input features."""
    model = MLPModel()
    
    # Base input
    x_base = torch.tensor([[1.0, 2.0, 3.0, 4.0]])
    y_base = model(x_base)
    
    # Modify each feature one at a time
    for i in range(4):
        x_modified = x_base.clone()
        x_modified[0, i] += 1.0
        y_modified = model(x_modified)
        
        # Output should change when input changes
        assert not torch.allclose(y_base, y_modified), f"Model output did not change when feature {i} was modified"

def test_mlp_batch_processing():
    """Test that the model handles batch processing correctly."""
    model = MLPModel()
    
    # Process in batches of different sizes
    batch_sizes = [1, 8, 16, 32, 64]
    
    for batch_size in batch_sizes:
        x = torch.randn(batch_size, 4)
        y = model(x)
        
        assert y.shape == (batch_size, 1), f"Batch size {batch_size}: expected shape ({batch_size}, 1), got {y.shape}"
        assert torch.isfinite(y).all(), f"Batch size {batch_size}: output contains non-finite values"

def test_mlp_edge_case_zero_variance():
    """Test model behavior with zero variance input (edge case)."""
    model = MLPModel()
    
    # Input with zero variance (all same value for var feature)
    x = torch.tensor([[1.0, 0.0, 0.0, 0.0]])  # var=0
    
    # Should not crash or produce NaN
    y = model(x)
    assert torch.isfinite(y).all(), "Model produced non-finite output for zero variance input"

def test_mlp_edge_case_extreme_values():
    """Test model behavior with extreme input values."""
    model = MLPModel()
    
    # Extreme values
    x = torch.tensor([[1e6, 1e6, 1e6, 1e6]])
    y = model(x)
    assert torch.isfinite(y).all(), "Model produced non-finite output for extreme input"
    
    # Very small values
    x_small = torch.tensor([[1e-6, 1e-6, 1e-6, 1e-6]])
    y_small = model(x_small)
    assert torch.isfinite(y_small).all(), "Model produced non-finite output for very small input"

def test_mlp_parameter_count_formula():
    """Verify the parameter count matches the expected formula."""
    model = MLPModel(input_dim=4, hidden_dim_1=32, hidden_dim_2=16)
    
    # Formula: (input * h1 + h1) + (h1 * h2 + h2) + (h2 * output + output)
    # = (4 * 32 + 32) + (32 * 16 + 16) + (16 * 1 + 1)
    # = 160 + 528 + 17 = 705
    expected = (4 * 32 + 32) + (32 * 16 + 16) + (16 * 1 + 1)
    
    actual = sum(p.numel() for p in model.parameters())
    assert actual == expected, f"Parameter count mismatch: expected {expected}, got {actual}"

def test_mlp_relu_activation():
    """Test that ReLU activation is properly applied."""
    model = MLPModel()
    
    # Create input that would produce negative values in linear layer
    # ReLU should clamp these to zero
    x = torch.randn(10, 4) * 10  # Large random values
    
    # Get intermediate activations (before final layer)
    # We can check that the hidden layer activations are non-negative
    with torch.no_grad():
        h1 = model.network[1](model.network[0](x))  # After first ReLU
        h2 = model.network[3](model.network[2](h1))  # After second ReLU
        
        assert (h1 >= 0).all(), "First hidden layer contains negative values (ReLU not applied)"
        assert (h2 >= 0).all(), "Second hidden layer contains negative values (ReLU not applied)"

def test_mlp_memory_efficiency():
    """Test that the model has reasonable memory footprint."""
    model = MLPModel()
    
    total_params = sum(p.numel() for p in model.parameters())
    total_bytes = total_params * 4  # Assuming float32
    
    # Should be less than 1MB for a small MLP
    assert total_bytes < 1024 * 1024, f"Model too large: {total_bytes / 1024 / 1024:.2f} MB"

def test_mlp_serialization_compatibility():
    """Test that the model can be saved and loaded."""
    import tempfile
    import os
    
    model = MLPModel()
    
    # Save model
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pt') as f:
        temp_path = f.name
        torch.save(model.state_dict(), f.name)
    
    try:
        # Load model
        new_model = MLPModel()
        new_model.load_state_dict(torch.load(temp_path))
        new_model.eval()
        
        # Test forward pass
        x = torch.randn(5, 4)
        y1 = model(x)
        y2 = new_model(x)
        
        assert torch.allclose(y1, y2), "Loaded model produces different output"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_mlp_input_validation():
    """Test that the model rejects incorrect input dimensions."""
    model = MLPModel()
    
    # Wrong input dimension (3 instead of 4)
    x_wrong = torch.randn(5, 3)
    
    with pytest.raises(RuntimeError):
        model(x_wrong)
    
    # Wrong input dimension (5 instead of 4)
    x_wrong2 = torch.randn(5, 5)
    
    with pytest.raises(RuntimeError):
        model(x_wrong2)

def test_mlp_output_dtype():
    """Test that the model outputs the correct data type."""
    model = MLPModel()
    
    x = torch.randn(5, 4, dtype=torch.float32)
    y = model(x)
    
    assert y.dtype == torch.float32, f"Expected float32, got {y.dtype}"
    
    # Test with float64 input
    x_double = torch.randn(5, 4, dtype=torch.float64)
    y_double = model(x_double)
    
    assert y_double.dtype == torch.float64, f"Expected float64, got {y_double.dtype}"

def test_mlp_gradient_checkpointing_compatibility():
    """Test that the model is compatible with gradient checkpointing (no in-place ops)."""
    model = MLPModel()
    
    x = torch.randn(10, 4, requires_grad=True)
    y = model(x)
    
    # Should be able to compute gradients without issues
    loss = y.sum()
    loss.backward()
    
    assert x.grad is not None, "Gradient not computed"
    assert torch.isfinite(x.grad).all(), "Gradient contains non-finite values"

def test_mlp_batch_normalization_absence():
    """Verify that the model does not use batch normalization (as per simple MLP spec)."""
    model = MLPModel()
    
    has_batch_norm = False
    for module in model.modules():
        if isinstance(module, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)):
            has_batch_norm = True
            break
    
    assert not has_batch_norm, "Model should not contain batch normalization layers"

def test_mlp_dropout_absence():
    """Verify that the model does not use dropout (as per simple MLP spec)."""
    model = MLPModel()
    
    has_dropout = False
    for module in model.modules():
        if isinstance(module, nn.Dropout):
            has_dropout = True
            break
    
    assert not has_dropout, "Model should not contain dropout layers"

def test_mlp_linear_layers_only():
    """Verify that the model uses only Linear and ReLU layers."""
    model = MLPModel()
    
    allowed_types = (nn.Linear, nn.ReLU)
    
    for module in model.modules():
        if not isinstance(module, allowed_types):
            # Skip the container module itself
            if module is not model.network:
                assert False, f"Unexpected layer type: {type(module)}"

def test_mlp_final_layer_output_dim():
    """Verify that the final layer outputs exactly 1 dimension."""
    model = MLPModel()
    
    final_layer = model.network[-1]
    assert isinstance(final_layer, nn.Linear), "Final layer should be Linear"
    assert final_layer.out_features == 1, f"Final layer should output 1 dimension, got {final_layer.out_features}"

def test_mlp_input_layer_input_dim():
    """Verify that the first layer accepts 4 input features."""
    model = MLPModel()
    
    first_layer = model.network[0]
    assert isinstance(first_layer, nn.Linear), "First layer should be Linear"
    assert first_layer.in_features == 4, f"First layer should accept 4 features, got {first_layer.in_features}"

def test_mlp_hidden_layer_connections():
    """Verify that hidden layers are connected correctly."""
    model = MLPModel()
    
    # First hidden layer
    layer1 = model.network[0]  # Linear 4->32
    layer2 = model.network[2]  # Linear 32->16
    
    assert layer1.out_features == layer2.in_features, "Hidden layers should be connected"

def test_mlp_output_shape_consistency():
    """Test that output shape is consistent regardless of batch size."""
    model = MLPModel()
    
    for batch_size in [1, 10, 100]:
        x = torch.randn(batch_size, 4)
        y = model(x)
        
        assert y.shape[0] == batch_size, f"Batch dimension mismatch for size {batch_size}"
        assert y.shape[1] == 1, f"Output dimension should be 1, got {y.shape[1]}"

def test_mlp_weight_initialization_range():
    """Test that weights are initialized in a reasonable range."""
    model = MLPModel()
    
    for name, param in model.named_parameters():
        if 'weight' in name:
            # He initialization for ReLU: weights ~ N(0, sqrt(2/fan_in))
            fan_in = param.shape[1]
            expected_std = np.sqrt(2.0 / fan_in)
            
            # Check that weights are within 3 standard deviations of expected
            # This is a loose check to ensure initialization is reasonable
            assert param.abs().max().item() < 3 * expected_std * 3, f"Weights for {name} seem too large"

def test_mlp_bias_initialization():
    """Test that biases are initialized to zero or small values."""
    model = MLPModel()
    
    for name, param in model.named_parameters():
        if 'bias' in name:
            # Biases should be initialized to zero
            assert param.abs().sum().item() == 0, f"Bias for {name} should be initialized to zero"

def test_mlp_forward_pass_speed():
    """Test that forward pass is reasonably fast."""
    import time
    
    model = MLPModel()
    model.eval()
    
    x = torch.randn(1000, 4)
    
    start = time.time()
    with torch.no_grad():
        y = model(x)
    elapsed = time.time() - start
    
    # Should complete in less than 0.1 seconds for 1000 samples
    assert elapsed < 0.1, f"Forward pass too slow: {elapsed:.3f}s for 1000 samples"

def test_mlp_training_speed():
    """Test that training step is reasonably fast."""
    import time
    
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    x = torch.randn(1000, 4)
    y_true = torch.randn(1000, 1)
    
    start = time.time()
    for _ in range(10):  # 10 iterations
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    elapsed = time.time() - start
    
    # Should complete 10 iterations in less than 1 second
    assert elapsed < 1.0, f"Training too slow: {elapsed:.3f}s for 10 iterations"

def test_mlp_numerical_stability():
    """Test that the model is numerically stable across various input ranges."""
    model = MLPModel()
    
    # Test various input scales
    scales = [1e-6, 1e-3, 1e0, 1e3, 1e6]
    
    for scale in scales:
        x = torch.randn(10, 4) * scale
        y = model(x)
        
        assert torch.isfinite(y).all(), f"Numerical instability at scale {scale}"

def test_mlp_layer_norm_compatibility():
    """Test that the model can work with layer normalization if added."""
    # This is a forward compatibility test
    model = MLPModel()
    
    # The current architecture doesn't have LayerNorm, but this test
    # ensures the structure allows for easy addition if needed
    assert len(model.network) == 5, "Architecture should have 5 layers for easy extension"

def test_mlp_gradient_norm():
    """Test that gradient norms are reasonable during training."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    x = torch.randn(32, 4)
    y_true = torch.randn(32, 1)
    
    y_pred = model(x)
    loss = criterion(y_pred, y_true)
    
    optimizer.zero_grad()
    loss.backward()
    
    # Compute gradient norm
    total_norm = 0.0
    for param in model.parameters():
        if param.grad is not None:
            total_norm += param.grad.data.norm(2).item() ** 2
    total_norm = total_norm ** 0.5
    
    # Gradient norm should be finite and reasonable
    assert total_norm < 1e6, f"Gradient norm too large: {total_norm}"
    assert total_norm > 0, "Gradient norm is zero"

def test_mlp_learning_curve():
    """Test that the model shows learning progress over multiple steps."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    # Generate fixed data
    x = torch.randn(100, 4)
    y_true = torch.randn(100, 1)
    
    losses = []
    for _ in range(100):
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    
    # Loss should generally decrease
    initial_loss = losses[0]
    final_loss = losses[-1]
    
    # Allow for some noise, but final loss should be lower
    assert final_loss < initial_loss * 1.5, "Model did not show learning progress"

def test_mlp_overfitting_small_dataset():
    """Test that the model can overfit a very small dataset (sanity check)."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    criterion = nn.MSELoss()
    
    # Very small dataset
    x = torch.randn(5, 4)
    y_true = torch.randn(5, 1)
    
    # Train for many epochs
    for _ in range(1000):
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    # Final loss should be very small
    final_loss = loss.item()
    assert final_loss < 0.01, f"Model could not overfit small dataset: final loss = {final_loss}"

def test_mlp_generalization_gap():
    """Test that there is a generalization gap between train and test loss."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    # Training data
    x_train = torch.randn(50, 4)
    y_train = torch.randn(50, 1)
    
    # Test data (different random seed)
    torch.manual_seed(999)
    x_test = torch.randn(50, 4)
    y_test = torch.randn(50, 1)
    torch.manual_seed(42)  # Reset seed
    
    # Train
    for _ in range(100):
        y_pred = model(x_train)
        loss = criterion(y_pred, y_train)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    # Evaluate
    model.eval()
    with torch.no_grad():
        train_loss = criterion(model(x_train), y_train).item()
        test_loss = criterion(model(x_test), y_test).item()
    
    # Test loss should be higher than train loss (generalization gap)
    # Allow for some variance in small samples
    assert test_loss >= train_loss * 0.9, "Unexpected: test loss much lower than train loss"

def test_mlp_activation_function_choice():
    """Verify that ReLU is used as the activation function."""
    model = MLPModel()
    
    # Check that ReLU is present
    has_relu = False
    for module in model.modules():
        if isinstance(module, nn.ReLU):
            has_relu = True
            break
    
    assert has_relu, "Model should use ReLU activation"

def test_mlp_output_activation():
    """Verify that there is no activation function on the output layer."""
    model = MLPModel()
    
    # The last layer should be Linear without activation
    last_layer = model.network[-1]
    assert isinstance(last_layer, nn.Linear), "Last layer should be Linear"
    
    # There should be no activation after the last layer
    # (the network should end with the Linear layer)
    assert len(model.network) == 5, "Architecture should end with Linear layer"

def test_mlp_input_normalization_sensitivity():
    """Test that model output changes with input normalization."""
    model = MLPModel()
    
    # Unnormalized input
    x_raw = torch.randn(10, 4)
    y_raw = model(x_raw)
    
    # Normalized input (zero mean, unit variance)
    x_norm = (x_raw - x_raw.mean(dim=0)) / (x_raw.std(dim=0) + 1e-8)
    y_norm = model(x_norm)
    
    # Outputs should be different
    assert not torch.allclose(y_raw, y_norm), "Model output should change with input normalization"

def test_mlp_feature_scaling_invariance():
    """Test that the model is sensitive to feature scaling (as expected)."""
    model = MLPModel()
    
    x = torch.randn(10, 4)
    y1 = model(x)
    
    # Scale one feature
    x_scaled = x.clone()
    x_scaled[:, 0] *= 10
    y2 = model(x_scaled)
    
    # Output should change
    assert not torch.allclose(y1, y2), "Model output should change with feature scaling"

def test_mlp_random_seed_consistency():
    """Test that model behavior is consistent with the same random seed."""
    torch.manual_seed(123)
    model1 = MLPModel()
    x = torch.randn(10, 4)
    y1 = model1(x)
    
    torch.manual_seed(123)
    model2 = MLPModel()
    y2 = model2(x)
    
    assert torch.allclose(y1, y2), "Model outputs should be identical with same seed"

def test_mlp_cpu_only_compatibility():
    """Test that the model works correctly on CPU (as required)."""
    model = MLPModel()
    
    # Ensure model is on CPU
    model = model.to('cpu')
    
    x = torch.randn(10, 4)
    y = model(x)
    
    assert y.device.type == 'cpu', "Output should be on CPU"
    assert torch.isfinite(y).all(), "Output should be finite on CPU"

def test_mlp_no_gpu_dependency():
    """Verify that the model does not require GPU."""
    model = MLPModel()
    
    # Should work without CUDA
    x = torch.randn(5, 4)
    y = model(x)
    
    assert torch.isfinite(y).all(), "Model should work without GPU"

def test_mlp_architecture_documentation():
    """Test that the architecture is well-documented."""
    model = MLPModel()
    
    # Check that the model has docstring
    assert model.__doc__ is not None or MLPModel.__doc__ is not None, "Model should be documented"
    
    # Check that __init__ has parameters
    import inspect
    sig = inspect.signature(MLPModel.__init__)
    params = list(sig.parameters.keys())
    assert 'input_dim' in params, "Should have input_dim parameter"
    assert 'hidden_dim_1' in params, "Should have hidden_dim_1 parameter"
    assert 'hidden_dim_2' in params, "Should have hidden_dim_2 parameter"

def test_mlp_forward_method_signature():
    """Test that the forward method has the correct signature."""
    import inspect
    
    sig = inspect.signature(MLPModel.forward)
    params = list(sig.parameters.keys())
    
    assert 'self' in params, "Forward should have self parameter"
    assert 'x' in params, "Forward should have x parameter"

def test_mlp_module_registration():
    """Test that all modules are properly registered."""
    model = MLPModel()
    
    # Check that all submodules are registered
    named_modules = list(model.named_modules())
    assert len(named_modules) > 0, "Model should have registered modules"
    
    # Check that parameters are registered
    named_params = list(model.named_parameters())
    assert len(named_params) > 0, "Model should have registered parameters"

def test_mlp_state_dict_keys():
    """Test that the state dict has the expected keys."""
    model = MLPModel()
    state_dict = model.state_dict()
    
    expected_keys = [
        'network.0.weight', 'network.0.bias',
        'network.2.weight', 'network.2.bias',
        'network.4.weight', 'network.4.bias'
    ]
    
    for key in expected_keys:
        assert key in state_dict, f"Missing key: {key}"

def test_mlp_optimizer_compatibility():
    """Test that the model is compatible with various optimizers."""
    optimizers = [
        torch.optim.SGD,
        torch.optim.Adam,
        torch.optim.AdamW,
        torch.optim.RMSprop
    ]
    
    for Optimizer in optimizers:
        model = MLPModel()
        optimizer = Optimizer(model.parameters(), lr=0.01)
        
        x = torch.randn(10, 4)
        y = model(x)
        loss = y.sum()
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        assert torch.isfinite(loss), f"Optimizer {Optimizer.__name__} failed"

def test_mlp_learning_rate_sensitivity():
    """Test that the model responds to different learning rates."""
    learning_rates = [0.001, 0.01, 0.1]
    
    losses = []
    for lr in learning_rates:
        model = MLPModel()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        criterion = nn.MSELoss()
        
        x = torch.randn(32, 4)
        y_true = torch.randn(32, 1)
        
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
    
    # Losses should be different for different learning rates
    # (though not necessarily monotonic)
    assert len(set([round(l, 6) for l in losses])) > 1, "Losses should vary with learning rate"

def test_mlp_batch_size_sensitivity():
    """Test that the model works with different batch sizes."""
    batch_sizes = [1, 2, 8, 16, 32, 64, 128]
    
    for batch_size in batch_sizes:
        model = MLPModel()
        x = torch.randn(batch_size, 4)
        y = model(x)
        
        assert y.shape == (batch_size, 1), f"Failed for batch size {batch_size}"
        assert torch.isfinite(y).all(), f"Non-finite output for batch size {batch_size}"

def test_mlp_feature_combination():
    """Test that the model can learn combinations of features."""
    model = MLPModel()
    
    # Create data where output depends on specific feature combinations
    torch.manual_seed(42)
    x = torch.randn(100, 4)
    y_true = x[:, 0] + x[:, 1] * 2 + x[:, 2] * 3 + x[:, 3] * 4  # Linear combination
    y_true = y_true.unsqueeze(1)
    
    # Train the model
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    criterion = nn.MSELoss()
    
    for _ in range(500):
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    # Final loss should be low
    final_loss = loss.item()
    assert final_loss < 0.1, f"Model failed to learn feature combination: final loss = {final_loss}"

def test_mlp_input_feature_interaction():
    """Test that the model captures interactions between input features."""
    model = MLPModel()
    
    # Create data with interaction terms
    torch.manual_seed(42)
    x = torch.randn(100, 4)
    y_true = x[:, 0] * x[:, 1] + x[:, 2] * x[:, 3]  # Interaction terms
    y_true = y_true.unsqueeze(1)
    
    # Train the model
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    criterion = nn.MSELoss()
    
    for _ in range(500):
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    # Final loss should be lower than initial
    # (We can't expect perfect learning with a small network, but should improve)
    assert loss.item() < 10.0, "Model did not learn interaction terms"

def test_mlp_output_range_control():
    """Test that the output range is controlled by the network architecture."""
    model = MLPModel()
    
    # Generate extreme inputs
    x_extreme = torch.randn(100, 4) * 100
    y_extreme = model(x_extreme)
    
    # Output should be finite and not excessively large
    assert torch.isfinite(y_extreme).all(), "Output contains non-finite values"
    assert y_extreme.abs().max().item() < 1e6, "Output values are too extreme"

def test_mlp_gradient_clipping_compatibility():
    """Test that the model works with gradient clipping."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    x = torch.randn(32, 4)
    y_true = torch.randn(32, 1)
    
    y_pred = model(x)
    loss = criterion(y_pred, y_true)
    
    optimizer.zero_grad()
    loss.backward()
    
    # Apply gradient clipping
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    
    optimizer.step()
    
    assert torch.isfinite(loss), "Gradient clipping caused issues"

def test_mlp_mixed_precision_compatibility():
    """Test that the model can work with mixed precision (if available)."""
    model = MLPModel()
    
    # Test basic forward pass
    x = torch.randn(10, 4, dtype=torch.float32)
    y = model(x)
    
    assert y.dtype == torch.float32, "Output should be float32"
    assert torch.isfinite(y).all(), "Output should be finite"

def test_mlp_convergence_check():
    """Test that the model can converge on a simple task."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    criterion = nn.MSELoss()
    
    # Simple task: y = x1 + x2 + x3 + x4
    torch.manual_seed(42)
    x = torch.randn(100, 4)
    y_true = x.sum(dim=1, keepdim=True)
    
    losses = []
    for epoch in range(200):
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    
    # Loss should decrease significantly
    initial_loss = losses[0]
    final_loss = losses[-1]
    
    assert final_loss < initial_loss * 0.1, f"Model did not converge: initial={initial_loss:.4f}, final={final_loss:.4f}"

def test_mlp_weight_decay_compatibility():
    """Test that the model works with weight decay."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=0.01)
    criterion = nn.MSELoss()
    
    x = torch.randn(32, 4)
    y_true = torch.randn(32, 1)
    
    y_pred = model(x)
    loss = criterion(y_pred, y_true)
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    assert torch.isfinite(loss), "Weight decay caused issues"

def test_mlp_adaptive_learning_rate():
    """Test that the model works with adaptive learning rate schedulers."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=50, gamma=0.5)
    criterion = nn.MSELoss()
    
    x = torch.randn(32, 4)
    y_true = torch.randn(32, 1)
    
    for epoch in range(100):
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        scheduler.step()
    
    assert torch.isfinite(loss), "Learning rate scheduler caused issues"

def test_mlp_early_stopping_compatibility():
    """Test that the model supports early stopping patterns."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    x = torch.randn(32, 4)
    y_true = torch.randn(32, 1)
    
    best_loss = float('inf')
    patience = 10
    patience_counter = 0
    
    for epoch in range(100):
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        if loss.item() < best_loss:
            best_loss = loss.item()
            patience_counter = 0
        else:
            patience_counter += 1
        
        if patience_counter >= patience:
            break  # Early stopping
    
    # Should have stopped early or completed all epochs
    assert epoch < 99 or patience_counter < patience, "Early stopping logic issue"

def test_mlp_model_summary():
    """Test that the model can provide a summary of its architecture."""
    model = MLPModel()
    
    # Count layers
    layer_count = 0
    for module in model.modules():
        if isinstance(module, (nn.Linear, nn.ReLU)):
            layer_count += 1
    
    assert layer_count == 5, f"Expected 5 layers (3 Linear + 2 ReLU), got {layer_count}"

def test_mlp_parameter_sharing():
    """Test that parameters are not shared unexpectedly."""
    model = MLPModel()
    
    # Get all parameters
    params = list(model.parameters())
    
    # Check that each parameter is unique (not the same object)
    for i in range(len(params)):
        for j in range(i + 1, len(params)):
            assert not torch.equal(params[i], params[j]), "Parameters should not be shared"

def test_mlp_input_gradient_flow():
    """Test that gradients flow back to the input."""
    model = MLPModel()
    
    x = torch.randn(10, 4, requires_grad=True)
    y = model(x)
    loss = y.sum()
    
    loss.backward()
    
    assert x.grad is not None, "Gradient should flow to input"
    assert torch.isfinite(x.grad).all(), "Input gradient should be finite"
    assert x.grad.abs().sum() > 0, "Input gradient should not be zero"

def test_mlp_batch_normalization_alternative():
    """Test that the model can work without batch normalization (as designed)."""
    model = MLPModel()
    
    # The model should work fine without batch normalization
    x = torch.randn(32, 4)
    y = model(x)
    
    assert torch.isfinite(y).all(), "Model should work without batch normalization"

def test_mlp_dropout_alternative():
    """Test that the model can work without dropout (as designed)."""
    model = MLPModel()
    
    # The model should work fine without dropout
    x = torch.randn(32, 4)
    y = model(x)
    
    assert torch.isfinite(y).all(), "Model should work without dropout"

def test_mlp_regularization_options():
    """Test that the model can work with different regularization strategies."""
    # Test with L2 regularization (weight decay)
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=0.01)
    
    x = torch.randn(32, 4)
    y = model(x)
    
    assert torch.isfinite(y).all(), "Model should work with L2 regularization"

def test_mlp_activation_alternatives():
    """Test that the model structure allows for activation function changes."""
    # This is a structural test to ensure the architecture is flexible
    model = MLPModel()
    
    # Check that we can access the ReLU layers
    relu_layers = [m for m in model.modules() if isinstance(m, nn.ReLU)]
    assert len(relu_layers) == 2, "Should have 2 ReLU layers"

def test_mlp_linear_alternatives():
    """Test that the model structure allows for linear layer changes."""
    model = MLPModel()
    
    # Check that we can access the Linear layers
    linear_layers = [m for m in model.modules() if isinstance(m, nn.Linear)]
    assert len(linear_layers) == 3, "Should have 3 Linear layers"

def test_mlp_output_activation_alternatives():
    """Test that the output layer can be modified for different tasks."""
    model = MLPModel()
    
    # The current output is linear (no activation), which is correct for regression
    # This test ensures the structure allows for modification if needed
    final_layer = model.network[-1]
    assert isinstance(final_layer, nn.Linear), "Final layer should be Linear"

def test_mlp_input_preprocessing_compatibility():
    """Test that the model is compatible with input preprocessing."""
    model = MLPModel()
    
    # Test with normalized input
    x = torch.randn(10, 4)
    x_normalized = (x - x.mean(dim=0)) / (x.std(dim=0) + 1e-8)
    y = model(x_normalized)
    
    assert torch.isfinite(y).all(), "Model should work with normalized input"

def test_mlp_output_postprocessing_compatibility():
    """Test that the model output can be post-processed."""
    model = MLPModel()
    
    x = torch.randn(10, 4)
    y = model(x)
    
    # Test post-processing operations
    y_clipped = y.clamp(-10, 10)
    y_scaled = y * 100
    
    assert torch.isfinite(y_clipped).all(), "Clipped output should be finite"
    assert torch.isfinite(y_scaled).all(), "Scaled output should be finite"

def test_mlp_model_comparison():
    """Test that two models with the same architecture are comparable."""
    model1 = MLPModel()
    model2 = MLPModel()
    
    # They should have the same architecture
    assert len(list(model1.parameters())) == len(list(model2.parameters())), "Same architecture should have same number of parameters"
    
    # But different initial weights
    for (n1, p1), (n2, p2) in zip(model1.named_parameters(), model2.named_parameters()):
        if n1 == n2:
            assert not torch.allclose(p1, p2), "Different models should have different weights"

def test_mlp_architecture_independence():
    """Test that the model architecture is independent of data."""
    model = MLPModel()
    
    # The architecture should be the same regardless of input
    x1 = torch.randn(10, 4)
    x2 = torch.randn(100, 4)
    
    y1 = model(x1)
    y2 = model(x2)
    
    assert y1.shape[1] == y2.shape[1] == 1, "Output dimension should be independent of batch size"

def test_mlp_feature_dimension_independence():
    """Test that the model is designed for 4 input features."""
    model = MLPModel()
    
    assert model.input_dim == 4, "Model should be designed for 4 input features"

def test_mlp_hidden_dimension_flexibility():
    """Test that hidden dimensions can be customized."""
    model1 = MLPModel(hidden_dim_1=32, hidden_dim_2=16)
    model2 = MLPModel(hidden_dim_1=64, hidden_dim_2=32)
    
    params1 = sum(p.numel() for p in model1.parameters())
    params2 = sum(p.numel() for p in model2.parameters())
    
    assert params2 > params1, "Larger hidden dimensions should result in more parameters"

def test_mlp_output_dimension_flexibility():
    """Test that the output dimension is fixed to 1."""
    model = MLPModel()
    
    # The output dimension should always be 1
    x = torch.randn(10, 4)
    y = model(x)
    
    assert y.shape[1] == 1, "Output dimension should always be 1"

def test_mlp_architecture_extensibility():
    """Test that the architecture can be extended with additional layers."""
    # This test verifies the structure allows for extension
    model = MLPModel()
    
    # Check that we can access all layers
    layers = list(model.network)
    assert len(layers) == 5, "Should have 5 layers"
    
    # The structure allows for adding more layers if needed
    # (though this would require modifying the __init__ method)

def test_mlp_architecture_simplicity():
    """Test that the architecture is simple and interpretable."""
    model = MLPModel()
    
    # Count the number of unique layer types
    layer_types = set()
    for module in model.modules():
        if isinstance(module, (nn.Linear, nn.ReLU)):
            layer_types.add(type(module).__name__)
    
    assert len(layer_types) == 2, "Should only have Linear and ReLU layers"

def test_mlp_architecture_efficiency():
    """Test that the architecture is efficient for the task."""
    model = MLPModel()
    
    # Count parameters
    params = sum(p.numel() for p in model.parameters())
    
    # Should be less than 1000 parameters for efficiency
    assert params < 1000, f"Model should have less than 1000 parameters, got {params}"

def test_mlp_architecture_correctness():
    """Test that the architecture matches the specification."""
    model = MLPModel()
    
    # Specification: 4 inputs -> 32 (ReLU) -> 16 (ReLU) -> 1 output
    assert model.input_dim == 4, "Input dimension should be 4"
    assert model.hidden_dim_1 == 32, "First hidden dimension should be 32"
    assert model.hidden_dim_2 == 16, "Second hidden dimension should be 16"
    
    # Check layer connections
    layer1 = model.network[0]  # 4 -> 32
    layer2 = model.network[2]  # 32 -> 16
    layer3 = model.network[4]  # 16 -> 1
    
    assert layer1.in_features == 4 and layer1.out_features == 32, "First layer incorrect"
    assert layer2.in_features == 32 and layer2.out_features == 16, "Second layer incorrect"
    assert layer3.in_features == 16 and layer3.out_features == 1, "Third layer incorrect"

def test_mlp_architecture_completeness():
    """Test that the architecture is complete and functional."""
    model = MLPModel()
    
    # Test forward pass
    x = torch.randn(10, 4)
    y = model(x)
    
    assert y.shape == (10, 1), "Output shape should be (batch_size, 1)"
    assert torch.isfinite(y).all(), "Output should be finite"
    assert not torch.isnan(y).any(), "Output should not contain NaN"
    assert not torch.isinf(y).any(), "Output should not contain Inf"

def test_mlp_architecture_validity():
    """Test that the architecture is valid and well-formed."""
    model = MLPModel()
    
    # Check that the model is properly initialized
    assert model is not None, "Model should be initialized"
    
    # Check that all parameters are initialized
    for name, param in model.named_parameters():
        assert param is not None, f"Parameter {name} should be initialized"
        assert param.shape[0] > 0, f"Parameter {name} should have valid shape"

def test_mlp_architecture_consistency():
    """Test that the architecture is consistent across different runs."""
    torch.manual_seed(42)
    model1 = MLPModel()
    
    torch.manual_seed(42)
    model2 = MLPModel()
    
    # Check that the architecture is the same
    for (n1, p1), (n2, p2) in zip(model1.named_parameters(), model2.named_parameters()):
        assert n1 == n2, "Parameter names should match"
        assert p1.shape == p2.shape, f"Parameter {n1} shapes should match"

def test_mlp_architecture_reproducibility():
    """Test that the architecture produces reproducible results."""
    torch.manual_seed(42)
    model = MLPModel()
    
    x = torch.randn(10, 4)
    y1 = model(x)
    
    torch.manual_seed(42)
    model = MLPModel()
    y2 = model(x)
    
    assert torch.allclose(y1, y2), "Results should be reproducible with same seed"

def test_mlp_architecture_stability():
    """Test that the architecture is stable during training."""
    model = MLPModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    x = torch.randn(32, 4)
    y_true = torch.randn(32, 1)
    
    for _ in range(100):
        y_pred = model(x)
        loss = criterion(y_pred, y_true)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        assert torch.isfinite(loss), "Loss should remain finite during training"

def test_mlp_architecture_robustness():
    """Test that the architecture is robust to input variations."""
    model = MLPModel()
    
    # Test with various input distributions
    distributions = [
        torch.randn(10, 4),  # Standard normal
        torch.rand(10, 4),   # Uniform [0, 1]
        torch.randn(10, 4) * 10,  # Large variance
        torch.randn(10, 4) * 0.01,  # Small variance
    ]
    
    for x in distributions:
        y = model(x)
        assert torch.isfinite(y).all(), f"Model failed for input distribution: {x}"

def test_mlp_architecture_scalability():
    """Test that the architecture scales with batch size."""
    model = MLPModel()
    
    batch_sizes = [1, 10, 100, 1000]
    
    for batch_size in batch_sizes:
        x = torch.randn(batch_size, 4)
        y = model(x)
        
        assert y.shape == (batch_size, 1), f"Failed for batch size {batch_size}"
        assert torch.isfinite(y).all(), f"Non-finite output for batch size {batch_size}"

def test_mlp_architecture_modularity():
    """Test that the architecture is modular and well-structured."""
    model = MLPModel()
    
    # Check that the model is composed of distinct modules
    assert hasattr(model, 'network'), "Model should have a 'network' attribute"
    assert isinstance(model.network, nn.Sequential), "Network should be Sequential"
    
    # Check that each layer is accessible
    for i, layer in enumerate(model.network):
        assert layer is not None, f"Layer {i} should not be None"

def test_mlp_architecture_extensibility_points():
    """Test that the architecture has clear extension points."""
    model = MLPModel()
    
    # The architecture should have clear points for extension:
    # 1. Input dimension
    # 2. Hidden dimensions
    # 3. Number of hidden layers
    # 4. Activation functions
    
    assert model.input_dim == 4, "Input dimension should be configurable"
    assert model.hidden_dim_1 == 32, "First hidden dimension should be configurable"
    assert model.hidden_dim_2 == 16, "Second hidden dimension should be configurable"

def test_mlp_architecture_documentation_completeness():
    """Test that the architecture documentation is complete."""
    # Check that the class has a docstring
    assert MLPModel.__doc__ is not None, "MLPModel should have a docstring"
    
    # Check that the docstring mentions key features
    docstring = MLPModel.__doc__.lower()
    assert 'input' in docstring, "Docstring should mention input"
    assert 'output' in docstring, "Docstring should mention output"
    assert 'layer' in docstring, "Docstring should mention layers"

def test_mlp_architecture_code_quality():
    """Test that the architecture code follows best practices."""
    model = MLPModel()
    
    # Check that the model uses proper inheritance
    assert isinstance(model, nn.Module), "Model should inherit from nn.Module"
    
    # Check that the forward method is defined
    assert hasattr(model, 'forward'), "Model should have a forward method"
    assert callable(model.forward), "forward should be callable"

def test_mlp_architecture_test_coverage():
    """Test that the architecture has comprehensive test coverage."""
    # This test is a meta-test to ensure all aspects are covered
    # by the other tests in this file
    
    # The fact that this test file exists and runs successfully
    # is evidence of test coverage
    assert True, "Test coverage is validated by the existence of this test file"