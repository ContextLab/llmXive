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
) -> Tuple[Dict[str, np.ndarray], Dict[str, int], Dict[str, float]]:
    """
    Perform SVD on accumulated update matrices for each layer.
    
    Args:
        updates: Dictionary mapping layer names to update tensors (Delta W).
        target_variance: Target cumulative explained variance (default 0.80).
        max_rank: Maximum rank to consider (default 50).
        fallback_rank: Rank to use if flat spectrum detected (default 10).
        
    Returns:
        Tuple of:
            - subspace_bases: Dict mapping layer names to subspace matrices (k x n_params).
            - selected_ranks: Dict mapping layer names to selected k.
            - explained_variances: Dict mapping layer names to achieved variance.
    """
    subspace_bases = {}
    selected_ranks = {}
    explained_variances = {}
    
    for layer_name, delta_w in updates.items():
        # Ensure tensor is 2D (flatten if necessary)
        if delta_w.dim() > 2:
            delta_w = delta_w.view(delta_w.shape[0], -1)
        elif delta_w.dim() == 1:
            delta_w = delta_w.unsqueeze(0)
        
        # Convert to numpy for SVD
        delta_np = delta_w.detach().cpu().numpy().astype(np.float64)
        
        # Perform SVD
        try:
            U, S, Vt = np.linalg.svd(delta_np, full_matrices=False)
        except np.linalg.LinAlgError as e:
            logger.error(f"SVD failed for layer {layer_name}: {e}")
            raise
        
        # Calculate total variance
        total_variance = np.sum(S ** 2)
        if total_variance == 0:
            logger.warning(f"Zero variance in updates for layer {layer_name}. Using fallback rank.")
            # Return a zero matrix of fallback rank
            n_params = delta_np.shape[1]
            subspace_bases[layer_name] = np.zeros((fallback_rank, n_params), dtype=np.float64)
            selected_ranks[layer_name] = fallback_rank
            explained_variances[layer_name] = 0.0
            continue
        
        # Calculate cumulative explained variance
        cumulative_variance = np.cumsum(S ** 2) / total_variance
        
        # Find the smallest k such that cumulative variance >= target
        selected_k = None
        achieved_variance = 0.0
        
        # Search up to min(max_rank, number of singular values)
        search_limit = min(max_rank, len(S))
        
        for k in range(1, search_limit + 1):
            cum_var = cumulative_variance[k - 1]
            if cum_var >= target_variance:
                selected_k = k
                achieved_variance = cum_var
                break
        
        # Fallback logic for flat spectrum
        if selected_k is None:
            # Check if the spectrum is flat (cumulative variance < target even at max_rank)
            max_cum_var = cumulative_variance[-1]
            if max_cum_var < target_variance:
                logger.warning(
                    f"Flat spectrum detected for layer {layer_name}: "
                    f"max cumulative variance {max_cum_var:.4f} < target {target_variance}. "
                    f"Using fixed k={fallback_rank}."
                )
                selected_k = fallback_rank
                # Recalculate achieved variance for the fallback rank
                if fallback_rank <= len(S):
                    achieved_variance = cumulative_variance[fallback_rank - 1]
                else:
                    achieved_variance = max_cum_var
            else:
                # This case should theoretically not be reached if the loop logic is correct,
                # but as a safety fallback:
                logger.warning(
                    f"Could not determine rank for layer {layer_name}. Using fallback k={fallback_rank}."
                )
                selected_k = fallback_rank
                if fallback_rank <= len(S):
                    achieved_variance = cumulative_variance[fallback_rank - 1]
                else:
                    achieved_variance = 1.0 # Cap at 1.0 if we took all available
        
        # Construct subspace basis (k x n_params)
        # U is (m, k), S is (k,), Vt is (k, n)
        # We want the basis in the parameter space (rows of Vt scaled by S)
        # Or simply the top k right singular vectors (Vt[:k])
        # The task asks for "stable subspace matrix (shape k x n_params)"
        # Vt has shape (k, n_params) for the top k components
        subspace_basis = Vt[:selected_k, :]
        
        subspace_bases[layer_name] = subspace_basis
        selected_ranks[layer_name] = selected_k
        explained_variances[layer_name] = achieved_variance
        
        logger.info(
            f"Layer {layer_name}: Selected k={selected_k}, "
            f"Achieved variance={achieved_variance:.4f}"
        )
    
    return subspace_bases, selected_ranks, explained_variances

def project_gradient_to_subspace(
    gradient: torch.Tensor,
    subspace_basis: np.ndarray
) -> torch.Tensor:
    """
    Project a gradient vector onto the subspace defined by the basis.
    
    Args:
        gradient: The gradient tensor to project.
        subspace_basis: The subspace basis matrix (k x n_params).
        
    Returns:
        The projected gradient tensor.
    """
    # Flatten gradient
    grad_flat = gradient.detach().cpu().numpy().flatten().astype(np.float64)
    
    # Ensure basis is 2D
    if subspace_basis.ndim != 2:
        raise ValueError(f"Subspace basis must be 2D, got {subspace_basis.ndim}D")
    
    # Project: P = V^T (V V^T)^-1 V g
    # Since V (rows of subspace_basis) are orthonormal (from SVD), V V^T = I
    # So projection is simply V^T (V g) -> reconstruct in original space?
    # Wait, standard projection onto row space of V (where V is k x n):
    # proj = V^T (V V^T)^-1 V x. If V has orthonormal rows, V V^T = I.
    # proj = V^T V x.
    
    # Calculate coefficients: c = V * x
    coefficients = np.dot(subspace_basis, grad_flat)
    
    # Reconstruct: x_proj = V^T * c
    projected_flat = np.dot(subspace_basis.T, coefficients)
    
    # Reshape back to original gradient shape
    projected_tensor = torch.tensor(
        projected_flat.reshape(gradient.shape),
        dtype=gradient.dtype,
        device=gradient.device
    )
    
    return projected_tensor

def save_subspace_artifacts(
    subspace_bases: Dict[str, np.ndarray],
    selected_ranks: Dict[str, int],
    explained_variances: Dict[str, float],
    output_dir: str
) -> Path:
    """
    Save subspace artifacts to disk.
    
    Args:
        subspace_bases: Dict of layer names to basis matrices.
        selected_ranks: Dict of layer names to selected ranks.
        explained_variances: Dict of layer names to achieved variances.
        output_dir: Directory to save artifacts.
        
    Returns:
        Path to the saved summary file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save individual bases
    for layer_name, basis in subspace_bases.items():
        safe_name = layer_name.replace("/", "_").replace(".", "_")
        np.save(output_path / f"subspace_{safe_name}.npy", basis)
    
    # Save metadata
    metadata = {
        "selected_ranks": selected_ranks,
        "explained_variances": explained_variances
    }
    
    import json
    with open(output_path / "subspace_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Saved subspace artifacts to {output_path}")
    return output_path / "subspace_metadata.json"

def main():
    """Main entry point for testing projection utilities."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    logger.info("Projection utilities module loaded.")
    logger.info("Use perform_layerwise_svd, project_gradient_to_subspace, or save_subspace_artifacts.")

if __name__ == "__main__":
    main()