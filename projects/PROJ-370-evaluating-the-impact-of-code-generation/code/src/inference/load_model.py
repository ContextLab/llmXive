"""
Model loading utilities for LLM-assisted bug detection.

This module provides functionality to load the StarCoder2-3B model
with memory constraints to ensure usage stays within 7GB (FR-015).
"""

import logging
import torch
from pathlib import Path
from typing import Optional, Dict, Any

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from config.settings import get_config, ensure_directories
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Model configuration
MODEL_ID = "bigcode/starcoder2-3b"
MEMORY_LIMIT_GB = 7.0
DEFAULT_DEVICE_MAP = "auto"
DEFAULT_LOW_CPU_MEM_USAGE = True

def load_model_and_tokenizer(
    model_id: str = MODEL_ID,
    device_map: str = DEFAULT_DEVICE_MAP,
    low_cpu_mem_usage: bool = DEFAULT_LOW_CPU_MEM_USAGE,
    torch_dtype: torch.dtype = torch.float16,
    max_memory: Optional[Dict[str, Any]] = None,
):
    """
    Load StarCoder2-3B model and tokenizer with memory constraints.

    Args:
        model_id: HuggingFace model identifier
        device_map: Device mapping strategy (default: "auto")
        low_cpu_mem_usage: Optimize CPU memory usage (default: True)
        torch_dtype: Precision for model weights (default: float16)
        max_memory: Optional dictionary mapping device to max memory in bytes/GB

    Returns:
        Tuple of (model, tokenizer)

    Raises:
        RuntimeError: If model loading fails or memory constraints are violated
        ValueError: If unsupported configuration is provided
    """
    logger.info(f"Loading model: {model_id}")
    logger.info(f"Device map: {device_map}, Low CPU memory usage: {low_cpu_mem_usage}")
    logger.info(f"Target precision: {torch_dtype}")

    # Validate device_map
    if device_map != "auto" and device_map != "cpu" and not isinstance(device_map, dict):
        raise ValueError(f"Unsupported device_map: {device_map}. Use 'auto', 'cpu', or a dict.")

    # Set up memory constraints if not explicitly provided
    if max_memory is None:
        # Calculate max memory based on limit (7GB)
        # Reserve some headroom for activation memory
        max_memory_gb = MEMORY_LIMIT_GB * 0.9  # 90% of limit for model weights
        max_memory = {"cpu": f"{max_memory_gb}GB"}
        logger.info(f"Setting max memory to {max_memory_gb}GB per device")

    try:
        # Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
        )

        # Configure model loading with memory optimization
        logger.info("Loading model with memory optimization...")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=device_map,
            low_cpu_mem_usage=low_cpu_mem_usage,
            torch_dtype=torch_dtype,
            max_memory=max_memory,
            trust_remote_code=True,
            # Additional memory optimizations
            attn_implementation="flash_attention_2" if torch.cuda.is_available() else None,
        )

        # Verify model is loaded successfully
        if model is None:
            raise RuntimeError("Failed to load model - model object is None")

        logger.info(f"Model loaded successfully on device: {next(model.parameters()).device}")
        logger.info(f"Model dtype: {model.dtype}")

        # Log model size estimate
        num_params = sum(p.numel() for p in model.parameters())
        param_size_gb = (num_params * model.element_size()) / (1024 ** 3)
        logger.info(f"Model parameters: {num_params:,} (~{param_size_gb:.2f}GB at {model.element_size() * 8} bits)")

        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}", exc_info=True)
        raise RuntimeError(f"Model loading failed: {str(e)}") from e

def load_model_for_inference(
    model_id: str = MODEL_ID,
    use_float16: bool = True,
):
    """
    Load model optimized for inference with memory constraints.

    This is the primary entry point for loading the model in the inference pipeline.

    Args:
        model_id: HuggingFace model identifier
        use_float16: Use float16 precision for memory efficiency (default: True)

    Returns:
        Tuple of (model, tokenizer)
    """
    dtype = torch.float16 if use_float16 else torch.float32
    return load_model_and_tokenizer(
        model_id=model_id,
        device_map=DEFAULT_DEVICE_MAP,
        low_cpu_mem_usage=DEFAULT_LOW_CPU_MEM_USAGE,
        torch_dtype=dtype,
    )

def main():
    """
    Main function to test model loading.
    """
    # Ensure output directories exist
    config = get_config()
    ensure_directories()

    logger.info("Starting model loading test...")

    try:
        model, tokenizer = load_model_for_inference()
        logger.info("Model loading test PASSED")

        # Test basic inference capability
        test_input = "def hello_world():"
        inputs = tokenizer(test_input, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Test generation successful: {result[:100]}...")

        return 0

    except Exception as e:
        logger.error(f"Model loading test FAILED: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
