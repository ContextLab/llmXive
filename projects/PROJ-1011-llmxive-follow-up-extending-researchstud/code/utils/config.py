import os
import random
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
from utils.logging_config import log_model_switch, log_memory_error, log_fallback_success, log_fallback_failure

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
    return {
        "model_name": "all-MiniLM-L6-v2",
        "quantized": True,
        "max_memory_gb": 7.0
    }

def select_model_on_memory_error(
    original_model: str,
    required_memory_gb: float,
    available_memory_gb: float
) -> Tuple[str, bool]:
    """
    Select a fallback model if memory constraints are hit.
    Returns (selected_model, success_flag).
    """
    logger = logging.getLogger("model_fallback")
    
    # Log the memory error
    log_memory_error(original_model, available_memory_gb, required_memory_gb)
    
    # Define fallback models in order of preference (smaller to larger)
    fallback_models = [
        ("all-distilroberta-v1", 2.0),  # Smallest, fastest
        ("all-MiniLM-L6-v2", 4.0),      # Medium size
    ]
    
    for model_name, memory_requirement in fallback_models:
        if model_name != original_model and memory_requirement <= available_memory_gb:
            log_model_switch(original_model, model_name, f"Memory constraint: required {required_memory_gb}GB, available {available_memory_gb}GB")
            log_fallback_success(original_model, model_name)
            return model_name, True
    
    # If no suitable fallback found
    error_msg = f"No suitable fallback model found. Required: {required_memory_gb}GB, Available: {available_memory_gb}GB"
    log_fallback_failure(original_model, error_msg)
    raise MemoryError(error_msg)
