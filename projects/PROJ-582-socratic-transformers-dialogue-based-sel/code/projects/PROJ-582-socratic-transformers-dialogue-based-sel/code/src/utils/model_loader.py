"""
Base model loader utility supporting Low-bit quantization.
"""
import os
import gc
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from src.utils.config import get_config

logger = logging.getLogger(__name__)

def load_model(
    model_name: str,
    use_4bit: bool = True,
    device_map: Optional[str] = "auto"
) -> Tuple[Any, Any]:
    """
    Load a model and tokenizer with optional 4-bit quantization.
    
    Args:
        model_name: HuggingFace model name or path.
        use_4bit: Whether to use 4-bit quantization (bitsandbytes).
        device_map: Device mapping for the model.
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading model: {model_name} (4bit={use_4bit})")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    if use_4bit:
        try:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                trust_remote_code=True
            )
        except Exception as e:
            logger.error(f"Failed to load model with 4-bit quantization: {e}")
            logger.info("Falling back to 8-bit or full precision...")
            # Fallback to 8-bit if 4-bit fails
            try:
                bnb_config_8bit = BitsAndBytesConfig(load_in_8bit=True)
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=bnb_config_8bit,
                    device_map=device_map
                )
            except Exception as e2:
                logger.error(f"Failed to load model with 8-bit quantization: {e2}")
                logger.info("Loading full precision model (may OOM on CPU)...")
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map=device_map,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=device_map,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
    return model, tokenizer

def get_model_card(model_name: str) -> Dict[str, Any]:
    """Get basic info about a model."""
    return {
        "name": model_name,
        "loaded": True
    }

def validate_model_compatibility(model_name: str) -> bool:
    """Check if a model is compatible with the current environment."""
    # Basic check for model existence
    try:
        from transformers import AutoConfig
        AutoConfig.from_pretrained(model_name)
        return True
    except Exception:
        return False

def main():
    """Main entry point for model loader."""
    config = get_config()
    model, tokenizer = load_model(config.base_model_name, use_4bit=config.use_4bit)
    logger.info("Model loaded successfully")
    return model, tokenizer
