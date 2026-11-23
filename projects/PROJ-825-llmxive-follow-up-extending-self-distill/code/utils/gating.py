"""
Gating utilities for calculating token entropy and context stability.

Implements T016 requirements.
"""
import torch
import numpy as np
from typing import List, Optional, Tuple
import math

def calculate_token_entropy(logits: torch.Tensor) -> float:
    """
    Calculate the token entropy (H_t) from logits.
    
    Args:
        logits: Tensor of shape (vocab_size,) or (batch_size, vocab_size).
                
    Returns:
        Entropy value.
    """
    # Convert to probabilities
    probs = torch.softmax(logits, dim=-1)
    
    # Calculate entropy: -sum(p * log(p))
    # Avoid log(0)
    eps = 1e-9
    entropy = -torch.sum(probs * torch.log(probs + eps), dim=-1)
    
    if entropy.dim() > 0:
        return entropy.mean().item()
    return entropy.item()

def calculate_context_stability(
    current_context: torch.Tensor, 
    previous_context: torch.Tensor
) -> float:
    """
    Calculate context stability (S_t) via cosine similarity.
    
    Args:
        current_context: Current context embedding.
        previous_context: Previous context embedding.
        
    Returns:
        Cosine similarity score (0.0 to 1.0).
    """
    # Ensure tensors are on the same device and same dtype
    if current_context.device != previous_context.device:
        current_context = current_context.to(previous_context.device)
        
    # Compute cosine similarity
    similarity = torch.nn.functional.cosine_similarity(
        current_context.unsqueeze(0), 
        previous_context.unsqueeze(0), 
        dim=1
    )
    
    # Return the similarity score (clamped to 0-1 if needed, though cosine is -1 to 1)
    # For stability, we usually want positive correlation.
    score = similarity.item()
    
    # Normalize to 0-1 range if necessary (assuming -1 to 1 input)
    # If the model produces embeddings where -1 is opposite, we might want to shift.
    # But typically for stability, we just want the raw similarity.
    # Let's assume we want a 0-1 metric where 1 is perfectly stable.
    # Cosine similarity is -1 to 1. Let's map to 0-1.
    normalized_score = (score + 1) / 2.0
    
    return max(0.0, min(1.0, normalized_score))

def calculate_gating_score(
    entropy: float, 
    stability: float, 
    alpha: float = 1.0, 
    beta: float = 1.0
) -> float:
    """
    Calculate the final gating score g_t = sigmoid(alpha * H_t + beta * S_t).
    
    Args:
        entropy: Token entropy H_t.
        stability: Context stability S_t.
        alpha: Weight for entropy.
        beta: Weight for stability.
        
    Returns:
        Gating score between 0 and 1.
    """
    # Combine scores
    combined = alpha * entropy + beta * stability
    
    # Apply sigmoid
    # Clamp to prevent overflow
    combined = max(-500, min(500, combined))
    gating_score = 1.0 / (1.0 + math.exp(-combined))
    
    return gating_score
