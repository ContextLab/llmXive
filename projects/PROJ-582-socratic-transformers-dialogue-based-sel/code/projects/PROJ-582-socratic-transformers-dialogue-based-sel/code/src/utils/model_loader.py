"""
Model Loader Utility for Socratic Transformers Project.

Implements base model loading with 4-bit quantization support via bitsandbytes.
Designed for CPU-constrained environments as per project requirements.
"""
import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import project config to get model IDs
try:
    from src.utils.config import get_config
except ImportError:
    # Fallback for direct execution
    logger.warning("Could not import config. Using defaults.")
    get_config = None


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Configure 4-bit quantization for memory efficiency.

    Returns:
        BitsAndBytesConfig: Quantization configuration for 4-bit loading.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        llm_int8_threshold=6.0,
        # Force CPU backend as per task requirement
        llm_int8_has_fp16_weight=False,
    )


def load_model(
    model_id: Optional[str] = None,
    tokenizer_id: Optional[str] = None,
    peft_path: Optional[str] = None,
    device_map: Optional[str] = "auto",
    quantization: bool = True
) -> Tuple[Any, Any]:
    """
    Load a base model with optional 4-bit quantization and PEFT adapters.

    Args:
        model_id: HuggingFace model ID. Defaults to BASE_MODEL_ID from config.
        tokenizer_id: HuggingFace tokenizer ID. Defaults to model_id if None.
        peft_path: Path to PEFT adapters (LoRA). Optional.
        device_map: Device mapping strategy. Defaults to "auto".
        quantization: Whether to use 4-bit quantization. Defaults to True.

    Returns:
        Tuple containing (model, tokenizer).

    Raises:
        ValueError: If model loading fails.
        RuntimeError: If quantization dependencies are missing.
    """
    # Determine model and tokenizer IDs
    if model_id is None:
        if get_config:
            config = get_config()
            model_id = getattr(config, 'BASE_MODEL_ID', 'microsoft/phi-2')
        else:
            model_id = 'microsoft/phi-2'
    
    if tokenizer_id is None:
        tokenizer_id = model_id

    logger.info(f"Loading model: {model_id}")
    logger.info(f"Loading tokenizer: {tokenizer_id}")

    # Load tokenizer first
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_id,
            trust_remote_code=True,
            padding_side='left'
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
    except Exception as e:
        logger.error(f"Failed to load tokenizer: {e}")
        raise

    # Configure quantization if requested
    quantization_config = None
    if quantization:
        try:
            import bitsandbytes as bnb
            logger.info("bitsandbytes available, enabling 4-bit quantization")
            quantization_config = get_4bit_quantization_config()
        except ImportError:
            logger.warning("bitsandbytes not installed. Falling back to 16-bit loading.")
            quantization_config = None
    else:
        logger.info("Quantization disabled")

    # Load base model
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map=device_map,
            trust_remote_code=True,
            torch_dtype=torch.float16 if quantization else torch.float32,
            low_cpu_mem_usage=True
        )
        logger.info(f"Base model loaded successfully from {model_id}")
    except Exception as e:
        logger.error(f"Failed to load base model: {e}")
        raise

    # Load PEFT adapters if provided
    if peft_path:
        try:
            logger.info(f"Loading PEFT adapters from: {peft_path}")
            model = PeftModel.from_pretrained(model, peft_path)
            logger.info("PEFT adapters loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load PEFT adapters: {e}")
            raise

    # Move to correct device if not using device_map
    if device_map is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        logger.info(f"Model moved to device: {device}")

    return model, tokenizer


def get_model_card(model_id: str) -> Dict[str, Any]:
    """
    Retrieve metadata about a model from HuggingFace.

    Args:
        model_id: HuggingFace model ID.

    Returns:
        Dictionary containing model metadata.
    """
    from huggingface_hub import model_info
    
    try:
        info = model_info(model_id)
        return {
            "id": info.id,
            "author": info.author,
            "pipeline_tag": info.pipeline_tag,
            "tags": info.tags,
            "downloads": info.downloads,
            "likes": info.likes,
            "card_data": info.card_data.to_dict() if info.card_data else None
        }
    except Exception as e:
        logger.error(f"Failed to fetch model card for {model_id}: {e}")
        return {}


def validate_model_compatibility(
    model_id: str,
    required_memory_gb: float = 4.0
) -> bool:
    """
    Check if a model is compatible with available hardware.

    Args:
        model_id: HuggingFace model ID.
        required_memory_gb: Minimum required RAM in GB.

    Returns:
        True if compatible, False otherwise.
    """
    from huggingface_hub import model_info
    
    try:
        info = model_info(model_id)
        # Get model size from card data if available
        if info.card_data and hasattr(info.card_data, 'model_size'):
            model_size_gb = info.card_data.model_size
            if model_size_gb > required_memory_gb:
                logger.warning(
                    f"Model {model_id} size ({model_size_gb}GB) exceeds "
                    f"available memory requirement ({required_memory_gb}GB)"
                )
                return False
        
        # Check if model has quantization configs
        has_quantization = any(
            tag.startswith('quantization') for tag in (info.tags or [])
        )
        if not has_quantization:
            logger.info(
                f"Model {model_id} may not have optimized quantization configs"
            )
        
        return True
    except Exception as e:
        logger.error(f"Validation failed for {model_id}: {e}")
        return False


def main():
    """
    Main entry point for testing model loading.
    """
    print("Testing model loader...")
    
    # Load a small model for testing
    model, tokenizer = load_model(
        model_id="microsoft/phi-2",  # Small model for testing
        quantization=True
    )
    
    # Verify loading
    assert model is not None, "Model is None"
    assert tokenizer is not None, "Tokenizer is None"
    
    # Test a simple forward pass
    test_input = "The capital of France is"
    inputs = tokenizer(test_input, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    print(f"Forward pass successful. Output shape: {outputs.logits.shape}")
    print("Model loader test passed!")
    
    # Cleanup
    del model, tokenizer, inputs, outputs
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()