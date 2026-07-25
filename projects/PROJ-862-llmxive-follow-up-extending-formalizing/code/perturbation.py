"""
Perturbation module for noise injection and token projection.
"""
import torch
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def inject_and_project(
    input_embeddings: torch.Tensor,
    sigma: float,
    model_embedding_matrix: torch.Tensor,
    padding_mask: Optional[torch.Tensor] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Inject Gaussian noise and project to nearest valid token.
    
    Args:
        input_embeddings: Tensor of shape (batch_size, seq_len, hidden_dim)
        sigma: Standard deviation for Gaussian noise
        model_embedding_matrix: Tensor of shape (vocab_size, hidden_dim)
        padding_mask: Optional boolean tensor (batch_size, seq_len)
    
    Returns:
        perturbed_token_ids: Tensor of shape (batch_size, seq_len)
        perturbed_embeddings: Tensor of shape (batch_size, seq_len, hidden_dim)
    """
    logger.debug(f"Injecting noise with sigma={sigma}")
    
    device = input_embeddings.device
    batch_size, seq_len, hidden_dim = input_embeddings.shape
    
    # 1. Generate noise
    noise = torch.randn_like(input_embeddings) * sigma
    
    # 2. Add noise
    perturbed_embeddings = input_embeddings + noise
    
    # 3. Project to nearest valid token
    # Flatten for efficient computation
    flat_embeddings = perturbed_embeddings.view(-1, hidden_dim)
    
    # Compute distances to all vocab tokens
    # ||x - e||^2 = ||x||^2 + ||e||^2 - 2<x,e>
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
    
    # Apply mask
    if padding_mask is not None:
        valid_mask = ~padding_mask
        valid_mask_3d = valid_mask.unsqueeze(-1).expand(-1, -1, hidden_dim)
        perturbed_token_ids = torch.where(valid_mask, perturbed_token_ids, 0)
        perturbed_embeddings = torch.where(valid_mask_3d, perturbed_embeddings, torch.zeros_like(perturbed_embeddings))
    
    return perturbed_token_ids, perturbed_embeddings