import os
import random
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
from utils.logging_config import log_model_switch, log_memory_error, log_fallback_success, log_fallback_failure

# Configuration constants for model fallback
# These are read from environment variables with safe defaults
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
FALLBACK_EMBEDDING_MODEL = os.getenv("FALLBACK_EMBEDDING_MODEL", "all-distilroberta-v1")
DEFAULT_MAX_MEMORY_GB = 7.0

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_environment_hash() -> str:
    """Get a hash of the current environment configuration."""
    env_vars = {
        'PYTHON_VERSION': os.getenv('PYTHON_VERSION', 'unknown'),
        'NUM_THREADS': os.getenv('OMP_NUM_THREADS', '1'),
    }
    env_str = str(sorted(env_vars.items()))
    return hashlib.sha256(env_str.encode()).hexdigest()[:16]

def validate_seed(seed: int) -> bool:
    """Validate that the seed is a positive integer."""
    return isinstance(seed, int) and seed > 0

def get_model_config() -> Dict[str, Any]:
    """Get the default model configuration."""
    # Use environment variable for fallback model if set, otherwise default
    fallback_model = os.getenv("FALLBACK_EMBEDDING_MODEL", FALLBACK_EMBEDDING_MODEL)
    
    return {
        "model_name": os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        "fallback_model_name": fallback_model,
        "quantized": True,
        "max_memory_gb": float(os.getenv("MAX_MEMORY_GB", DEFAULT_MAX_MEMORY_GB))
    }

def select_model_on_memory_error(
    original_model: str,
    required_memory_gb: float,
    available_memory_gb: float
) -> Tuple[str, bool]:
    """
    Select a fallback model if memory constraints are hit.
    Returns (selected_model, success_flag).
    
    This implementation uses the configurable FALLBACK_EMBEDDING_MODEL from config
    rather than hardcoding specific model names, allowing runtime configuration
    of the fallback strategy.
    """
    logger = logging.getLogger("model_fallback")
    
    # Log the memory error
    log_memory_error(original_model, available_memory_gb, required_memory_gb)
    
    # Get the configured fallback model
    fallback_model = os.getenv("FALLBACK_EMBEDDING_MODEL", FALLBACK_EMBEDDING_MODEL)
    
    # Estimate memory requirement for fallback model (simplified heuristic)
    # In production, this would be based on actual model metadata
    fallback_memory_estimate = 2.0  # GB for smaller models like all-distilroberta-v1
    
    if fallback_memory_estimate <= available_memory_gb:
        log_model_switch(
            original_model, 
            fallback_model, 
            f"Memory constraint: required {required_memory_gb}GB, available {available_memory_gb}GB"
        )
        log_fallback_success(original_model, fallback_model)
        return fallback_model, True
    
    # If no suitable fallback found
    error_msg = (
        f"No suitable fallback model found. "
        f"Original: {original_model} ({required_memory_gb}GB), "
        f"Fallback: {fallback_model} (estimated {fallback_memory_estimate}GB), "
        f"Available: {available_memory_gb}GB"
    )
    log_fallback_failure(original_model, error_msg)
    raise MemoryError(error_msg)