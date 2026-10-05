import numpy as np
from typing import List, Optional
from utils.seeds import get_rng
from utils.logging import get_logger

def inject_noise(confidence: float, sigma: float = 0.05, rng: Optional[np.random.Generator] = None) -> float:
    """
    Injects Gaussian noise into a confidence score.
    Clamps result to [0.0, 1.0].
    """
    if rng is None:
        rng = get_rng(42) # Fallback, should always be passed in loops

    noise = rng.normal(0.0, sigma)
    noisy_conf = confidence + noise
    return float(np.clip(noisy_conf, 0.0, 1.0))

def inject_gaussian_noise(confidence: float, sigma: float = 0.05, rng: Optional[np.random.Generator] = None) -> float:
    """Alias for inject_noise."""
    return inject_noise(confidence, sigma, rng)

def apply_noise_to_batch(confidences: List[float], sigma: float = 0.05, rng: Optional[np.random.Generator] = None) -> List[float]:
    """Applies noise to a batch of confidence scores."""
    return [inject_noise(c, sigma, rng) for c in confidences]
