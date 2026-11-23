"""
Quantization module to convert continuous data to discrete integers.

This module implements the quantization logic for the Kairos discrete world model stack,
converting continuous HDF5 state vectors into discrete integer representations
based on configurable bit-depths (4, 8, 16) as per FR-001.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Union, Optional
import numpy as np
import h5py

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging import get_logger, QuantizationError
from data.schema import clamp_to_bin, validate_quantization_level, QuantizationLevel

logger = get_logger(__name__)

def quantize_dataset(
    input_path: Path,
    quantization_level: int,
    subset_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Quantize continuous data from an HDF5 file to discrete integers.
    
    This function reads HDF5 episodes, extracts state vectors (observations),
    and converts them to discrete integer values within the range [0, 2^bits - 1].
    It strictly enforces bin clamping to prevent out-of-bounds values.
    
    Args:
        input_path: Path to the input HDF5 file containing LIBERO data.
        quantization_level: Number of bits (4, 8, or 16) for quantization.
        subset_size: Optional limit on the number of episodes to process.
        
    Returns:
        List of dictionaries containing:
            - episode_id: Integer identifier for the episode.
            - state_vector: List of quantized integer values.
            - action_vector: List of original action values (floats).
            
    Raises:
        QuantizationError: If quantization fails or input is invalid.
        FileNotFoundError: If the input HDF5 file does not exist.
    """
    # Validate quantization level against allowed values (4, 8, 16)
    validate_quantization_level(quantization_level)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Starting quantization of {input_path} to {quantization_level}-bit...")
    
    try:
        with h5py.File(input_path, 'r') as f:
            episodes = []
            episode_count = 0
            
            # Iterate over dataset keys
            for key in sorted(f.keys()):
                if not key.startswith("episode_"):
                    continue
                
                episode_count += 1
                if subset_size and episode_count > subset_size:
                    logger.info(f"Reached subset limit of {subset_size} episodes.")
                    break
                
                ep_group = f[key]
                
                # Extract observations and actions
                obs = None
                acts = None
                
                if "observations" in ep_group:
                    obs = ep_group["observations"][()]
                if "actions" in ep_group:
                    acts = ep_group["actions"][()]
                
                if obs is None or acts is None:
                    logger.warning(f"Skipping episode {key} due to missing observations or actions.")
                    continue
                
                # Ensure arrays are numpy arrays
                if not isinstance(obs, np.ndarray):
                    obs = np.array(obs)
                if not isinstance(acts, np.ndarray):
                    acts = np.array(acts)
                
                # Flatten multi-dimensional observations if necessary
                # The state vector is expected to be 1D for quantization
                if obs.ndim > 1:
                    obs = obs.flatten()
                if acts.ndim > 1:
                    acts = acts.flatten()
                
                # Perform quantization on the observation (state vector)
                quantized_vector = _quantize_array(obs, quantization_level)
                
                episodes.append({
                    "episode_id": int(key.split("_")[1]),
                    "state_vector": quantized_vector.tolist(),
                    "action_vector": acts.tolist()
                })
            
            logger.info(f"Successfully quantized {len(episodes)} episodes.")
            return episodes
            
    except Exception as e:
        logger.error(f"Quantization process failed: {e}", exc_info=True)
        raise QuantizationError(f"Failed to quantize data: {e}") from e

def _quantize_array(arr: np.ndarray, bits: int) -> np.ndarray:
    """
    Quantize a numpy array to discrete integer bins.
    
    This function normalizes the input array to [0, 1] based on its min/max,
    maps it to discrete bins, and strictly clamps the result to the valid range
    [0, 2^bits - 1] to ensure no out-of-bounds values occur.
    
    Args:
        arr: Input continuous numpy array.
        bits: Number of bits for quantization (determines bin count).
        
    Returns:
        Numpy array of integers representing quantized values.
        
    Raises:
        QuantizationError: If quantization logic fails.
    """
    try:
        # Determine min and max for normalization
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        
        # Handle constant arrays (zero variance)
        if max_val == min_val:
            logger.warning("Input array has zero variance. Returning zeros.")
            num_bins = 2 ** bits
            return np.zeros_like(arr, dtype=np.int32)
        
        # Normalize to [0, 1] range
        normalized = (arr - min_val) / (max_val - min_val)
        
        # Calculate number of bins
        num_bins = 2 ** bits
        
        # Map to bins [0, num_bins - 1]
        # Using floor to map continuous [0, 1) to discrete bins
        # Note: 1.0 maps to num_bins, which we clamp below
        quantized = np.floor(normalized * num_bins).astype(np.int32)
        
        # STRICT CLAMPING: Ensure values are within [0, num_bins - 1]
        # This handles edge cases where normalized == 1.0 exactly
        quantized = np.clip(quantized, 0, num_bins - 1)
        
        # Final validation using schema utility
        # This acts as a sanity check before returning
        validated = clamp_to_bin(quantized, bits)
        
        return validated
        
    except Exception as e:
        logger.error(f"Array quantization failed: {e}")
        raise QuantizationError(f"Failed to quantize array: {e}") from e