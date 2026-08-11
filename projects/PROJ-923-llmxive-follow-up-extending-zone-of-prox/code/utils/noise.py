"""
Noise injection utilities for simulation variance (FR-008).

This module implements per-step Gaussian noise injection into confidence scores
to ensure statistical variance in simulation results as required by FR-008.
"""
import numpy as np
from typing import List

from utils.seeds import get_rng
from utils.logging import get_logger

logger = get_logger(__name__)

def inject_noise(confidence: float, sigma: float = 0.05) -> float:
    """
    Injects Gaussian noise into a confidence score per step.
    
    This function implements the core noise injection mechanism required by FR-008.
    It adds Gaussian noise with mean 0 and standard deviation `sigma` to the
    input confidence score, then clamps the result to the valid probability range [0.0, 1.0].
    
    Args:
        confidence: The original confidence score (0.0 to 1.0).
        sigma: Standard deviation of the Gaussian noise (default: 0.05).
        
    Returns:
        Noisy confidence score, clamped to [0.0, 1.0].
        
    Raises:
        ValueError: If confidence is outside the valid range [0.0, 1.0].
    """
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"Confidence must be in range [0.0, 1.0], got {confidence}")
        
    rng = get_rng()
    noise = rng.normal(0.0, sigma)
    noisy_value = confidence + noise
    
    # Clamp to valid probability range
    return max(0.0, min(1.0, noisy_value))

def inject_gaussian_noise(confidence: float, sigma: float = 0.05) -> float:
    """
    Alias for inject_noise to maintain backward compatibility with existing imports.
    
    Injects Gaussian noise into a confidence score.
    
    Args:
        confidence: The original confidence score (0.0 to 1.0).
        sigma: Standard deviation of the Gaussian noise.
        
    Returns:
        Noisy confidence score, clamped to [0.0, 1.0].
    """
    return inject_noise(confidence, sigma)

def apply_noise_to_batch(confidences: List[float], sigma: float = 0.05) -> List[float]:
    """
    Applies Gaussian noise to a batch of confidence scores.
    
    Args:
        confidences: List of confidence scores (each in range [0.0, 1.0]).
        sigma: Standard deviation of the Gaussian noise.
        
    Returns:
        List of noisy confidence scores, each clamped to [0.0, 1.0].
    """
    return [inject_noise(c, sigma) for c in confidences]