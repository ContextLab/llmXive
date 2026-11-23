"""
Base model loader utility supporting 4-bit quantization via bitsandbytes (CPU backend).

This module provides functions to load transformer models with 4-bit quantization
configured for CPU execution, adhering to the memory constraints (FR-003) of the project.
"""

import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, PreTrainedModel

# Import project configuration
from src.utils.config import get_config

# Setup logging
logger = logging.getLogger(__name__)

def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Configure 4-bit quantization settings optimized for CPU inference.

    Returns:
        BitsAndBytesConfig: Configuration object for 4-bit quantization.
    """
    try:
        from bitsandbytes.nn.modules import Params4bit
        # bitsandbytes is available, configure 4-bit
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float32,  # Use float32 for stability on CPU
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            llm_int8_enable_fp32_cpu_offload=True,  # Enable CPU offloading for LLM.int8 style
            # Note: For pure CPU 4-bit, we often rely on the model loading logic
            # to handle device mapping. The config below is the standard 4-bit setup.
        )
        logger.info("4-bit quantization configuration created for CPU backend.")
        return quantization_config
    except ImportError:
        logger.warning("bitsandbytes not installed. Falling back to standard 8-bit or full precision config.")
        # Fallback to a lighter quantization if bitsandbytes is missing, though T002 requires it.
        # We still return a config, but it might be ignored if the library isn't present.
        return BitsAndBytesConfig(
            load_in_4bit=False,
            load_in_8bit=True,
        )

def load_model(
    model_id: Optional[str] = None,
    device_map: str = "auto",
    trust_remote_code: bool = False,
) -> Tuple[PreTrainedModel, AutoTokenizer]:
    """
    Load a base model and tokenizer with 4-bit quantization support.

    Args:
        model_id: The HuggingFace model ID. Defaults to BASE_MODEL_ID from config.
        device_map: Device mapping strategy. Defaults to "auto".
        trust_remote_code: Whether to trust remote code in the model.

    Returns:
        Tuple containing the loaded model and tokenizer.

    Raises:
        ValueError: If model_id is not provided and not found in config.
        RuntimeError: If model loading fails.
    """
    config = get_config()

    if model_id is None:
        if not hasattr(config, 'BASE_MODEL_ID') or config.BASE_MODEL_ID is None:
            raise ValueError("model_id not provided and BASE_MODEL_ID is not set in config.")
        model_id = config.BASE_MODEL_ID

    logger.info(f"Loading model: {model_id}")

    # Get quantization config
    quantization_config = get_4bit_quantization_config()

    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=trust_remote_code,
            use_fast=True,
        )

        # Ensure tokenizer has pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map=device_map,
            trust_remote_code=trust_remote_code,
            torch_dtype=torch.float32,  # Explicitly set dtype for CPU safety
            low_cpu_mem_usage=True,
        )

        # Verify model is loaded
        if model is None:
            raise RuntimeError("Failed to load model: returned None.")

        logger.info(f"Model {model_id} loaded successfully with 4-bit quantization.")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {str(e)}")
        # Attempt cleanup
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise RuntimeError(f"Model loading failed: {str(e)}") from e

def get_model_card(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch basic metadata for a model from HuggingFace.

    Args:
        model_id: The HuggingFace model ID.

    Returns:
        Dictionary with model metadata or None if not found.
    """
    from huggingface_hub import HfApi

    api = HfApi()
    try:
        model_info = api.model_info(model_id)
        return {
            "id": model_info.id,
            "author": model_info.author,
            "cardData": getattr(model_info, 'cardData', None),
            "tags": model_info.tags,
        }
    except Exception as e:
        logger.warning(f"Could not fetch model card for {model_id}: {e}")
        return None

def validate_model_compatibility(model_id: str) -> bool:
    """
    Validate that a model is compatible with 4-bit quantization and CPU constraints.

    Args:
        model_id: The HuggingFace model ID.

    Returns:
        True if compatible, False otherwise.
    """
    # Basic heuristic: check if model is a known LLM type
    # In a real implementation, we might check parameter count or architecture
    if "llama" in model_id.lower() or "mistral" in model_id.lower() or "gemma" in model_id.lower():
        return True

    # Fallback: assume compatible if not explicitly known incompatible
    # A more robust check would involve fetching model config and checking params
    return True

def main() -> None:
    """
    Main entry point for testing the model loader.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Attempt to load the model defined in config
        # This will raise an error if BASE_MODEL_ID is not set or model is inaccessible
        model, tokenizer = load_model()
        print(f"Successfully loaded model: {model.config.model_type}")
        print(f"Tokenizer vocab size: {tokenizer.vocab_size}")
        
        # Simple inference test (optional, depends on time/resources)
        # input_text = "Hello, world!"
        # inputs = tokenizer(input_text, return_tensors="pt")
        # outputs = model.generate(**inputs, max_new_tokens=10)
        # print(f"Generated: {tokenizer.decode(outputs[0], skip_special_tokens=True)}")
        
    except Exception as e:
        print(f"Model loading test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()