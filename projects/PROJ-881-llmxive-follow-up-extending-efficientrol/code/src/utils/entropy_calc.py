"""
Entropy calculation utilities for llmXive research pipeline.

This module provides functions to compute Shannon entropy from probability
distributions, with specific safeguards against numerical instability
(log(0) errors) as required by the project specifications.
"""

import numpy as np
from typing import Union, List, Optional

def compute_shannon_entropy(probs: Union[np.ndarray, List[float]]) -> float:
    """
    Compute the Shannon entropy of a probability distribution.

    Formula: H = -sum(p_i * log(p_i))

    This implementation clamps probability values less than 1e-9 to 1e-9
    BEFORE taking the logarithm to prevent log(0) errors, as required
    by the project specifications for handling high-confidence edge cases.

    Args:
        probs: A probability distribution (1D array or list of floats).
               The values should sum to approximately 1.0.

    Returns:
        float: The Shannon entropy value. Returns 0.0 for empty input
               or if all probabilities are effectively zero after clamping.

    Raises:
        ValueError: If input is empty or contains negative values.
        TypeError: If input is not a list or numpy array.

    Example:
        >>> import numpy as np
        >>> probs = np.array([0.5, 0.5])
        >>> compute_shannon_entropy(probs)
        0.693147...
    """
    # Convert to numpy array if list
    if isinstance(probs, list):
        probs = np.array(probs, dtype=np.float64)
    elif not isinstance(probs, np.ndarray):
        raise TypeError(f"Expected list or numpy array, got {type(probs)}")

    # Validate input
    if probs.size == 0:
        return 0.0

    if np.any(probs < 0):
        raise ValueError("Probability values cannot be negative")

    # CRITICAL: Clamp probabilities < 1e-9 to 1e-9 BEFORE log
    # This prevents log(0) errors for high-confidence predictions
    clamped_probs = np.where(probs < 1e-9, 1e-9, probs)

    # Compute entropy: -sum(p * log(p))
    # Using natural logarithm (base e) as standard for Shannon entropy
    entropy = -np.sum(clamped_probs * np.log(clamped_probs))

    return float(entropy)


def compute_batch_entropy(
    probs_batch: Union[np.ndarray, List[List[float]]]
) -> List[float]:
    """
    Compute Shannon entropy for a batch of probability distributions.

    Args:
        probs_batch: A 2D array or list of lists, where each row is a
                     probability distribution.

    Returns:
        List[float]: A list of entropy values, one for each distribution
                     in the batch.

    Example:
        >>> batch = [[0.5, 0.5], [0.9, 0.1]]
        >>> compute_batch_entropy(batch)
        [0.693147..., 0.325082...]
    """
    if isinstance(probs_batch, list):
        probs_batch = np.array(probs_batch, dtype=np.float64)
    elif not isinstance(probs_batch, np.ndarray):
        raise TypeError(f"Expected 2D list or numpy array, got {type(probs_batch)}")

    if probs_batch.ndim != 2:
        raise ValueError(f"Expected 2D input, got {probs_batch.ndim}D")

    entropies = []
    for probs in probs_batch:
        entropies.append(compute_shannon_entropy(probs))

    return entropies


def compute_layer_wise_entropy(
    logits: Union[np.ndarray, List[List[float]]]
) -> List[float]:
    """
    Compute Shannon entropy from raw logits by first converting to
    probabilities via softmax.

    This is useful for analyzing model confidence at different layers
    without manual softmax conversion.

    Args:
        logits: A 2D array or list of lists, where each row contains
                raw logits for a vocabulary distribution.

    Returns:
        List[float]: A list of entropy values for each logit vector.

    Example:
        >>> logits = [[2.0, 1.0, 0.0], [0.1, 0.2, 0.3]]
        >>> compute_layer_wise_entropy(logits)
        [...]
    """
    if isinstance(logits, list):
        logits = np.array(logits, dtype=np.float64)
    elif not isinstance(logits, np.ndarray):
        raise TypeError(f"Expected 2D list or numpy array, got {type(logits)}")

    if logits.ndim != 2:
        raise ValueError(f"Expected 2D input, got {logits.ndim}D")

    # Apply softmax to convert logits to probabilities
    # Subtract max for numerical stability
    exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    return compute_batch_entropy(probs)
