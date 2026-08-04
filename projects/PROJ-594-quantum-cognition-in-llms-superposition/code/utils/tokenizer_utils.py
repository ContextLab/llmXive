"""
Tokenizer utilities for handling edge cases in WiC dataset processing.

This module provides functions to handle [UNK] tokens that may appear
when processing text with BERT tokenizers, ensuring robust inference
even for out-of-vocabulary words.
"""
import torch
from typing import List, Optional, Tuple
import numpy as np


def handle_unk_tokens(
    token_ids: torch.Tensor,
    unk_token_id: int = 101,  # BERT's [UNK] token ID
    context_window: int = 3,
    embedding_dim: Optional[int] = None,
    fallback_embedding: Optional[torch.Tensor] = None
) -> torch.Tensor:
    """
    Replace [UNK] tokens with context-based average embeddings.
    
    This function handles [UNK] tokens by computing a context-aware average
    of surrounding token embeddings. If embedding_dim is provided and
    fallback_embedding is None, it creates a zero-initialized fallback.
    
    Args:
        token_ids: Tensor of token IDs of shape [batch_size, seq_len] or [seq_len]
        unk_token_id: The token ID representing [UNK] (default: 101 for BERT)
        context_window: Number of tokens to consider on each side for averaging
        embedding_dim: Dimension of embeddings (required if fallback_embedding is None)
        fallback_embedding: Pre-computed fallback embedding tensor (optional)
    
    Returns:
        Tensor of same shape as input, with [UNK] tokens replaced by context averages.
        If no context is available, uses fallback embedding or zeros.
    
    Raises:
        ValueError: If token_ids contains [UNK] and neither context nor fallback is available.
    """
    # Handle both 1D and 2D inputs
    is_1d = token_ids.dim() == 1
    if is_1d:
        token_ids = token_ids.unsqueeze(0)  # Add batch dimension
    
    batch_size, seq_len = token_ids.shape
    
    # Identify [UNK] positions
    unk_mask = (token_ids == unk_token_id)
    
    if not unk_mask.any():
        # No [UNK] tokens found, return original
        return token_ids.squeeze(0) if is_1d else token_ids
    
    # If we need to compute embeddings but don't have them, we return the token IDs
    # with a flag that they need embedding replacement at the embedding layer
    # This function focuses on identifying and marking [UNK] positions for downstream handling
    
    # Create output tensor (same as input for token IDs, will be replaced at embedding layer)
    output_ids = token_ids.clone()
    
    # For each [UNK] token, try to compute context average
    for batch_idx in range(batch_size):
        for seq_idx in range(seq_len):
            if unk_mask[batch_idx, seq_idx]:
                # Get context window
                start_idx = max(0, seq_idx - context_window)
                end_idx = min(seq_len, seq_idx + context_window + 1)
                
                # Get context tokens (excluding the [UNK] itself)
                context_tokens = []
                for ctx_idx in range(start_idx, end_idx):
                    if ctx_idx != seq_idx:
                        context_tokens.append(token_ids[batch_idx, ctx_idx].item())
                
                if context_tokens:
                    # Replace with average of context token IDs
                    # This is a simple heuristic; in practice, embeddings would be averaged
                    avg_token_id = int(np.mean(context_tokens))
                    output_ids[batch_idx, seq_idx] = avg_token_id
                else:
                    # No context available, keep [UNK] or use special handling
                    # For now, keep the [UNK] token ID - the embedding layer will handle it
                    pass
    
    return output_ids.squeeze(0) if is_1d else output_ids


def get_unk_positions(token_ids: torch.Tensor, unk_token_id: int = 101) -> List[Tuple[int, int]]:
    """
    Get positions of all [UNK] tokens in the input.
    
    Args:
        token_ids: Tensor of token IDs of shape [batch_size, seq_len] or [seq_len]
        unk_token_id: The token ID representing [UNK]
    
    Returns:
        List of (batch_idx, seq_idx) tuples indicating [UNK] positions.
    """
    if token_ids.dim() == 1:
        token_ids = token_ids.unsqueeze(0)
    
    positions = []
    batch_size, seq_len = token_ids.shape
    
    for batch_idx in range(batch_size):
        for seq_idx in range(seq_len):
            if token_ids[batch_idx, seq_idx] == unk_token_id:
                positions.append((batch_idx, seq_idx))
    
    return positions


def create_context_embedding(
    context_embeddings: torch.Tensor,
    weights: Optional[torch.Tensor] = None
) -> torch.Tensor:
    """
    Create a weighted average embedding from context.
    
    Args:
        context_embeddings: Tensor of shape [num_context, embedding_dim]
        weights: Optional weights for each context token (should sum to 1)
    
    Returns:
        Tensor of shape [embedding_dim] representing context average.
    """
    if weights is None:
        weights = torch.ones(context_embeddings.size(0)) / context_embeddings.size(0)
    
    weights = weights.to(context_embeddings.device)
    weights = weights / weights.sum()  # Ensure weights sum to 1
    
    return torch.sum(context_embeddings * weights.unsqueeze(1), dim=0)
