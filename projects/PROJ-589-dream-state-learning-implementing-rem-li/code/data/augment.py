"""
Data augmentation module for Dream-State Learning.

Implements Denoising AutoEncoder (DAE) masking logic consistent with BERT.
Provides functions to randomly mask tokens in input sequences for the dream phase.
"""
import random
from typing import List, Tuple, Optional
import numpy as np

# Constants for DAE masking
# Moderate mask rate as specified in task description
DEFAULT_MASK_RATE = 0.15
# BERT-style masking probabilities
PROB_REPLACE_WITH_MASK = 0.80
PROB_REPLACE_WITH_RANDOM = 0.10
PROB_KEEP_ORIGINAL = 0.10

# Special tokens (assuming standard BERT tokenization)
MASK_TOKEN_ID = 103  # [MASK]
PAD_TOKEN_ID = 0     # [PAD]
CLS_TOKEN_ID = 101   # [CLS]
SEP_TOKEN_ID = 102   # [SEP]

def apply_dae_mask(
    input_ids: List[int],
    mask_rate: float = DEFAULT_MASK_RATE,
    seed: Optional[int] = None
) -> Tuple[List[int], List[int], List[int]]:
    """
    Apply DAE masking to a sequence of token IDs.
    
    Implements BERT-style masking:
    - 80% of selected tokens are replaced with [MASK]
    - 10% are replaced with a random token from the vocabulary
    - 10% are kept unchanged (to prevent model from relying solely on [MASK])
    
    Args:
        input_ids: List of token IDs representing the input sequence
        mask_rate: Probability of masking each token (default: 0.15)
        seed: Random seed for reproducibility (optional)
    
    Returns:
        Tuple of (masked_ids, labels, mask_positions):
        - masked_ids: Input sequence with selected tokens masked
        - labels: Original token IDs for masked positions, -100 for non-masked
        - mask_positions: Boolean list indicating which positions were masked
    
    Raises:
        ValueError: If input_ids is empty or mask_rate is invalid
    """
    if not input_ids:
        raise ValueError("input_ids cannot be empty")
    
    if not 0.0 < mask_rate < 1.0:
        raise ValueError(f"mask_rate must be between 0 and 1, got {mask_rate}")
    
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    num_tokens = len(input_ids)
    num_to_mask = max(1, int(num_tokens * mask_rate))
    
    # Select random positions to mask, avoiding special tokens if possible
    # We'll mask any token except CLS and SEP for better learning
    special_ids = {CLS_TOKEN_ID, SEP_TOKEN_ID, PAD_TOKEN_ID}
    maskable_positions = [i for i in range(num_tokens) if input_ids[i] not in special_ids]
    
    # If all tokens are special, mask everything (edge case)
    if not maskable_positions:
        maskable_positions = list(range(num_tokens))
    
    # Randomly select positions to mask
    positions_to_mask = random.sample(maskable_positions, min(num_to_mask, len(maskable_positions)))
    
    # Initialize outputs
    masked_ids = input_ids.copy()
    labels = [-100] * num_tokens  # -100 is standard for ignored positions in loss calculation
    mask_positions = [False] * num_tokens
    
    # Get vocabulary size for random token replacement
    # We'll use a reasonable upper bound; in practice this would come from the tokenizer
    vocab_size = max(input_ids) + 1000  # Heuristic upper bound
    
    for pos in positions_to_mask:
        mask_positions[pos] = True
        labels[pos] = input_ids[pos]  # Store original token for loss calculation
        
        # Apply masking strategy
        rand_val = random.random()
        if rand_val < PROB_REPLACE_WITH_MASK:
            # Replace with [MASK] token
            masked_ids[pos] = MASK_TOKEN_ID
        elif rand_val < PROB_REPLACE_WITH_MASK + PROB_REPLACE_WITH_RANDOM:
            # Replace with random token
            masked_ids[pos] = random.randint(0, vocab_size - 1)
        else:
            # Keep original token (10% chance)
            pass  # masked_ids[pos] remains unchanged
    
    return masked_ids, labels, mask_positions

def create_dae_batch(
    batch_input_ids: List[List[int]],
    mask_rate: float = DEFAULT_MASK_RATE,
    seed: Optional[int] = None
) -> Tuple[List[List[int]], List[List[int]], List[List[bool]]]:
    """
    Apply DAE masking to a batch of input sequences.
    
    Args:
        batch_input_ids: List of token ID sequences
        mask_rate: Probability of masking each token (default: 0.15)
        seed: Random seed for reproducibility (optional)
    
    Returns:
        Tuple of (masked_batch, labels_batch, mask_positions_batch):
        - masked_batch: List of masked sequences
        - labels_batch: List of label sequences for loss calculation
        - mask_positions_batch: List of boolean mask position indicators
    """
    if not batch_input_ids:
        return [], [], []
    
    if seed is not None:
        # Use different seeds for each sample in the batch
        base_seed = seed
    else:
        base_seed = None
    
    masked_batch = []
    labels_batch = []
    mask_positions_batch = []
    
    for i, input_ids in enumerate(batch_input_ids):
        current_seed = base_seed + i if base_seed is not None else None
        masked, labels, mask_positions = apply_dae_mask(
            input_ids, 
            mask_rate=mask_rate, 
            seed=current_seed
        )
        masked_batch.append(masked)
        labels_batch.append(labels)
        mask_positions_batch.append(mask_positions)
    
    return masked_batch, labels_batch, mask_positions_batch

def calculate_mask_statistics(
    input_ids: List[int],
    mask_rate: float = DEFAULT_MASK_RATE,
    seed: Optional[int] = None
) -> dict:
    """
    Calculate statistics about the masking operation for logging/debugging.
    
    Args:
        input_ids: List of token IDs
        mask_rate: Probability of masking each token
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing masking statistics
    """
    masked_ids, labels, mask_positions = apply_dae_mask(
        input_ids, 
        mask_rate=mask_rate, 
        seed=seed
    )
    
    num_masked = sum(mask_positions)
    num_tokens = len(input_ids)
    actual_rate = num_masked / num_tokens if num_tokens > 0 else 0.0
    
    # Count masking strategies used
    mask_count = 0
    random_count = 0
    unchanged_count = 0
    
    for i, pos in enumerate(mask_positions):
        if pos:
            if masked_ids[i] == MASK_TOKEN_ID:
                mask_count += 1
            elif masked_ids[i] == input_ids[i]:
                unchanged_count += 1
            else:
                random_count += 1
    
    return {
        "total_tokens": num_tokens,
        "num_masked": num_masked,
        "actual_mask_rate": actual_rate,
        "target_mask_rate": mask_rate,
        "mask_strategy_counts": {
            "replaced_with_mask": mask_count,
            "replaced_with_random": random_count,
            "kept_unchanged": unchanged_count
        },
        "strategy_percentages": {
            "mask": (mask_count / num_masked * 100) if num_masked > 0 else 0.0,
            "random": (random_count / num_masked * 100) if num_masked > 0 else 0.0,
            "unchanged": (unchanged_count / num_masked * 100) if num_masked > 0 else 0.0
        }
    }