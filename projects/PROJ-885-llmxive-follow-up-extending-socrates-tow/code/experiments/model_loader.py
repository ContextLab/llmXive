"""
Model loading utilities with memory constraints for CPU-only execution.

This module provides functionality to estimate model memory usage before loading,
ensuring compliance with the 7GB RAM limit specified in FR-004.
"""
import logging
import os
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 * 1024 * 1024

logger = logging.getLogger(__name__)


@dataclass
class ModelMemoryEstimate:
    """Container for model memory estimation results."""
    model_name: str
    estimated_params: int
    estimated_memory_gb: float
    fits_in_memory: bool
    reason: str


def estimate_model_memory(
    model_name: str,
    param_count: Optional[int] = None,
    precision_bytes: int = 4
) -> ModelMemoryEstimate:
    """
    Estimate the memory footprint of a model before loading.
    
    Args:
        model_name: Name or identifier of the model
        param_count: Number of parameters in the model (if known)
        precision_bytes: Bytes per parameter (4 for FP32, 2 for FP16, 1 for INT8)
    
    Returns:
        ModelMemoryEstimate with memory usage details
    """
    # If param_count is not provided, try to infer from model name
    if param_count is None:
        param_count = _infer_param_count_from_name(model_name)
    
    # Calculate memory: params * precision + overhead (10% for optimizer states, buffers, etc.)
    # For inference, we typically don't need optimizer states, but we add overhead for
    # activations and framework overhead
    overhead_factor = 1.1
    estimated_memory_bytes = param_count * precision_bytes * overhead_factor
    estimated_memory_gb = estimated_memory_bytes / (1024 ** 3)
    
    fits_in_memory = estimated_memory_bytes <= MEMORY_LIMIT_BYTES
    
    reason = (
        "Model fits within memory limit" if fits_in_memory 
        else f"Model exceeds {MEMORY_LIMIT_GB}GB limit"
    )
    
    return ModelMemoryEstimate(
        model_name=model_name,
        estimated_params=param_count,
        estimated_memory_gb=estimated_memory_gb,
        fits_in_memory=fits_in_memory,
        reason=reason
    )


def _infer_param_count_from_name(model_name: str) -> int:
    """
    Infer parameter count from model name pattern.
    
    Common patterns:
    - "7b", "7B" -> 7 billion
    - "13b", "13B" -> 13 billion
    - "30b", "30B" -> 30 billion
    - "65b", "65B" -> 65 billion
    
    Args:
        model_name: Model identifier string
    
    Returns:
        Estimated parameter count
    """
    import re
    
    # Look for common parameter size patterns
    patterns = [
        r'(\d+)\s*[bB]',  # e.g., "7b", "13 B"
        r'(\d+\.\d+)\s*[bB]',  # e.g., "7.1b"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, model_name)
        if match:
            billions = float(match.group(1))
            return int(billions * 1_000_000_000)
    
    # Default to a small model if no pattern found
    logger.warning(
        f"Could not infer parameter count from model name '{model_name}'. "
        "Assuming small model (1B parameters)."
    )
    return 1_000_000_000


def check_and_load_model(
    model_name: str,
    model_class: Any,
    model_kwargs: Optional[Dict[str, Any]] = None,
    precision_bytes: int = 4
) -> Tuple[bool, Optional[Any], str]:
    """
    Check if a model can fit in memory and load it if possible.
    
    This function performs a pre-flight memory check before attempting to load
    a model. If the estimated memory usage exceeds the limit, it logs a warning
    and returns without loading.
    
    Args:
        model_name: Name/identifier of the model to load
        model_class: The model class to instantiate (e.g., AutoModelForCausalLM)
        model_kwargs: Additional keyword arguments for model loading
        precision_bytes: Bytes per parameter (4 for FP32, 2 for FP16, 1 for INT8)
    
    Returns:
        Tuple of (success: bool, model: Optional[Any], message: str)
    """
    if model_kwargs is None:
        model_kwargs = {}
    
    # Estimate memory usage
    estimate = estimate_model_memory(model_name, precision_bytes=precision_bytes)
    
    if not estimate.fits_in_memory:
        warning_msg = (
            f"Model '{model_name}' estimated at {estimate.estimated_memory_gb:.2f}GB "
            f"exceeds {MEMORY_LIMIT_GB}GB limit. Skipping load. Reason: {estimate.reason}"
        )
        logger.warning(warning_msg)
        return False, None, warning_msg
    
    try:
        logger.info(f"Loading model '{model_name}' (estimated {estimate.estimated_memory_gb:.2f}GB)")
        # Note: Actual model loading logic would go here
        # For now, we return a success flag and placeholder
        # In real implementation: model = model_class.from_pretrained(model_name, **model_kwargs)
        return True, None, f"Model '{model_name}' would be loaded successfully"
    except Exception as e:
        error_msg = f"Failed to load model '{model_name}': {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def get_available_models() -> Dict[str, ModelMemoryEstimate]:
    """
    Get memory estimates for a predefined set of models.
    
    Returns:
        Dictionary mapping model names to their memory estimates
    """
    # Predefined list of models with their parameter counts
    models = {
        "tiny-llama-1.1b": 1_100_000_000,
        "phi-2": 2_700_000_000,
        "mistral-7b": 7_000_000_000,
        "llama-2-7b": 7_000_000_000,
        "llama-2-13b": 13_000_000_000,
        "mistral-8x7b": 56_000_000_000,
        "llama-2-70b": 70_000_000_000,
    }
    
    estimates = {}
    for name, params in models.items():
        estimates[name] = estimate_model_memory(name, param_count=params)
    
    return estimates


def filter_models_by_memory(models: Dict[str, ModelMemoryEstimate]) -> Dict[str, ModelMemoryEstimate]:
    """
    Filter models to only include those that fit within memory limits.
    
    Args:
        models: Dictionary of model names to memory estimates
    
    Returns:
        Filtered dictionary containing only models that fit in memory
    """
    return {
        name: estimate for name, estimate in models.items()
        if estimate.fits_in_memory
    }
