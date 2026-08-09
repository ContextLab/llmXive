"""
Noise injection utilities for simulation variance (FR-008).
"""
import numpy as np
from utils.seeds import get_rng
from utils.logging import get_logger

logger = get_logger(__name__)

def inject_gaussian_noise(confidence: float, sigma: float = 0.05) -> float:
    """
    Injects Gaussian noise into a confidence score.
    
    Args:
        confidence: The original confidence score (0.0 to 1.0).
        sigma: Standard deviation of the Gaussian noise.
        
    Returns:
        Noisy confidence score, clamped to [0.0, 1.0].
    """
    rng = get_rng()
    noise = rng.normal(0, sigma)
    noisy_value = confidence + noise
    
    # Clamp to valid probability range
    return max(0.0, min(1.0, noisy_value))

def apply_noise_to_batch(confidences: list, sigma: float = 0.05) -> list:
    """
    Applies Gaussian noise to a batch of confidence scores.
    
    Args:
        confidences: List of confidence scores.
        sigma: Standard deviation of the Gaussian noise.
        
    Returns:
        List of noisy confidence scores.
    """
    return [inject_gaussian_noise(c, sigma) for c in confidences]
