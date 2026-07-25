"""
Optimized perturbation module for T036.
Implements vectorized noise injection and projection to minimize CPU overhead.
"""
import torch
import numpy as np
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

def inject_and_project_vectorized(
    input_embeddings: torch.Tensor,
    sigma: float,
    model_embedding_matrix: torch.Tensor,
    padding_mask: Optional[torch.Tensor] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Vectorized noise injection and token projection.
    
    Args:
        input_embeddings: Tensor of shape (batch_size, seq_len, hidden_dim)
        sigma: Standard deviation for Gaussian noise
        model_embedding_matrix: Tensor of shape (vocab_size, hidden_dim)
        padding_mask: Optional boolean tensor (batch_size, seq_len) where True = valid token
    
    Returns:
        perturbed_token_ids: Tensor of shape (batch_size, seq_len)
        perturbed_embeddings: Tensor of shape (batch_size, seq_len, hidden_dim)
    """
    logger.debug(f"Starting vectorized perturbation with sigma={sigma}")
    
    device = input_embeddings.device
    batch_size, seq_len, hidden_dim = input_embeddings.shape
    
    # 1. Generate noise in one shot
    noise = torch.randn_like(input_embeddings) * sigma
    
    # 2. Add noise (vectorized)
    perturbed_embeddings = input_embeddings + noise
    
    # 3. Project to nearest valid token (vectorized)
    # Reshape for efficient matrix multiplication:
    # input: (batch * seq, hidden)
    # embedding_matrix: (vocab, hidden)
    # We need to compute distance to all vocab tokens for every position
    
    flat_embeddings = perturbed_embeddings.view(-1, hidden_dim)
    
    # Compute squared Euclidean distances: ||x - e||^2 = ||x||^2 + ||e||^2 - 2<x,e>
    x_norm_sq = torch.sum(flat_embeddings ** 2, dim=1, keepdim=True)  # (N, 1)
    e_norm_sq = torch.sum(model_embedding_matrix ** 2, dim=1, keepdim=True)  # (V, 1)
    
    # Dot product: (N, hidden) @ (hidden, V) -> (N, V)
    dot_products = torch.matmul(flat_embeddings, model_embedding_matrix.t())
    
    # Distance matrix: (N, V)
    distances = x_norm_sq + e_norm_sq.t() - 2 * dot_products
    
    # Handle potential numerical issues
    distances = torch.clamp(distances, min=0.0)
    
    # Find nearest token indices
    # distances shape: (batch_size * seq_len, vocab_size)
    nearest_indices = torch.argmin(distances, dim=1)
    
    # Reshape back to (batch_size, seq_len)
    perturbed_token_ids = nearest_indices.view(batch_size, seq_len)
    
    # Retrieve the actual embeddings for the nearest tokens
    # This ensures we use the exact model embeddings, not the perturbed ones
    perturbed_embeddings = model_embedding_matrix[nearest_indices].view(
        batch_size, seq_len, hidden_dim
    )
    
    # Apply padding mask if provided (set perturbed tokens to 0 where padding)
    if padding_mask is not None:
        # Create inverse mask: False where padding, True where valid
        valid_mask = ~padding_mask
        # Expand to 3D
        valid_mask_3d = valid_mask.unsqueeze(-1).expand(-1, -1, hidden_dim)
        # Zero out padding positions
        perturbed_token_ids = torch.where(valid_mask, perturbed_token_ids, 0)
        perturbed_embeddings = torch.where(valid_mask_3d, perturbed_embeddings, torch.zeros_like(perturbed_embeddings))
    
    logger.debug(f"Vectorized perturbation complete. Output shape: {perturbed_embeddings.shape}")
    return perturbed_token_ids, perturbed_embeddings

def inject_and_project(
    input_embeddings: torch.Tensor,
    sigma: float,
    model_embedding_matrix: torch.Tensor,
    padding_mask: Optional[torch.Tensor] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Public API wrapper. Currently delegates to vectorized implementation.
    Kept for API compatibility with existing code.
    """
    return inject_and_project_vectorized(
        input_embeddings, sigma, model_embedding_matrix, padding_mask
    )
