"""
Model loading utilities for Socratic Transformers project.
Supports Low-bit quantization (GGUF or bitsandbytes CPU backend) to fit Limited RAM constraints.
"""
import os
import gc
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizer,
)
from peft import PeftModel

# Import project config to respect seed and path settings
from src.utils.config import get_config

logger = logging.getLogger(__name__)


def _get_default_model_path() -> str:
    """Return the default model path from config or environment."""
    config = get_config()
    if hasattr(config, 'base_model_path') and config.base_model_path:
        return config.base_model_path
    # Fallback to a small model suitable for CPU/low RAM if not specified
    return "microsoft/phi-1.5"


def _create_bitsandbytes_config(
    load_in_4bit: bool = True,
    bnb_4bit_compute_dtype: Optional[torch.dtype] = None,
    bnb_4bit_quant_type: str = "nf4",
    bnb_4bit_use_double_quant: bool = True,
) -> BitsAndBytesConfig:
    """
    Create a BitsAndBytesConfig for 4-bit quantization.
    Optimized for CPU backend or low-memory GPU environments.
    """
    if bnb_4bit_compute_dtype is None:
        # Use float16 if available, else float32 to avoid OOM on CPU
        bnb_4bit_compute_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    return BitsAndBytesConfig(
        load_in_4bit=load_in_4bit,
        bnb_4bit_compute_dtype=bnb_4bit_compute_dtype,
        bnb_4bit_quant_type=bnb_4bit_quant_type,
        bnb_4bit_use_double_quant=bnb_4bit_use_double_quant,
        llm_int8_threshold=6.0,
        llm_int8_has_fp16_weight=False,
    )


def load_model(
    model_id_or_path: Optional[str] = None,
    trust_remote_code: bool = False,
    device_map: Optional[str] = "auto",
    use_lora: bool = False,
    lora_adapter_path: Optional[str] = None,
) -> Tuple[Union[PreTrainedModel, PeftModel], PreTrainedTokenizer]:
    """
    Load a pre-trained model and tokenizer with Low-bit quantization support.

    Args:
        model_id_or_path: HuggingFace model ID or local path. Uses config default if None.
        trust_remote_code: Whether to trust remote code.
        device_map: Device mapping strategy. 'auto' for CPU/GPU distribution.
        use_lora: Whether to load LoRA adapters.
        lora_adapter_path: Path to LoRA adapter weights.

    Returns:
        Tuple of (model, tokenizer)

    Raises:
        RuntimeError: If model loading fails due to memory or configuration issues.
    """
    if model_id_or_path is None:
        model_id_or_path = _get_default_model_path()

    logger.info(f"Loading model: {model_id_or_path}")
    logger.info(f"Device map: {device_map}")

    # Configure quantization for low RAM
    bnb_config = _create_bitsandbytes_config()

    # Load tokenizer first
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id_or_path,
            trust_remote_code=trust_remote_code,
            padding_side="left",
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id
    except Exception as e:
        logger.error(f"Failed to load tokenizer: {e}")
        raise RuntimeError(f"Tokenizer loading failed: {e}")

    # Load base model with quantization
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_id_or_path,
            quantization_config=bnb_config,
            device_map=device_map,
            trust_remote_code=trust_remote_code,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
    except Exception as e:
        logger.error(f"Failed to load base model: {e}")
        raise RuntimeError(f"Base model loading failed: {e}")

    # Load LoRA adapter if requested
    if use_lora and lora_adapter_path:
        logger.info(f"Loading LoRA adapter from: {lora_adapter_path}")
        try:
            model = PeftModel.from_pretrained(model, lora_adapter_path)
        except Exception as e:
            logger.error(f"Failed to load LoRA adapter: {e}")
            raise RuntimeError(f"LoRA adapter loading failed: {e}")

    # Clear GPU cache if available
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

    logger.info(f"Model loaded successfully: {model_id_or_path}")
    return model, tokenizer


def get_model_card(model: PreTrainedModel) -> Dict[str, Any]:
    """
    Extract metadata card from a loaded model.

    Args:
        model: Loaded PreTrainedModel or PeftModel.

    Returns:
        Dictionary containing model metadata.
    """
    card = {}
    if hasattr(model, 'config'):
        card['model_type'] = model.config.model_type
        card['hidden_size'] = getattr(model.config, 'hidden_size', None)
        card['num_attention_heads'] = getattr(model.config, 'num_attention_heads', None)
        card['num_hidden_layers'] = getattr(model.config, 'num_hidden_layers', None)
        card['vocab_size'] = getattr(model.config, 'vocab_size', None)

    if hasattr(model, 'peft_config'):
        card['is_peft_model'] = True
        card['peft_types'] = list(model.peft_config.keys()) if model.peft_config else []
    else:
        card['is_peft_model'] = False

    return card


def validate_model_compatibility(
    model: PreTrainedModel,
    min_hidden_size: int = 512,
    max_hidden_size: int = 8192,
) -> bool:
    """
    Validate that a loaded model meets hardware constraints.

    Args:
        model: Loaded model to validate.
        min_hidden_size: Minimum acceptable hidden dimension.
        max_hidden_size: Maximum acceptable hidden dimension.

    Returns:
        True if model is compatible, False otherwise.
    """
    if not hasattr(model, 'config'):
        logger.warning("Model has no config attribute, skipping validation.")
        return True

    hidden_size = getattr(model.config, 'hidden_size', None)
    if hidden_size is None:
        logger.warning("Could not determine hidden size, skipping validation.")
        return True

    if hidden_size < min_hidden_size:
        logger.warning(f"Hidden size {hidden_size} is below minimum {min_hidden_size}")
        return False

    if hidden_size > max_hidden_size:
        logger.warning(f"Hidden size {hidden_size} exceeds maximum {max_hidden_size}")
        return False

    logger.info(f"Model hidden size {hidden_size} is within acceptable range")
    return True


def main():
    """CLI entry point for model loading demonstration."""
    import argparse

    parser = argparse.ArgumentParser(description="Load model with Low-bit quantization")
    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help="HuggingFace model ID or local path (defaults to config or phi-1.5)"
    )
    parser.add_argument(
        "--use-lora",
        action="store_true",
        help="Load LoRA adapter if available"
    )
    parser.add_argument(
        "--lora-path",
        type=str,
        default=None,
        help="Path to LoRA adapter weights"
    )

    args = parser.parse_args()

    try:
        model, tokenizer = load_model(
            model_id_or_path=args.model_id,
            use_lora=args.use_lora,
            lora_adapter_path=args.lora_path,
        )
        card = get_model_card(model)
        is_valid = validate_model_compatibility(model)

        print(f"Model loaded: {args.model_id or 'default'}")
        print(f"Model card: {card}")
        print(f"Compatibility: {'VALID' if is_valid else 'INVALID'}")

    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise


if __name__ == "__main__":
    main()
