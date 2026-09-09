"""
Data augmentation utilities for Dream-State Learning.

Implements BERT-style masking strategies for the Denoising Autoencoder (DAE)
used in the dream phase of the training cycle.
"""
import random
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

# Import from local config to ensure consistency
# Note: We define the constant here for immediate use in augmentation logic,
# but it is also referenced in config.py for hyperparameter management.
MASK_RATE = 0.15

# Constants for masking strategy (BERT-style)
MASK_TOKEN_ID = 103  # Standard [MASK] token ID for DistilBERT/TinyLlama
RANDOM_REPLACE_RATE = 0.1  # 10% of masked tokens are replaced with random tokens
KEEP_ORIGINAL_RATE = 0.1   # 10% of masked tokens remain unchanged


def apply_dae_mask(
    input_ids: List[int],
    mask_rate: float = MASK_RATE,
    mask_token_id: int = MASK_TOKEN_ID,
    random_replace_rate: float = RANDOM_REPLACE_RATE,
    keep_original_rate: float = KEEP_ORIGINAL_RATE,
    vocab_size: Optional[int] = None,
    seed: Optional[int] = None
) -> Tuple[List[int], List[bool]]:
    """
    Apply BERT-style masking to a sequence of token IDs.
    
    This implements the Denoising Autoencoder input generation for the dream phase.
    A fraction of tokens are masked according to:
    - 80% replaced with [MASK] token
    - 10% replaced with a random token from the vocabulary
    - 10% kept as original (to prevent the model from learning to always copy)
    
    Args:
        input_ids: List of token IDs to mask.
        mask_rate: Probability of masking each token (default 0.15).
        mask_token_id: The ID of the [MASK] token.
        random_replace_rate: Fraction of masked tokens to replace randomly (default 0.1).
        keep_original_rate: Fraction of masked tokens to leave unchanged (default 0.1).
        vocab_size: Size of vocabulary (required for random replacement).
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (masked_input_ids, mask_positions) where mask_positions is a 
        boolean list indicating which positions were masked.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    if not input_ids:
        return [], []
        
    length = len(input_ids)
    mask_positions = [False] * length
    masked_ids = input_ids.copy()
    
    # Determine which positions to mask
    num_masks = max(1, int(length * mask_rate))
    mask_indices = random.sample(range(length), num_masks)
    
    for idx in mask_indices:
        mask_positions[idx] = True
        roll = random.random()
        
        if roll < (1.0 - random_replace_rate - keep_original_rate):
            # Replace with [MASK] token (80% of masks)
            masked_ids[idx] = mask_token_id
        elif roll < (1.0 - keep_original_rate):
            # Replace with random token (10% of masks)
            if vocab_size is None:
                # Fallback: use a reasonable default if vocab_size not provided
                # This should ideally be passed from config or model
                vocab_size = 30522  # DistilBERT vocab size
            masked_ids[idx] = random.randint(0, vocab_size - 1)
        else:
            # Keep original (10% of masks)
            pass  # masked_ids[idx] remains unchanged
                
    return masked_ids, mask_positions


def create_dae_batch(
    batch_input_ids: List[List[int]],
    mask_rate: float = MASK_RATE,
    seed: Optional[int] = None
) -> Tuple[List[List[int]], List[List[bool]], List[List[int]]]:
    """
    Create a DAE training batch from a list of input sequences.
    
    Args:
        batch_input_ids: List of token ID sequences.
        mask_rate: Masking probability.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (masked_inputs, mask_positions, original_ids)
        - masked_inputs: Inputs with [MASK] tokens applied
        - mask_positions: Boolean masks indicating which tokens were masked
        - original_ids: The original unmasked inputs (targets for reconstruction)
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    masked_batch = []
    mask_positions_batch = []
    original_batch = []
    
    for input_ids in batch_input_ids:
        masked_ids, mask_positions = apply_dae_mask(
            input_ids, 
            mask_rate=mask_rate,
            seed=seed if seed is not None else random.randint(0, 2**31)
        )
        masked_batch.append(masked_ids)
        mask_positions_batch.append(mask_positions)
        original_batch.append(input_ids)
        
    return masked_batch, mask_positions_batch, original_batch


def calculate_mask_statistics(
    input_ids: List[int],
    mask_rate: float = MASK_RATE
) -> Dict[str, Any]:
    """
    Calculate statistics about expected masking for a given sequence.
    
    Args:
        input_ids: Input token sequence.
        mask_rate: Expected masking rate.
        
    Returns:
        Dictionary containing:
        - total_tokens: Length of input
        - expected_masks: Expected number of masked tokens
        - mask_rate: Actual mask rate used
    """
    total_tokens = len(input_ids)
    expected_masks = int(total_tokens * mask_rate)
    
    return {
        "total_tokens": total_tokens,
        "expected_masks": expected_masks,
        "mask_rate": mask_rate,
        "min_masks": max(1, expected_masks - 1),
        "max_masks": expected_masks + 1
    }