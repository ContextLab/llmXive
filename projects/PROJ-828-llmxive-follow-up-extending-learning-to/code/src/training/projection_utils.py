"""
projection_utils.py

Utilities for SVD-based subspace projection and gradient constraint logic.
Handles layer-wise SVD, variance thresholding, and fallback strategies for flat spectra.
"""

import os
import logging
import numpy as np
import torch
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def perform_layerwise_svd(
    updates: Dict[str, torch.Tensor],
    target_variance: float = 0.80,
    max_rank: int = 50,
    fallback_rank: int = 10
) -> Tuple[Dict[str, np.ndarray], Dict[str, int], bool]:
    """
    Perform SVD on accumulated update matrices for each layer.
    
    Args:
        updates: Dictionary mapping layer names to update tensors (Delta W).
        target_variance: Target cumulative explained variance (default 0.80).
        max_rank: Maximum rank to consider for variance calculation (default 50).
        fallback_rank: Rank to use if spectrum is too flat (default 10).
        
    Returns:
      - subspace_basis: Dict mapping layer names to (k x n) basis matrices (numpy).
      - ranks_used: Dict mapping layer names to the selected rank k.
      - fallback_triggered: Boolean indicating if any layer triggered the flat-spectrum fallback.
    """
    subspace_basis = {}
    ranks_used = {}
    fallback_triggered = False

    for layer_name, delta_w in updates.items():
        # Ensure tensor is on CPU and contiguous
        if delta_w.device.type != 'cpu':
            delta_w = delta_w.cpu()
        delta_w = delta_w.contiguous()

        # Flatten to 2D if necessary (assuming weight matrices are 2D or can be treated as such)
        # If delta_w is [out_features, in_features], keep as is.
        # If it's higher dimensional (e.g. conv), we might need to flatten appropriately.
        # For this task, we assume standard linear layer weights [out, in].
        if delta_w.dim() > 2:
            # Flatten all but the last dimension to treat as a matrix of vectors
            original_shape = delta_w.shape
            delta_w_flat = delta_w.view(delta_w.shape[0], -1)
            logger.warning(f"Layer {layer_name} has dim > 2. Flattening to {delta_w_flat.shape} for SVD.")
        else:
            delta_w_flat = delta_w
            original_shape = None

        # Perform SVD
        # U: [m, k], S: [k], Vt: [k, n]
        # Use torch.svd for stability or torch.linalg.svd
        try:
            U, S, Vt = torch.linalg.svd(delta_w_flat, full_matrices=False)
        except RuntimeError as e:
            logger.error(f"SVD failed for layer {layer_name}: {e}")
            raise

        # Convert to numpy for variance calculation
        S_np = S.numpy()
        total_variance = np.sum(S_np ** 2)
        
        if total_variance == 0:
            logger.warning(f"Layer {layer_name} has zero variance. Using fallback rank {fallback_rank}.")
            k = fallback_rank
            # Create a random orthogonal basis if variance is zero to avoid NaNs
            # Or just take the top k rows of Vt (which might be zero)
            # Better: take top k from Vt, if S is zero, Vt is arbitrary but we need a valid projection.
            # We'll take the first k rows of Vt.
            basis = Vt[:k, :].numpy()
            subspace_basis[layer_name] = basis
            ranks_used[layer_name] = k
            fallback_triggered = True
            continue

        cumulative_variance = np.cumsum(S_np ** 2) / total_variance
        
        # Find k such that cumulative variance >= target_variance
        # Limit search to max_rank
        search_limit = min(len(cumulative_variance), max_rank)
        
        # Check if we can meet the target within max_rank
        if cumulative_variance[search_limit - 1] < target_variance:
            # Flat spectrum detected: even at max_rank, we haven't reached 80%
            logger.warning(
                f"Flat spectrum detected for layer {layer_name}. "
                f"Max variance at k={search_limit} is {cumulative_variance[search_limit-1]:.4f} < {target_variance}. "
                f"Using fixed fallback rank k={fallback_rank}."
            )
            k = fallback_rank
            fallback_triggered = True
        else:
            # Find the first index where cumulative variance >= target
            # np.searchsorted returns the index to insert to maintain order.
            # We want the first index where value >= target.
            k_idx = np.searchsorted(cumulative_variance, target_variance, side='left')
            # Ensure k is at least 1 and within bounds
            k = max(1, min(k_idx + 1, search_limit))
            
            # Double check: if k_idx is 0, we take 1. If k_idx is search_limit-1, we take search_limit.
            # Actually, if cumulative_variance[0] >= target, k_idx=0, we want k=1.
            # If cumulative_variance[search_limit-1] < target, we are in the fallback branch above.
            # So here, k_idx is valid.
            # However, searchsorted returns index. If we need k elements, and index is i, we take i+1 elements?
            # Example: cum = [0.1, 0.4, 0.85], target=0.8. searchsorted -> 2. We want k=3 (indices 0,1,2).
            # So k = k_idx + 1.
            # But if cum[0] >= 0.8, searchsorted -> 0. k=1. Correct.
            k = k_idx + 1

        # Extract top-k right singular vectors (rows of Vt)
        # Vt shape: [k, n] where n is number of parameters
        top_k_vectors = Vt[:k, :]
        
        subspace_basis[layer_name] = top_k_vectors.numpy()
        ranks_used[layer_name] = k

    return subspace_basis, ranks_used, fallback_triggered

def project_gradient_to_subspace(
    gradient: torch.Tensor,
    basis: np.ndarray,
    layer_name: str
) -> torch.Tensor:
    """
    Project a gradient vector onto the subspace defined by the basis.
    
    Args:
        gradient: The gradient tensor to project.
        basis: The subspace basis matrix (k x n) from perform_layerwise_svd.
        layer_name: Name of the layer for logging.
        
    Returns:
        projected_gradient: The gradient projected onto the subspace.
    """
    if gradient.device.type != 'cpu':
        gradient = gradient.cpu()
    
    # Flatten gradient to match basis dimensions
    if gradient.dim() > 2:
        grad_flat = gradient.view(gradient.shape[0], -1)
    else:
        grad_flat = gradient

    grad_vec = grad_flat.view(-1) # [n]
    basis_tensor = torch.from_numpy(basis).to(grad_vec.dtype) # [k, n]
    
    # Project: p = B^T (B B^T)^{-1} B g
    # Since B has orthonormal rows (from SVD of Vt), B B^T = I.
    # So p = B^T (B g)
    # B g is a vector of size k: dot products of basis vectors with gradient
    coeffs = torch.matmul(basis_tensor, grad_vec) # [k]
    projected = torch.matmul(basis_tensor.t(), coeffs) # [n]
    
    # Reshape back to original shape
    if gradient.dim() > 2:
        projected = projected.view(gradient.shape)
    else:
        projected = projected.view(gradient.shape)
        
    return projected

def save_subspace_artifacts(
    subspace_basis: Dict[str, np.ndarray],
    ranks_used: Dict[str, int],
    output_dir: str,
    seed: int
) -> None:
    """
    Save the computed subspace bases and metadata to disk.
    
    Args:
        subspace_basis: Dict of layer_name -> basis matrix.
        ranks_used: Dict of layer_name -> rank k.
        output_dir: Directory to save artifacts.
        seed: The random seed used for this run.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save basis matrices
    for layer_name, basis in subspace_basis.items():
        safe_name = layer_name.replace("/", "_").replace(".", "_")
        filename = f"subspace_{safe_name}_seed{seed}.npy"
        np.save(output_path / filename, basis)
        logger.info(f"Saved subspace basis for {layer_name} to {filename} (k={ranks_used[layer_name]})")
    
    # Save metadata
    metadata = {
        "seed": seed,
        "ranks_used": ranks_used,
        "total_layers": len(subspace_basis)
    }
    with open(output_path / f"subspace_metadata_seed{seed}.json", "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved subspace metadata to subspace_metadata_seed{seed}.json")

def main():
    """
    Main entry point for testing projection utilities.
    """
    import json
    from src.utils.seeds import set_seed

    logging.basicConfig(level=logging.INFO)
    
    # Test with synthetic data to verify fallback logic
    set_seed(42)
    
    # Create dummy updates
    dummy_updates = {
        "layer_0": torch.randn(100, 100),
        "layer_1": torch.randn(50, 50),
    }
    
    # Force a flat spectrum scenario by making S decay very slowly or be uniform
    # We'll mock the SVD to simulate a flat spectrum for testing
    # But for now, let's just run the real logic on random data
    # Random data usually has a decent spectrum, but let's try to trigger fallback if possible
    # Or just verify the logic runs without crashing.
    
    try:
        basis, ranks, fallback = perform_layerwise_svd(dummy_updates, target_variance=0.99, max_rank=50, fallback_rank=10)
        logger.info(f"Fallback triggered: {fallback}")
        logger.info(f"Ranks used: {ranks}")
        
        # Verify shapes
        for name, b in basis.items():
            logger.info(f"Layer {name}: basis shape {b.shape}, rank {ranks[name]}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
