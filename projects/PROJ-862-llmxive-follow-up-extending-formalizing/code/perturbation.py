"""
Perturbation module for injecting Gaussian noise and projecting to valid tokens.

This module implements the logic for:
1. Adding Gaussian noise to input embeddings.
2. Projecting the noisy embeddings to the nearest valid token embedding
   from the model's embedding matrix.
"""
import torch
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def inject_and_project(
    embedding: torch.Tensor,
    sigma: float,
    model_embedding_matrix: torch.Tensor,
    random_seed: Optional[int] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Inject Gaussian noise into embeddings and project to the nearest valid token.

    Args:
        embedding (torch.Tensor): Input embeddings of shape [batch_size, hidden_dim].
        sigma (float): Standard deviation of the Gaussian noise.
        model_embedding_matrix (torch.Tensor): The model's embedding matrix of shape 
            [vocab_size, hidden_dim].
        random_seed (int, optional): Random seed for reproducibility.

    Returns:
        Tuple[torch.Tensor, torch.Tensor]: 
            - perturbed_token_ids: Tensor of shape [batch_size] containing the indices 
              of the nearest tokens.
            - perturbed_embeddings: Tensor of shape [batch_size, hidden_dim] containing 
              the projected embeddings (which are copies of the nearest token embeddings).
    
    Raises:
        ValueError: If sigma is negative or if dimensions mismatch.
    """
    if sigma < 0:
        raise ValueError(f"Sigma must be non-negative, got {sigma}")
    
    if random_seed is not None:
        torch.manual_seed(random_seed)

    batch_size, hidden_dim = embedding.shape
    vocab_size, emb_dim = model_embedding_matrix.shape

    if hidden_dim != emb_dim:
        raise ValueError(
            f"Embedding dimension mismatch: input {hidden_dim} vs model {emb_dim}"
        )

    # 1. Inject Gaussian Noise
    # Generate noise with the same shape and dtype as the embedding
    noise = torch.randn_like(embedding) * sigma
    noisy_embedding = embedding + noise

    # 2. Project to Nearest Valid Token
    # Calculate Euclidean distances between noisy embeddings and all vocab embeddings
    # Shape: [batch_size, vocab_size]
    # Using efficient broadcasting: ||a - b||^2 = ||a||^2 - 2a.b + ||b||^2
    # Or simply torch.cdist for clarity and numerical stability on CPU
    distances = torch.cdist(noisy_embedding, model_embedding_matrix, p=2)

    # Find the index of the minimum distance for each item in the batch
    # Shape: [batch_size]
    perturbed_token_ids = torch.argmin(distances, dim=1)

    # Retrieve the actual embeddings of the nearest tokens
    # Shape: [batch_size, hidden_dim]
    perturbed_embeddings = model_embedding_matrix[perturbed_token_ids]

    logger.debug(
        f"Injected noise (sigma={sigma}) and projected {batch_size} embeddings. "
        f"Unique tokens selected: {len(torch.unique(perturbed_token_ids))}"
    )

    return perturbed_token_ids, perturbed_embeddings
