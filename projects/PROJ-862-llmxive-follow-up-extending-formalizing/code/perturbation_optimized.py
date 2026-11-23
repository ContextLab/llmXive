"""
Optimized perturbation module for the noise-injection sweep.

This module provides vectorized operations for injecting Gaussian noise into
input embeddings and projecting them back to the nearest valid token embeddings.
It replaces the scalar-loop implementation in `perturbation.py` to significantly
reduce runtime during the sigma-sweep phase.

Key Optimizations:
1. Vectorized noise injection using broadcasting (no Python loops over tokens).
2. Vectorized nearest-neighbor search using matrix multiplication (dot product)
   instead of explicit distance loops.
3. Efficient memory management via torch operations on CPU (no GPU offloading).
"""

import torch
import numpy as np
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

def inject_and_project_vectorized(
    embeddings: torch.Tensor,
    sigma: float,
    model_embedding_matrix: torch.Tensor,
    tokenizer_vocab_size: Optional[int] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Inject Gaussian noise into a batch of embeddings and project to the nearest
    valid token embeddings using vectorized operations.

    Args:
        embeddings (torch.Tensor): Input embeddings of shape (batch_size, seq_len, hidden_dim).
        sigma (float): Standard deviation of the Gaussian noise to inject.
        model_embedding_matrix (torch.Tensor): The model's embedding matrix of shape (vocab_size, hidden_dim).
        tokenizer_vocab_size (int, optional): The actual vocabulary size to use (in case the matrix is padded).

    Returns:
        Tuple[torch.Tensor, torch.Tensor]:
            - perturbed_token_ids: Shape (batch_size, seq_len), indices of nearest tokens.
            - perturbed_embeddings: Shape (batch_size, seq_len, hidden_dim), the projected embeddings.
    """
    if not isinstance(embeddings, torch.Tensor):
        raise TypeError(f"embeddings must be a torch.Tensor, got {type(embeddings)}")
    if not isinstance(model_embedding_matrix, torch.Tensor):
        raise TypeError(f"model_embedding_matrix must be a torch.Tensor, got {type(model_embedding_matrix)}")

    batch_size, seq_len, hidden_dim = embeddings.shape
    vocab_size, emb_dim = model_embedding_matrix.shape

    if hidden_dim != emb_dim:
        raise ValueError(
            f"Embedding dimension mismatch: input {hidden_dim} vs model {emb_dim}"
        )

    # Determine effective vocab size if provided
    effective_vocab = tokenizer_vocab_size if tokenizer_vocab_size is not None else vocab_size
    if effective_vocab > vocab_size:
        effective_vocab = vocab_size

    # 1. Vectorized Noise Injection
    # Generate noise of the same shape as embeddings
    noise = torch.normal(0.0, sigma, size=embeddings.shape, dtype=embeddings.dtype, device=embeddings.device)
    perturbed_embeddings_raw = embeddings + noise

    # 2. Vectorized Nearest-Neighbor Projection
    # We need to find the token in model_embedding_matrix closest to each perturbed vector.
    # Distance^2 = ||a||^2 + ||b||^2 - 2*a.b
    # Since we want to minimize distance, we can maximize the dot product if embeddings are normalized.
    # However, perturbed embeddings are not necessarily normalized.
    # We will compute Euclidean distance directly for accuracy.

    # Reshape perturbed embeddings to (batch_size * seq_len, hidden_dim)
    flat_perturbed = perturbed_embeddings_raw.view(-1, hidden_dim)  # (N, D)
    N = flat_perturbed.shape[0]

    # Get the model embedding matrix (V, D)
    # We only consider the valid vocab range
    valid_model_embeddings = model_embedding_matrix[:effective_vocab]  # (V, D)

    # Compute squared norms for perturbed vectors: (N, 1)
    sq_norm_perturbed = torch.sum(flat_perturbed ** 2, dim=1, keepdim=True)  # (N, 1)

    # Compute squared norms for model embeddings: (1, V)
    sq_norm_model = torch.sum(valid_model_embeddings ** 2, dim=1, keepdim=True).t()  # (1, V)

    # Compute dot product: (N, V)
    # dot = flat_perturbed @ valid_model_embeddings.T
    dot_product = torch.matmul(flat_perturbed, valid_model_embeddings.t())

    # Compute squared Euclidean distances: (N, V)
    # dist^2 = ||x||^2 + ||c||^2 - 2*x.c
    sq_distances = sq_norm_perturbed + sq_norm_model - 2 * dot_product

    # Ensure no negative values due to floating point errors
    sq_distances = torch.clamp(sq_distances, min=0.0)

    # Find the index of the minimum distance for each perturbed vector
    # indices shape: (N,)
    nearest_indices = torch.argmin(sq_distances, dim=1)

    # Reshape back to (batch_size, seq_len)
    perturbed_token_ids = nearest_indices.view(batch_size, seq_len)

    # Retrieve the actual projected embeddings from the model matrix
    # Using advanced indexing: model_matrix[nearest_indices]
    # This creates a view of the embeddings corresponding to the nearest tokens
    perturbed_embeddings = valid_model_embeddings[nearest_indices]  # (N, D)
    perturbed_embeddings = perturbed_embeddings.view(batch_size, seq_len, hidden_dim)

    logger.debug(f"Vectorized projection complete: {N} vectors processed in one pass.")

    return perturbed_token_ids, perturbed_embeddings


def inject_and_project(
    embeddings: torch.Tensor,
    sigma: float,
    model_embedding_matrix: torch.Tensor,
    tokenizer_vocab_size: Optional[int] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Wrapper function that uses the optimized vectorized implementation.
    
    This function maintains the same signature as the original scalar implementation
    in `perturbation.py` but delegates to the optimized version for performance.
    It serves as the entry point for the sweep loop to ensure backward compatibility
    while gaining the performance benefits of vectorization.

    Args:
        embeddings (torch.Tensor): Input embeddings of shape (batch_size, seq_len, hidden_dim).
        sigma (float): Standard deviation of the Gaussian noise to inject.
        model_embedding_matrix (torch.Tensor): The model's embedding matrix.
        tokenizer_vocab_size (int, optional): The actual vocabulary size.

    Returns:
        Tuple[torch.Tensor, torch.Tensor]: (perturbed_token_ids, perturbed_embeddings)
    """
    return inject_and_project_vectorized(
        embeddings, sigma, model_embedding_matrix, tokenizer_vocab_size
    )
