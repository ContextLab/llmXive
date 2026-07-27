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
        Tuple[torch.Tensor, torch.Tensor]: (perturbed_token_ids, perturbed_embeddings)
    """
    effective_vocab = tokenizer_vocab_size if tokenizer_vocab_size is not None else model_embedding_matrix.shape[0]
    valid_model_embeddings = model_embedding_matrix[:effective_vocab]

    perturbed_token_ids_list = []
    perturbed_embeddings_list = []

    # Iterate over batch and sequence length (Scalar Loop - Slow)
    for batch_idx in range(embeddings.shape[0]):
        batch_tokens = []
        batch_embs = []
        for seq_idx in range(embeddings.shape[1]):
            token_emb = embeddings[batch_idx, seq_idx]
            
            # Inject noise
            noise = torch.normal(0.0, sigma, size=token_emb.shape, device=token_emb.device)
            perturbed_emb = token_emb + noise
            
            # Find nearest token (Scalar Loop over Vocab - Slow)
            min_dist = float('inf')
            nearest_idx = 0
            for vocab_idx in range(effective_vocab):
                dist = torch.norm(perturbed_emb - valid_model_embeddings[vocab_idx])
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = vocab_idx
            
            batch_tokens.append(nearest_idx)
            batch_embs.append(valid_model_embeddings[nearest_idx])
        
        perturbed_token_ids_list.append(torch.tensor(batch_tokens))
        perturbed_embeddings_list.append(torch.stack(batch_embs))

    perturbed_token_ids = torch.stack(perturbed_token_ids_list)
    perturbed_embeddings = torch.stack(perturbed_embeddings_list)

    return perturbed_token_ids, perturbed_embeddings
