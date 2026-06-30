"""
Unit tests for KVarNQuantizer functionality.
Includes tests for variance clamping and MSE comparison against Uniform quantization.
"""
import torch
import pytest
import numpy as np

# Import existing implementations
from src.quantization.uniform import UniformQuantizer
from src.quantization.kvarn import KVarNQuantizer


def test_variance_clamping():
    """
    T010: Verify that variance clamping works correctly (var < 1e-8).
    Ensures the quantizer handles near-zero variance regions without numerical instability.
    """
    # Create a tensor with very low variance (near zero)
    low_var_tensor = torch.ones(1, 4, 128) * 0.0001  # Constant-ish tensor
    low_var_tensor += torch.randn(1, 4, 128) * 1e-10  # Add tiny noise

    quantizer = KVarNQuantizer(bits=8)

    # This should not raise an error due to division by zero or negative variance
    try:
        quantized = quantizer.quantize(low_var_tensor)
        dequantized = quantizer.dequantize(quantized)
        assert quantized.shape == low_var_tensor.shape
        assert dequantized.shape == low_var_tensor.shape
    except Exception as e:
        pytest.fail(f"Variance clamping failed with error: {e}")


def test_mse_comparison_kvarn_vs_uniform():
    """
    T011: Unit test comparing MSE of KVarN vs Uniform on a synthetic tensor slice.
    
    This test creates a synthetic tensor with varying local variance regions to simulate
    real hidden states. It then quantizes the tensor using both KVarN and Uniform quantizers
    and compares the Mean Squared Error (MSE) of the reconstruction.
    
    Expectation: KVarN should generally achieve lower or comparable MSE than Uniform
    quantization, especially in regions with varying variance, because it adapts the
    quantization scale based on local variance.
    """
    torch.manual_seed(42)
    
    # Create a synthetic tensor slice simulating hidden states
    # Shape: (batch, seq_len, hidden_dim)
    batch_size = 2
    seq_len = 64
    hidden_dim = 256
    
    # Create a tensor with varying patterns:
    # - Low variance region (first half)
    # - High variance region (second half)
    # - Mixed region
    tensor_low_var = torch.randn(batch_size, seq_len // 2, hidden_dim) * 0.1
    tensor_high_var = torch.randn(batch_size, seq_len // 2, hidden_dim) * 5.0
    
    synthetic_tensor = torch.cat([tensor_low_var, tensor_high_var], dim=1)
    
    # Initialize quantizers
    uniform_quantizer = UniformQuantizer(bits=8)
    kvarn_quantizer = KVarNQuantizer(bits=8)
    
    # Quantize and dequantize
    uniform_quantized = uniform_quantizer.quantize(synthetic_tensor)
    uniform_dequantized = uniform_quantizer.dequantize(uniform_quantized)
    
    kvarn_quantized = kvarn_quantizer.quantize(synthetic_tensor)
    kvarn_dequantized = kvarn_quantizer.dequantize(kvarn_quantized)
    
    # Calculate MSE for both
    mse_uniform = torch.mean((synthetic_tensor - uniform_dequantized) ** 2).item()
    mse_kvarn = torch.mean((synthetic_tensor - kvarn_dequantized) ** 2).item()
    
    # Assert that MSE values are valid numbers
    assert np.isfinite(mse_uniform), "Uniform MSE is not finite"
    assert np.isfinite(mse_kvarn), "KVarN MSE is not finite"
    
    # Log the results for observation
    print(f"Uniform Quantization MSE: {mse_uniform:.6f}")
    print(f"KVarN Quantization MSE: {mse_kvarn:.6f}")
    
    # Assert that KVarN performs at least as well as Uniform
    # In some edge cases they might be equal, but KVarN should not be significantly worse
    # We allow a small tolerance for numerical differences
    tolerance = 0.01 * mse_uniform  # 1% tolerance
    assert mse_kvarn <= mse_uniform + tolerance, (
        f"KVarN MSE ({mse_kvarn:.6f}) is significantly worse than Uniform MSE ({mse_uniform:.6f})"
    )
    
    # Additional check: ensure quantization actually happened (dequantized != original)
    assert not torch.allclose(synthetic_tensor, uniform_dequantized, atol=1e-6), \
        "Uniform quantization produced identical output (no quantization occurred)"
    assert not torch.allclose(synthetic_tensor, kvarn_dequantized, atol=1e-6), \
        "KVarN quantization produced identical output (no quantization occurred)"