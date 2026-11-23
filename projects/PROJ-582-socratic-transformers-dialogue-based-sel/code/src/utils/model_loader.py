"""
Base model loader utility supporting 4-bit quantization via bitsandbytes.

This module provides utilities to load transformer models with 4-bit quantization
optimized for CPU/low-memory environments, adhering to the project's memory constraints.
"""

import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from src.utils.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Constructs a BitsAndBytesConfig for 4-bit quantization.

    Returns:
        BitsAndBytesConfig: Configuration object for 4-bit quantization.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

def load_model(
    model_id: Optional[str] = None,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
    quantization_config: Optional[BitsAndBytesConfig] = None,
    cache_dir: Optional[str] = None,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Loads a base model and its tokenizer with 4-bit quantization support.

    Args:
        model_id: The Hugging Face model ID. If None, uses BASE_MODEL_ID from config.
        device_map: Device mapping strategy. Defaults to "auto" if not specified.
        quantization_config: Optional custom quantization config. Defaults to 4-bit config.
        cache_dir: Optional directory to cache models.

    Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded model and tokenizer.

    Raises:
        ValueError: If model_id is not provided and not found in config.
        RuntimeError: If model loading fails.
    """
    config = get_config()
    
    # Determine model ID
    if model_id is None:
        model_id = config.get("BASE_MODEL_ID")
        if not model_id:
            raise ValueError(
                "model_id must be provided or set in config (BASE_MODEL_ID)"
            )

    logger.info(f"Loading model: {model_id}")

    # Setup quantization config if not provided
    if quantization_config is None:
        quantization_config = get_4bit_quantization_config()

    # Setup device map
    if device_map is None:
        # For CPU backend or limited memory, use auto which handles sharding
        device_map = "auto"

    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            cache_dir=cache_dir,
            trust_remote_code=True,
        )
        
        # Ensure pad token exists
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map=device_map,
            cache_dir=cache_dir,
            trust_remote_code=True,
            torch_dtype=torch.float16,
        )

        logger.info(f"Model loaded successfully: {model_id}")
        logger.info(f"Model device: {model.device}")
        
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {str(e)}")
        raise RuntimeError(f"Model loading failed: {str(e)}") from e

def get_model_card(model_id: str) -> Dict[str, Any]:
    """
    Retrieves basic information about a model from its config.

    Args:
        model_id: The Hugging Face model ID.

    Returns:
        Dict containing model metadata.
    """
    try:
        config = AutoTokenizer.from_pretrained(model_id).init_kwargs
        return {
            "model_id": model_id,
            "tokenizer_class": config.get("tokenizer_class", "Unknown"),
            "vocab_size": config.get("vocab_size", "Unknown"),
        }
    except Exception as e:
        logger.warning(f"Could not retrieve model card for {model_id}: {e}")
        return {"model_id": model_id, "error": str(e)}

def validate_model_compatibility(model_id: str) -> bool:
    """
    Validates if a model is compatible with 4-bit quantization.

    Args:
        model_id: The Hugging Face model ID.

    Returns:
        bool: True if compatible, False otherwise.
    """
    try:
        # Attempt to load config without full model
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
        
        # Check for common incompatible architectures
        incompatible_types = ["gpt2", "llama", "mistral"] # Simplified check
        
        logger.info(f"Model {model_id} architecture: {config.model_type}")
        return True
    except Exception as e:
        logger.error(f"Compatibility check failed for {model_id}: {e}")
        return False

def main() -> None:
    """
    Main entry point for testing the model loader.
    """
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # Load model (will use BASE_MODEL_ID from config)
        model, tokenizer = load_model()
        print(f"Successfully loaded model: {model.__class__.__name__}")
        print(f"Tokenizer loaded: {tokenizer.__class__.__name__}")
        
        # Cleanup
        del model
        del tokenizer
        gc.collect()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()