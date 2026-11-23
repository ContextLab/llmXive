"""
Original perturbation module (Scalar Implementation).

This file is kept for reference and backward compatibility with tests
that might expect the scalar logic. The production pipeline now uses
`perturbation_optimized.py` which provides the same interface but with
vectorized operations for performance.

NOTE: This implementation is significantly slower than `inject_and_project_vectorized`
and should not be used for large-scale sweeps.
"""

import torch
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ProjectionError(Exception):
    """
    Raised when projection to the nearest valid token fails.
    This prevents corrupted data from entering the analysis pipeline.
    """
    pass

def inject_and_project(
    embeddings: torch.Tensor,
    sigma: float,
    model_embedding_matrix: torch.Tensor,
    tokenizer_vocab_size: Optional[int] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Inject Gaussian noise and project to nearest token (Scalar Implementation).
    
    This is the original implementation used before T036 optimization.
    It iterates over tokens individually, which is slow for large batches.

    Args:
        embeddings (torch.Tensor): Input embeddings.
        sigma (float): Noise standard deviation.
        model_embedding_matrix (torch.Tensor): Model embedding matrix.
        tokenizer_vocab_size (int, optional): Vocabulary size.

    Returns:
        perturbed_token_ids: Tensor of shape (batch_size, seq_len)
        perturbed_embeddings: Tensor of shape (batch_size, seq_len, hidden_dim)
    
    Raises:
        ProjectionError: If the embedding matrix dimensions are incompatible 
                         or if the projection logic fails unexpectedly.
    """
    logger.debug(f"Injecting noise with sigma={sigma}")
    
    # Validate inputs immediately to prevent silent failures
    if input_embeddings is None:
        raise ProjectionError("Input embeddings cannot be None.")
    
    if model_embedding_matrix is None:
        raise ProjectionError("Model embedding matrix cannot be None.")
    
    if not isinstance(input_embeddings, torch.Tensor) or not isinstance(model_embedding_matrix, torch.Tensor):
        raise ProjectionError("Inputs must be PyTorch tensors.")

    device = input_embeddings.device
    
    try:
        batch_size, seq_len, hidden_dim = input_embeddings.shape
        vocab_size, embed_dim = model_embedding_matrix.shape
    except (ValueError, TypeError) as e:
        raise ProjectionError(f"Failed to determine tensor shapes: {e}")

    # 1. Dimension Mismatch Check (Critical Safety Step)
    if hidden_dim != embed_dim:
        raise ProjectionError(
            f"Dimension mismatch: Input embeddings have hidden_dim={hidden_dim}, "
            f"but model embedding matrix has embed_dim={embed_dim}. "
            f"Cannot project embeddings of incompatible dimensions."
        )

    if vocab_size == 0:
        raise ProjectionError("Model embedding matrix is empty; cannot project to valid tokens.")

    # 2. Generate noise
    noise = torch.randn_like(input_embeddings) * sigma
    
    # 3. Add noise
    perturbed_embeddings = input_embeddings + noise
    
    # 4. Project to nearest valid token
    # Flatten for efficient computation
    flat_embeddings = perturbed_embeddings.view(-1, hidden_dim)
    
    # Compute distances to all vocab tokens
    # ||x - e||^2 = ||x||^2 + ||e||^2 - 2<x,e>
    try:
        x_norm_sq = torch.sum(flat_embeddings ** 2, dim=1, keepdim=True)
        e_norm_sq = torch.sum(model_embedding_matrix ** 2, dim=1, keepdim=True)
        dot_products = torch.matmul(flat_embeddings, model_embedding_matrix.t())
        
        distances = x_norm_sq + e_norm_sq.t() - 2 * dot_products
        distances = torch.clamp(distances, min=0.0)
        
        # Find nearest
        nearest_indices = torch.argmin(distances, dim=1)
        
        # Reshape
        perturbed_token_ids = nearest_indices.view(batch_size, seq_len)
        
        # Retrieve embeddings
        perturbed_embeddings = model_embedding_matrix[nearest_indices].view(
            batch_size, seq_len, hidden_dim
        )
    except Exception as e:
        raise ProjectionError(f"Projection calculation failed: {e}")
    
    # Apply mask
    if padding_mask is not None:
        if padding_mask.shape != (batch_size, seq_len):
            raise ProjectionError(
                f"Padding mask shape {padding_mask.shape} does not match "
                f"expected {(batch_size, seq_len)}."
            )
        valid_mask = ~padding_mask
        valid_mask_3d = valid_mask.unsqueeze(-1).expand(-1, -1, hidden_dim)
        perturbed_token_ids = torch.where(valid_mask, perturbed_token_ids, 0)
        perturbed_embeddings = torch.where(valid_mask_3d, perturbed_embeddings, torch.zeros_like(perturbed_embeddings))
    
    return perturbed_token_ids, perturbed_embeddings
