"""
Model loading utilities for Socratic Transformers project.

Supports Low-bit quantization (GGUF or bitsandbytes CPU backend) to fit
Limited RAM constraints on free-tier runners.
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

# Configure logging for model loading operations
logger = logging.getLogger(__name__)


def load_model(
    model_path: str,
    device: str = "cpu",
    quantization: str = "4bit",
    use_cache: bool = False,
    trust_remote_code: bool = False,
    max_memory: Optional[Dict[str, Union[int, str]]] = None,
) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Load a pre-trained model with low-bit quantization support.
    
    Args:
        model_path: Path or HuggingFace model identifier
        device: Target device ('cpu', 'cuda', 'auto')
        quantization: Quantization method ('4bit', '8bit', 'none')
        use_cache: Whether to use KV caching during generation
        trust_remote_code: Whether to trust remote code in model
        max_memory: Maximum memory per device (e.g., {"cpu": "4GB", "cuda:0": "16GB"})
    
    Returns:
        Tuple of (model, tokenizer)
    
    Raises:
        ValueError: If quantization method is not supported
        RuntimeError: If model loading fails due to memory constraints
    """
    logger.info(f"Loading model: {model_path} on {device} with {quantization} quantization")
    
    # Validate quantization method
    if quantization not in ["4bit", "8bit", "none"]:
        raise ValueError(f"Unsupported quantization: {quantization}. Use '4bit', '8bit', or 'none'")
    
    # Load tokenizer first
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=trust_remote_code,
        )
        # Ensure pad token is set for generation
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.info("Set pad_token to eos_token")
    except Exception as e:
        logger.error(f"Failed to load tokenizer: {e}")
        raise
    
    # Configure quantization
    quantization_config = None
    if quantization == "4bit":
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            llm_int8_threshold=6.0,
        )
    elif quantization == "8bit":
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
        )
    
    # Prepare model kwargs
    model_kwargs = {
        "trust_remote_code": trust_remote_code,
        "use_cache": use_cache,
        "device_map": "auto" if device == "auto" else None,
    }
    
    if quantization_config:
        model_kwargs["quantization_config"] = quantization_config
    
    if max_memory:
        model_kwargs["max_memory"] = max_memory
    
    # Load model
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            **model_kwargs,
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    # Move model to device if not using device_map
    if device != "auto" and quantization_config is None:
        model = model.to(device)
    
    logger.info(f"Model loaded successfully: {model_path}")
    return model, tokenizer


def load_peft_model(
    base_model_path: str,
    peft_path: str,
    device: str = "cpu",
    quantization: str = "4bit",
) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Load a PEFT (LoRA) model on top of a base model.
    
    Args:
        base_model_path: Path to the base model
        peft_path: Path to the PEFT adapters
        device: Target device
        quantization: Quantization method for base model
    
    Returns:
        Tuple of (peft_model, tokenizer)
    """
    logger.info(f"Loading PEFT model from {peft_path} on base {base_model_path}")
    
    # Load base model with quantization
    base_model, tokenizer = load_model(
        model_path=base_model_path,
        device=device,
        quantization=quantization,
    )
    
    # Load PEFT adapters
    try:
        peft_model = PeftModel.from_pretrained(base_model, peft_path)
    except Exception as e:
        logger.error(f"Failed to load PEFT adapters: {e}")
        raise
    
    logger.info("PEFT model loaded successfully")
    return peft_model, tokenizer


def get_model_card(model_path: str) -> Dict[str, Any]:
    """
    Retrieve model metadata/card information.
    
    Args:
        model_path: Path or HuggingFace model identifier
    
    Returns:
        Dictionary containing model metadata
    """
    from transformers import AutoConfig
    
    try:
        config = AutoConfig.from_pretrained(model_path)
        return {
            "model_type": config.model_type,
            "hidden_size": getattr(config, "hidden_size", None),
            "num_attention_heads": getattr(config, "num_attention_heads", None),
            "num_hidden_layers": getattr(config, "num_hidden_layers", None),
            "vocab_size": getattr(config, "vocab_size", None),
            "max_position_embeddings": getattr(config, "max_position_embeddings", None),
        }
    except Exception as e:
        logger.warning(f"Could not retrieve model card: {e}")
        return {}


def validate_model_compatibility(
    model_path: str,
    required_memory_gb: float = 4.0,
    quantization: str = "4bit",
) -> bool:
    """
    Validate if a model can fit within memory constraints.
    
    Args:
        model_path: Path or HuggingFace model identifier
        required_memory_gb: Required memory in GB
        quantization: Quantization method
    
    Returns:
        True if model is compatible, False otherwise
    """
    model_card = get_model_card(model_path)
    
    if not model_card:
        logger.warning("Could not validate model compatibility - no model card")
        return False
    
    # Estimate memory usage based on quantization
    vocab_size = model_card.get("vocab_size", 0)
    hidden_size = model_card.get("hidden_size", 0)
    num_layers = model_card.get("num_hidden_layers", 0)
    
    if not all([vocab_size, hidden_size, num_layers]):
        logger.warning("Incomplete model info for memory estimation")
        return True  # Assume compatible if we can't estimate
    
    # Rough memory estimation (in GB)
    # Parameters ≈ hidden_size * (vocab_size + 4 * hidden_size * num_layers)
    # For 4-bit: divide by 8 (bits per byte / bits per param)
    
    estimated_params = hidden_size * (vocab_size + 4 * hidden_size * num_layers)
    
    if quantization == "4bit":
        estimated_memory_gb = (estimated_params * 4) / (8 * 1024**3)
    elif quantization == "8bit":
        estimated_memory_gb = (estimated_params * 8) / (8 * 1024**3)
    else:
        estimated_memory_gb = (estimated_params * 16) / (8 * 1024**3)  # float16
    
    logger.info(f"Estimated memory for {model_path}: {estimated_memory_gb:.2f} GB")
    
    return estimated_memory_gb <= required_memory_gb


def main():
    """
    Command-line interface for model loading utilities.
    
    Usage:
        python -m src.utils.model_loader --model_path <path> --quantization <4bit|8bit|none>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Model loading utility")
    parser.add_argument("--model_path", type=str, required=True, help="Model path or identifier")
    parser.add_argument("--device", type=str, default="cpu", help="Target device")
    parser.add_argument("--quantization", type=str, default="4bit", choices=["4bit", "8bit", "none"])
    parser.add_argument("--validate_only", action="store_true", help="Only validate compatibility")
    parser.add_argument("--required_memory_gb", type=float, default=4.0, help="Required memory in GB")
    
    args = parser.parse_args()
    
    if args.validate_only:
        compatible = validate_model_compatibility(
            args.model_path,
            args.required_memory_gb,
            args.quantization,
        )
        print(f"Model compatible: {compatible}")
        return
    
    try:
        model, tokenizer = load_model(
            model_path=args.model_path,
            device=args.device,
            quantization=args.quantization,
        )
        print(f"Successfully loaded model: {args.model_path}")
        print(f"Model type: {type(model).__name__}")
        print(f"Tokenizer type: {type(tokenizer).__name__}")
    except Exception as e:
        print(f"Failed to load model: {e}")
        raise


if __name__ == "__main__":
    main()