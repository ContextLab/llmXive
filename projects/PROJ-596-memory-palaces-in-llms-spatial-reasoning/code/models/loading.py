"""
Model Loading Utilities.

Handles loading of GPT-2 Medium (quantized) and DistilGPT2 fallback based on
memory constraints.
"""

import os
import sys
import gc
import logging
from typing import Optional, Tuple, Union

import torch

# Import the wrapper classes defined in this task
from models.base import GPT2MediumBaseline
from models.base_fallback import DistilGPT2Fallback
from training.memory_monitor import MemoryMonitor

logger = logging.getLogger(__name__)


def check_memory_budget(required_gb: float = 6.0) -> bool:
    """
    Check if the system has enough free memory to load a large model.

    Args:
        required_gb: Required memory in GB.

    Returns:
        True if memory is sufficient, False otherwise.
    """
    # Simple check using torch.cuda if available, else system memory
    if torch.cuda.is_available():
        free_memory = torch.cuda.mem_get_info()[0] / (1024 ** 3)
        return free_memory > required_gb
    else:
        # Fallback for CPU-only environments (approximate)
        # In a real scenario, we might use psutil, but keeping it simple for now
        logger.warning("CUDA not available. Assuming sufficient CPU memory for demo.")
        return True


def load_gpt2_medium_quantized(model_name: str = "gpt2-medium") -> GPT2MediumBaseline:
    """
    Load the GPT-2 Medium model with 4-bit quantization.

    Args:
        model_name: Hugging Face model identifier.

    Returns:
        GPT2MediumBaseline instance.
    """
    logger.info("Attempting to load GPT-2 Medium (quantized)...")
    model = GPT2MediumBaseline(model_name=model_name, quantized=True)
    logger.info("GPT-2 Medium loaded successfully.")
    return model


def load_distilgpt2_fallback(model_name: str = "distilgpt2") -> DistilGPT2Fallback:
    """
    Load the DistilGPT2 fallback model.

    Args:
        model_name: Hugging Face model identifier.

    Returns:
        DistilGPT2Fallback instance.
    """
    logger.info("Loading DistilGPT2 fallback...")
    model = DistilGPT2Fallback(model_name=model_name)
    logger.info("DistilGPT2 loaded successfully.")
    return model


def load_model(
    preferred_model: str = "gpt2-medium",
    fallback_model: str = "distilgpt2",
    memory_threshold_gb: float = 6.0
) -> Tuple[Union[GPT2MediumBaseline, DistilGPT2Fallback], str]:
    """
    Load a model based on memory availability.

    Tries to load the preferred model (GPT-2 Medium). If memory is insufficient,
    falls back to the smaller model (DistilGPT2).

    Args:
        preferred_model: Name of the preferred model.
        fallback_model: Name of the fallback model.
        memory_threshold_gb: Memory threshold in GB to trigger fallback.

    Returns:
        Tuple of (loaded_model_instance, model_type_name)
    """
    logger.info(f"Checking memory budget (threshold: {memory_threshold_gb} GB)...")
    
    # Clear cache before checking
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if check_memory_budget(memory_threshold_gb):
        try:
            logger.info("Memory sufficient. Loading preferred model (GPT-2 Medium).")
            model = load_gpt2_medium_quantized(preferred_model)
            return model, "gpt2_medium"
        except Exception as e:
            logger.error(f"Failed to load preferred model: {e}")
            logger.warning("Falling back to DistilGPT2.")
    else:
        logger.warning("Memory insufficient for GPT-2 Medium. Falling back to DistilGPT2.")

    # Load fallback
    model = load_distilgpt2_fallback(fallback_model)
    return model, "distilgpt2_fallback"


def main():
    """Entry point for testing model loading."""
    logging.basicConfig(level=logging.INFO)
    model, model_type = load_model()
    logger.info(f"Selected model type: {model_type}")
    logger.info(f"Model parameters: {model.get_num_params()}")

if __name__ == "__main__":
    main()