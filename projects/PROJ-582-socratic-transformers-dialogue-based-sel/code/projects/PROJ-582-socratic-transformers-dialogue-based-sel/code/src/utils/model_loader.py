"""
Base model loader utility supporting 4-bit quantization via bitsandbytes.
Designed for CPU backend execution as per project constraints.
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

# Configure logging for the module
logger = logging.getLogger(__name__)

def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Creates a BitsAndBytesConfig for 4-bit quantization optimized for CPU.
    
    Returns:
        BitsAndBytesConfig: Configuration object for 4-bit loading.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float32,  # Use float32 for CPU stability
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        llm_int8_enable_fp32_cpu_offload=True,  # Ensure CPU compatibility
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head", "embed_tokens"],
    )

def load_model(
    model_id: Optional[str] = None,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
    max_memory: Optional[Dict[str, Union[int, str]]] = None,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Loads a base model and tokenizer with 4-bit quantization support.
    
    Args:
        model_id: The HuggingFace model ID. If None, loads from config.BASE_MODEL_ID.
        device_map: Device mapping strategy. Defaults to "cpu" if not specified.
        max_memory: Maximum memory per device.
        
    Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded model and tokenizer.
        
    Raises:
        ValueError: If the model configuration is invalid or loading fails.
    """
    config = get_config()
    effective_model_id = model_id or config.BASE_MODEL_ID
    
    if not effective_model_id:
        raise ValueError(
            "Model ID not provided and BASE_MODEL_ID is not set in configuration."
        )

    logger.info(f"Loading model: {effective_model_id}")
    
    # Determine device map if not provided
    if device_map is None:
        # Force CPU as per task requirement for CPU backend
        device_map = "cpu"
    
    # Prepare quantization config
    quantization_config = get_4bit_quantization_config()

    try:
        # Load tokenizer first
        tokenizer = AutoTokenizer.from_pretrained(
            effective_model_id,
            trust_remote_code=True,
            padding_side="left",
        )
        
        # Ensure pad token is set if missing
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            effective_model_id,
            quantization_config=quantization_config,
            device_map=device_map,
            max_memory=max_memory,
            trust_remote_code=True,
            torch_dtype=torch.float32,  # Explicit float32 for CPU
        )
        
        logger.info(f"Successfully loaded model: {effective_model_id}")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {effective_model_id}: {str(e)}")
        raise

def get_model_card(model_id: str) -> Dict[str, Any]:
    """
    Retrieves basic metadata about a model from HuggingFace.
    
    Args:
        model_id: The HuggingFace model ID.
        
    Returns:
        Dict[str, Any]: Model metadata including pipeline_tag, tags, etc.
    """
    from transformers import AutoConfig
    
    try:
        config = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
        return {
            "model_id": model_id,
            "architectures": getattr(config, "architectures", []),
            "model_type": getattr(config, "model_type", "unknown"),
            "hidden_size": getattr(config, "hidden_size", None),
            "num_attention_heads": getattr(config, "num_attention_heads", None),
            "num_hidden_layers": getattr(config, "num_hidden_layers", None),
        }
    except Exception as e:
        logger.warning(f"Could not retrieve model card for {model_id}: {e}")
        return {"model_id": model_id, "error": str(e)}

def validate_model_compatibility(
    model_id: str, 
    required_features: Optional[list] = None
) -> bool:
    """
    Validates if a model is compatible with the current environment.
    
    Args:
        model_id: The HuggingFace model ID.
        required_features: List of required features (e.g., ["4-bit", "CPU"]).
        
    Returns:
        bool: True if compatible, False otherwise.
    """
    if required_features is None:
        required_features = ["4-bit", "CPU"]
        
    # Check if 4-bit is available
    if "4-bit" in required_features:
        try:
            import bitsandbytes as bnb
            if not hasattr(bnb.nn, "Linear4bit"):
                logger.error("bitsandbytes 4-bit support not found.")
                return False
        except ImportError:
            logger.error("bitsandbytes not installed.")
            return False
    
    # Check CPU availability
    if "CPU" in required_features:
        if not torch.cuda.is_available():
            logger.info("CUDA not available, falling back to CPU.")
        else:
            logger.info("CUDA available, but CPU mode requested.")
    
    return True

def main():
    """
    Main entry point for testing the model loader.
    Runs the verification command: python -c "from src.utils.model_loader import load_model; load_model()"
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        # Attempt to load the model defined in config
        # Using a small model for verification to ensure it runs within time/memory constraints
        # In production, config.BASE_MODEL_ID should be set to the intended model
        model, tokenizer = load_model()
        logger.info("Model loaded successfully.")
        print("SUCCESS: Model loader verification passed.")
        return 0
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        print(f"FAILED: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())