"""
Unit tests for CPU initialization of DreamXLite model.

This test suite verifies that the DreamXLite model can be initialized
and run on a CPU-only environment without CUDA errors.

Tests:
- test_cpu_initialization: Verifies model loads on CPU without CUDA errors
- test_no_cuda_usage: Ensures no CUDA operations are attempted
- test_device_placement: Confirms all model parameters are on CPU device
"""

import os
import sys
import pytest
import torch
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.dreamx_lite import create_dreamx_lite_model, verify_dreamx_lite_cpu_initialization
from utils.config import set_global_seed, init_environment


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up test environment with deterministic seeds and CPU-only mode."""
    # Force CPU-only mode for testing
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    # Initialize environment and set seed
    init_environment()
    set_global_seed(42)
    
    yield
    
    # Cleanup
    if 'CUDA_VISIBLE_DEVICES' in os.environ:
        del os.environ['CUDA_VISIBLE_DEVICES']

def test_cpu_initialization():
    """
    Test that DreamXLite model initializes without CUDA errors on CPU runner.
    
    Verifies:
    - Model creation completes without CUDA-related exceptions
    - All parameters are placed on CPU device
    - Model can perform a forward pass on CPU
    """
    try:
        # Create model explicitly on CPU
        model = create_dreamx_lite_model(device='cpu')
        
        # Verify model is on CPU
        assert next(model.parameters()).device.type == 'cpu', \
            "Model parameters not on CPU device"
        
        # Verify no CUDA tensors exist
        for param in model.parameters():
            assert param.device.type == 'cpu', \
                f"Parameter on {param.device} instead of CPU"
        
        # Test forward pass with dummy input
        dummy_input = torch.randn(1, 3, 256, 256, device='cpu')
        with torch.no_grad():
            _ = model(dummy_input)
        
        logging.info("CPU initialization test passed successfully")
        
    except RuntimeError as e:
        error_msg = str(e)
        # Explicitly check for CUDA errors
        if 'cuda' in error_msg.lower() or 'cudnn' in error_msg.lower():
            pytest.fail(f"CUDA error during initialization: {error_msg}")
        elif 'device' in error_msg.lower():
            pytest.fail(f"Device placement error: {error_msg}")
        else:
            # Re-raise if it's a different runtime error
            raise
    except Exception as e:
        pytest.fail(f"Unexpected error during CPU initialization: {str(e)}")

def test_no_cuda_usage():
    """
    Test that no CUDA operations are attempted during model initialization.
    
    This test ensures the model is truly CPU-only and doesn't attempt
    to use CUDA even if available.
    """
    # Ensure CUDA is not available or disabled
    if torch.cuda.is_available():
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    try:
        # Create model
        model = create_dreamx_lite_model(device='cpu')
        
        # Verify no CUDA streams or contexts are created
        if torch.cuda.is_available():
            # If CUDA is available but disabled, verify we didn't use it
            assert model.device.type == 'cpu', "Model should be on CPU"
        
        # Test that all operations work on CPU
        test_input = torch.randn(2, 3, 128, 128, device='cpu')
        with torch.no_grad():
            output = model(test_input)
        
        assert output.device.type == 'cpu', "Output should be on CPU"
        logging.info("No CUDA usage test passed")
        
    except RuntimeError as e:
        if 'cuda' in str(e).lower():
            pytest.fail(f"Attempted CUDA operation: {str(e)}")
        raise

def test_device_placement():
    """
    Test that all model components are correctly placed on CPU.
    
    Verifies:
    - All parameters are on CPU
    - Buffers are on CPU
    - Submodules are on CPU
    """
    model = create_dreamx_lite_model(device='cpu')
    
    # Check all parameters
    for name, param in model.named_parameters():
        assert param.device.type == 'cpu', \
            f"Parameter '{name}' is on {param.device}, expected CPU"
    
    # Check all buffers
    for name, buffer in model.named_buffers():
        assert buffer.device.type == 'cpu', \
            f"Buffer '{name}' is on {buffer.device}, expected CPU"
    
    # Check submodule devices
    for name, module in model.named_modules():
        if name == '':
            continue  # Skip root module
        
        # Check if module has parameters
        if len(list(module.parameters())) > 0:
            first_param = next(module.parameters())
            assert first_param.device.type == 'cpu', \
                f"Module '{name}' has parameters on {first_param.device}"
    
    logging.info("Device placement test passed")

def test_verify_function():
    """
    Test the verify_dreamx_lite_cpu_initialization helper function.
    
    This function should return True if CPU initialization succeeds,
    False otherwise.
    """
    try:
        result = verify_dreamx_lite_cpu_initialization()
        assert result is True, "Verification function should return True for successful CPU init"
        logging.info("Verification function test passed")
    except Exception as e:
        pytest.fail(f"Verification function failed: {str(e)}")