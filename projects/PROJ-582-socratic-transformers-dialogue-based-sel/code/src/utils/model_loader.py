"""
Base model loader utility supporting 4-bit quantization via bitsandbytes.

This module provides functions to load transformer models with quantization
configured for CPU backend execution, adhering to the project's memory constraints.
"""

import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizer,
)

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_config

logger = logging.getLogger(__name__)


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Constructs a BitsAndBytesConfig for 4-bit quantization optimized for CPU.

    Returns:
        BitsAndBytesConfig: Configuration object for 4-bit quantization.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float32,  # CPU often prefers float32 for compute
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        llm_int8_enable_fp32_cpu_offload=True,  # Enable CPU offload for stability
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"],  # Keep output layer in FP32
    )


def load_model(
    model_id: Optional[str] = None,
    quantization_config: Optional[BitsAndBytesConfig] = None,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Loads a transformer model and tokenizer with optional 4-bit quantization.

    Args:
        model_id: The Hugging Face model ID. If None, reads from config.
        quantization_config: Optional BitsAndBytesConfig. If None, uses default 4-bit config.
        device_map: Optional device mapping. Defaults to "auto" or CPU if memory constrained.

    Returns:
        Tuple[PreTrainedModel, PreTrainedTokenizer]: The loaded model and tokenizer.
    """
    config = get_config()
    effective_model_id = model_id or config.BASE_MODEL_ID

    if not effective_model_id:
        raise ValueError(
            "Model ID not provided and not found in configuration (BASE_MODEL_ID)."
        )

    logger.info(f"Loading model: {effective_model_id}")

    if quantization_config is None:
        quantization_config = get_4bit_quantization_config()
        logger.info("Using default 4-bit quantization config.")

    # Determine device map
    if device_map is None:
        # Default to auto, but ensure CPU compatibility if needed
        # For strict CPU-only environments, we might force 'cpu' but 'auto' handles offloading better
        device_map = "auto"
        logger.info("Using 'auto' device map.")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            effective_model_id,
            trust_remote_code=True,
        )
        # Ensure pad token exists for generation
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            effective_model_id,
            quantization_config=quantization_config,
            device_map=device_map,
            trust_remote_code=True,
            torch_dtype=torch.float32,  # Ensure base dtype is compatible
        )

        logger.info(f"Model loaded successfully: {model.config.model_type}")
        logger.info(f"Model parameters: {model.num_parameters()}")

        # Force garbage collection to free up memory
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {effective_model_id}: {e}")
        raise


def get_model_card(model: PreTrainedModel) -> Dict[str, Any]:
    """
    Extracts basic metadata from a loaded model.

    Args:
        model: The loaded PreTrainedModel.

    Returns:
        Dict[str, Any]: Dictionary containing model metadata.
    """
    return {
        "model_type": model.config.model_type,
        "vocab_size": model.config.vocab_size,
        "hidden_size": getattr(model.config, "hidden_size", None),
        "num_attention_heads": getattr(model.config, "num_attention_heads", None),
        "num_hidden_layers": getattr(model.config, "num_hidden_layers", None),
    }


def validate_model_compatibility(
    model: PreTrainedModel,
    required_features: Optional[list[str]] = None,
) -> bool:
    """
    Validates that the loaded model supports required features.

    Args:
        model: The loaded model.
        required_features: List of required config keys or capabilities.

    Returns:
        bool: True if compatible, False otherwise.
    """
    if required_features is None:
        return True

    for feature in required_features:
        if not hasattr(model.config, feature):
            logger.warning(f"Model missing required feature: {feature}")
            return False
    return True


def main():
    """
    Entry point for standalone execution and verification.
    Attempts to load the model defined in config to verify the loader works.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        model, tokenizer = load_model()
        logger.info("Model loader verification: SUCCESS")
        logger.info(f"Model Card: {get_model_card(model)}")
        return 0
    except Exception as e:
        logger.error(f"Model loader verification: FAILED - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
