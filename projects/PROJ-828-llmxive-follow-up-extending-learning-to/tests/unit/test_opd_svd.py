"""
Contract test for OPD SVD output shape.

This test verifies that the SVD decomposition performed on the accumulated
  parameter updates from the OPD baseline produces matrices with the expected
  shapes and properties.

It serves as a contract test to ensure that:
1. The accumulated update matrices have the correct shape (matching model parameters).
2. The SVD decomposition produces U, S, Vh matrices with valid shapes.
3. The top-k singular vectors can be extracted correctly.
4. The stable subspace matrix has the expected shape (k x n_params).

This test is part of User Story 1 (US1) and must pass before proceeding
with the full OPD baseline implementation.
"""

import pytest
import torch
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.seeds import set_seed

# Mock the OPD baseline logic for testing purposes
# In a real scenario, this would import from src/training/opd_baseline.py
# once it's implemented, but for the contract test, we simulate the expected behavior.

def create_mock_accumulated_update(layer_shape):
    """Create a mock accumulated update matrix for a given layer shape."""
    # Flatten the layer shape to a single vector
    n_params = np.prod(layer_shape)
    # Create a random matrix with some structure
    # This simulates what would be accumulated during OPD training
    update = torch.randn(n_params, dtype=torch.float32)
    return update

def perform_svd_on_update(update_matrix, k=10):
    """
    Perform SVD on the update matrix and return the top-k singular vectors.
    
    Args:
        update_matrix: Tensor of shape (n_params,) representing accumulated updates
        k: Number of top singular vectors to keep
    
    Returns:
        U: Tensor of shape (k, n_params) - left singular vectors
        S: Tensor of shape (k,) - singular values
        Vh: Tensor of shape (k, n_params) - right singular vectors (transposed)
    """
    # Reshape to matrix form if needed (for SVD)
    # For a single vector, we treat it as a rank-1 matrix
    if update_matrix.dim() == 1:
        # Reshape to (n_params, 1) for SVD
        matrix = update_matrix.unsqueeze(1)
    else:
        matrix = update_matrix
    
    # Perform SVD
    U, S, Vh = torch.svd(matrix)
    
    # Select top-k components
    k_actual = min(k, S.shape[0])
    U_top = U[:, :k_actual].t()  # Shape: (k, n_params)
    S_top = S[:k_actual]          # Shape: (k,)
    Vh_top = Vh[:k_actual, :]     # Shape: (k, n_params)
    
    return U_top, S_top, Vh_top_top

def create_mock_model_update(layer_shapes):
    """Create mock accumulated updates for all layers."""
    updates = {}
    for i, shape in enumerate(layer_shapes):
        layer_update = create_mock_accumulated_update(shape)
        updates[f"layer_{i}"] = layer_update
    return updates

class TestOPDSVDContract:
    """Contract tests for OPD SVD output shapes."""
    
    def test_accumulated_update_shape(self):
        """Test that accumulated update matrices have the expected shape."""
        # Define mock layer shapes (e.g., from a pruned TinyLlama-300M model)
        layer_shapes = [
            (4096, 4096),  # q_proj
            (4096, 4096),  # k_proj
            (4096, 4096),  # v_proj
            (4096, 4096),  # o_proj
            (4096, 11008), # gate_proj
            (11008, 4096), # up_proj
            (11008, 4096), # down_proj
        ]
        
        updates = create_mock_model_update(layer_shapes)
        
        # Verify each update has the correct shape
        for layer_name, update in updates.items():
            expected_n_params = np.prod(layer_shapes[int(layer_name.split("_")[1])])
            assert update.shape == (expected_n_params,), \
                f"Layer {layer_name} update shape {update.shape} != expected ({expected_n_params},)"
    
    def test_svd_output_shapes(self):
        """Test that SVD produces matrices with correct shapes."""
        set_seed(42)
        
        # Create a mock update
        layer_shape = (1024, 1024)  # 1M params
        update = create_mock_accumulated_update(layer_shape)
        
        # Perform SVD
        k = 10
        U, S, Vh = perform_svd_on_update(update, k=k)
        
        # Verify shapes
        n_params = np.prod(layer_shape)
        assert U.shape == (k, n_params), f"U shape {U.shape} != expected ({k}, {n_params})"
        assert S.shape == (k,), f"S shape {S.shape} != expected ({k},)"
        assert Vh.shape == (k, n_params), f"Vh shape {Vh.shape} != expected ({k}, {n_params})"
    
    def test_stable_subspace_shape(self):
        """Test that the stable subspace matrix has the expected shape."""
        set_seed(42)
        
        # Simulate accumulated updates for multiple layers
        layer_shapes = [
            (512, 512),   # 256K params
            (512, 512),   # 256K params
            (512, 2048),  # 1M params
        ]
        
        updates = create_mock_model_update(layer_shapes)
        
        # Perform SVD on each layer and collect top-k vectors
        k = 10
        subspace_matrices = []
        
        for layer_name, update in updates.items():
            U, S, Vh = perform_svd_on_update(update, k=k)
            # The stable subspace for this layer is represented by U (top-k left singular vectors)
            subspace_matrices.append(U)
        
        # Verify each subspace matrix has the correct shape
        for i, (layer_name, shape) in enumerate(zip(updates.keys(), layer_shapes)):
            n_params = np.prod(shape)
            expected_shape = (k, n_params)
            assert subspace_matrices[i].shape == expected_shape, \
                f"Subspace matrix for {layer_name} shape {subspace_matrices[i].shape} != expected {expected_shape}"
    
    def test_singular_values_non_negative(self):
        """Test that singular values are non-negative."""
        set_seed(42)
        
        layer_shape = (256, 256)
        update = create_mock_accumulated_update(layer_shape)
        
        k = 5
        U, S, Vh = perform_svd_on_update(update, k=k)
        
        # Singular values should be non-negative
        assert torch.all(S >= 0), "Singular values should be non-negative"
    
    def test_cumulative_explained_variance(self):
        """Test that we can compute cumulative explained variance correctly."""
        set_seed(42)
        
        layer_shape = (128, 128)
        update = create_mock_accumulated_update(layer_shape)
        
        # Perform full SVD to get all singular values
        if update.dim() == 1:
            matrix = update.unsqueeze(1)
        else:
            matrix = update
        
        U_full, S_full, Vh_full = torch.svd(matrix)
        
        # Test cumulative explained variance calculation
        total_variance = torch.sum(S_full ** 2)
        cumulative_variance = torch.cumsum(S_full ** 2, dim=0)
        explained_variance_ratio = cumulative_variance / total_variance
        
        # Verify that the last value is approximately 1.0 (or 100%)
        assert torch.isclose(explained_variance_ratio[-1], torch.tensor(1.0), atol=1e-5), \
            "Cumulative explained variance should sum to 1.0"
    
    def test_top_k_selection(self):
        """Test that selecting top-k vectors works correctly for different k values."""
        set_seed(42)
        
        layer_shape = (64, 64)
        update = create_mock_accumulated_update(layer_shape)
        
        n_params = np.prod(layer_shape)
        
        # Test with various k values
        for k in [1, 5, 10, 50]:
            k_actual = min(k, n_params)
            U, S, Vh = perform_svd_on_update(update, k=k)
            
            expected_shape = (k_actual, n_params)
            assert U.shape == expected_shape, \
                f"U shape {U.shape} != expected {expected_shape} for k={k}"
            assert S.shape == (k_actual,), \
                f"S shape {S.shape} != expected ({k_actual},) for k={k}"
            assert Vh.shape == expected_shape, \
                f"Vh shape {Vh.shape} != expected {expected_shape} for k={k}"
    
    def test_reconstruction_error(self):
        """Test that the SVD reconstruction error decreases with more components."""
        set_seed(42)
        
        layer_shape = (32, 32)
        update = create_mock_accumulated_update(layer_shape)
        
        if update.dim() == 1:
            matrix = update.unsqueeze(1)
        else:
            matrix = update
        
        # Perform full SVD
        U_full, S_full, Vh_full = torch.svd(matrix)
        
        # Calculate reconstruction errors for different k values
        errors = []
        for k in range(1, min(10, S_full.shape[0]) + 1):
            # Reconstruct with top-k components
            U_k = U_full[:, :k]
            S_k = S_full[:k]
            Vh_k = Vh_full[:k, :]
            
            reconstructed = U_k @ torch.diag(S_k) @ Vh_k
            error = torch.norm(matrix - reconstructed, p='fro') ** 2
            errors.append(error.item())
        
        # Verify that errors are decreasing (or at least non-increasing)
        for i in range(1, len(errors)):
            assert errors[i] <= errors[i-1] + 1e-6, \
                f"Reconstruction error should decrease with more components: {errors[i]} > {errors[i-1]}"