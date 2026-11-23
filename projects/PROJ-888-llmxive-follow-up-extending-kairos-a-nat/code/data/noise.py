"""
Noise injection module to add Gaussian noise to discrete state vectors.

This module implements the noise injection step of the data construction pipeline.
It takes quantized discrete state vectors, adds Gaussian noise with a configurable
standard deviation, and clamps the results back to valid discrete bins.

Per project constraints:
- No synthetic fallbacks are used.
- All operations are performed in-place on the provided data structure.
- Clamping ensures values remain within [0, 2^bits - 1].
"""
import sys
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging import get_logger
from data.schema import clamp_to_bin

logger = get_logger(__name__)

def inject_noise(
    data: List[Dict[str, Any]],
    std_dev: float,
    quantization_level: int
) -> List[Dict[str, Any]]:
    """
    Inject Gaussian noise into discrete state vectors and clamp to valid bins.
    
    This function processes a list of episodes, each containing a 'state_vector'.
    It adds Gaussian noise with the specified standard deviation to each element
    of the state vector, rounds to the nearest integer, and then clamps the result
    to the valid range [0, 2^quantization_level - 1].
    
    Args:
        data: List of dictionaries, each containing a 'state_vector' key with
              a list of integer values representing the quantized state.
        std_dev: Standard deviation of the Gaussian noise to inject. Must be > 0.
        quantization_level: Number of bits used for quantization (e.g., 4, 8, 16).
                           Determines the number of bins: 2^bits.
                           
    Returns:
        List of dictionaries with the same structure as input, but with
        'state_vector' values modified to include injected noise and clamped
        to valid discrete bins.
        
    Raises:
        ValueError: If std_dev is negative or quantization_level is invalid.
        TypeError: If input data is not in the expected format.
    """
    if std_dev < 0:
        raise ValueError(f"std_dev must be non-negative, got {std_dev}")
    if quantization_level <= 0:
        raise ValueError(f"quantization_level must be positive, got {quantization_level}")
        
    num_bins = 2 ** quantization_level
    noisy_data = []
    
    logger.info(f"Injecting noise (std={std_dev}) into {len(data)} episodes...")
    logger.debug(f"Quantization level: {quantization_level} bits -> {num_bins} bins")
    
    for idx, episode in enumerate(data):
        if "state_vector" not in episode:
            logger.warning(f"Episode {idx} missing 'state_vector', skipping")
            noisy_data.append(episode)
            continue
            
        state_vec = np.array(episode["state_vector"], dtype=np.float64)
        
        if state_vec.size == 0:
            logger.debug(f"Episode {idx} has empty state vector")
            noisy_data.append(episode)
            continue
        
        # Generate Gaussian noise with mean=0 and std=std_dev
        noise = np.random.normal(0, std_dev, size=state_vec.shape)
        
        # Add noise to the state vector
        noisy_vec = state_vec + noise
        
        # Round to nearest integer (discrete bins)
        noisy_vec = np.round(noisy_vec)
        
        # Clamp to valid discrete bins [0, num_bins - 1]
        noisy_vec = clamp_to_bin(noisy_vec, bits=quantization_level)
        
        # Convert back to list and update episode
        episode["state_vector"] = noisy_vec.astype(int).tolist()
        noisy_data.append(episode)
        
        # Log progress periodically
        if (idx + 1) % 10 == 0:
            logger.debug(f"Processed {idx + 1}/{len(data)} episodes")
    
    logger.info(f"Successfully injected noise into {len(noisy_data)} episodes")
    return noisy_data