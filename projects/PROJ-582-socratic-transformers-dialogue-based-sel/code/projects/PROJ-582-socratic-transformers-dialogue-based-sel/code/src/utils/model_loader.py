import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, PreTrainedModel

from src.utils.config import get_config

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Constructs a BitsAndBytesConfig for 4-bit quantization optimized for CPU backend.
    
    Returns:
        BitsAndBytesConfig: Configuration object for 4-bit loading.
    """
    config = get_config()
    # Default to a small model if not specified, but rely on config for the actual ID
    base_model_id = getattr(config, 'BASE_MODEL_ID', 'microsoft/phi-2')
    
    logger.info(f"Preparing 4-bit quantization config for {base_model_id} on CPU backend.")
    
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float32,  # Use float32 for CPU stability
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        llm_int8_enable_fp32_cpu_offload=False, # Keep it simple for CPU
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"],
    )

def load_model(
    model_id: Optional[str] = None,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
    use_4bit: bool = True
) -> Tuple[PreTrainedModel, AutoTokenizer]:
    """
    Loads the base model and tokenizer with optional 4-bit quantization.
    
    Args:
        model_id: HuggingFace model ID. Defaults to BASE_MODEL_ID from config.
        device_map: Where to load the model. Defaults to "cpu" if not provided.
        use_4bit: Whether to use 4-bit quantization.
        
    Returns:
        Tuple containing the loaded model and tokenizer.
        
    Raises:
        ValueError: If model loading fails.
        ImportError: If required libraries (bitsandbytes) are missing.
    """
    if model_id is None:
        config = get_config()
        model_id = getattr(config, 'BASE_MODEL_ID', 'microsoft/phi-2')
    
    if device_map is None:
        device_map = "cpu"
    
    logger.info(f"Loading model: {model_id} on {device_map}")
    
    # Load tokenizer first
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
    except Exception as e:
        logger.error(f"Failed to load tokenizer for {model_id}: {e}")
        raise ValueError(f"Could not load tokenizer: {e}") from e

    # Prepare quantization config if needed
    quantization_config = None
    if use_4bit:
        try:
            # Attempt to import bitsandbytes to ensure it's available
            import bitsandbytes as bnb
            quantization_config = get_4bit_quantization_config()
            logger.info("4-bit quantization config generated.")
        except ImportError:
            logger.warning("bitsandbytes not found. Loading model in full precision.")
            use_4bit = False
        except Exception as e:
            logger.error(f"Error configuring 4-bit quantization: {e}")
            use_4bit = False

    # Load model
    try:
        model_kwargs = {
            "trust_remote_code": True,
            "device_map": device_map,
            "torch_dtype": torch.float32, # Explicitly set for CPU
        }
        
        if use_4bit and quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            **model_kwargs
        )
        
        logger.info(f"Model loaded successfully: {model_id}")
        logger.info(f"Model parameters: {model.num_parameters()}")
        
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {e}")
        # Clean up memory if partial load occurred
        if 'model' in locals():
            del model
            gc.collect()
        raise ValueError(f"Could not load model: {e}") from e

def get_model_card(model: PreTrainedModel) -> Optional[Dict[str, Any]]:
    """
    Retrieves the model card (config) metadata.
    
    Args:
        model: The loaded model instance.
        
    Returns:
        Dictionary of model config attributes or None if unavailable.
    """
    try:
        return {
            "model_type": getattr(model.config, "model_type", "unknown"),
            "hidden_size": getattr(model.config, "hidden_size", None),
            "num_attention_heads": getattr(model.config, "num_attention_heads", None),
            "num_hidden_layers": getattr(model.config, "num_hidden_layers", None),
        }
    except Exception as e:
        logger.warning(f"Could not retrieve model card: {e}")
        return None

def validate_model_compatibility(model: PreTrainedModel) -> bool:
    """
    Validates that the loaded model meets basic compatibility criteria.
    
    Args:
        model: The loaded model instance.
        
    Returns:
        True if compatible, False otherwise.
    """
    if model is None:
        return False
    
    # Check if it has a forward method
    if not hasattr(model, "forward"):
        logger.error("Model missing forward method.")
        return False
        
    # Check if it has a config
    if not hasattr(model, "config"):
        logger.error("Model missing config.")
        return False
        
    logger.info("Model compatibility check passed.")
    return True

def main():
    """
    Main entry point for testing the model loader.
    """
    try:
        model, tokenizer = load_model()
        if validate_model_compatibility(model):
            card = get_model_card(model)
            print(f"Successfully loaded model. Card: {card}")
            sys.exit(0)
        else:
            print("Model loaded but failed compatibility check.")
            sys.exit(1)
    except Exception as e:
        print(f"Error during model loading: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
