"""
Model Loader Utility for Socratic Transformers.

Implements base model loading with support for Low-bit quantization (4-bit via bitsandbytes)
to satisfy Limited RAM constraints (CPU/Free-tier environments).
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

# Import local config to ensure consistent seed/model paths
from src.utils.config import get_config

logger = logging.getLogger(__name__)


def _get_quantization_config() -> Optional[BitsAndBytesConfig]:
    """
    Returns a BitsAndBytesConfig for 4-bit quantization if CUDA is available or
    if the environment explicitly requests low-memory mode.
    Falls back to None for standard loading (e.g., if running on a GPU with enough VRAM).
    """
    config = get_config()
    
    # Check if we are in a constrained environment (CPU or low VRAM)
    # The spec requires Low-bit quantization (GGUF or bitsandbytes CPU backend)
    # We prioritize bitsandbytes as it is already in requirements.txt (T002)
    
    use_cpu = config.get("use_cpu", False)
    low_memory_mode = config.get("low_memory_mode", True)
    
    if use_cpu or low_memory_mode:
        logger.info("Initializing 4-bit quantization config for low-memory environment.")
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            # Important for CPU/Free-tier: allow non-strict dtype if needed
            llm_int8_enable_fp32_cpu_offload=True if use_cpu else False,
        )
    
    return None


def load_model(
    model_name_or_path: str,
    tokenizer_name_or_path: Optional[str] = None,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
    peft_adapter_path: Optional[str] = None,
) -> Tuple[Union[PreTrainedModel, PeftModel], PreTrainedTokenizer]:
    """
    Loads a base model and tokenizer with support for 4-bit quantization.
    
    Args:
        model_name_or_path: HuggingFace model ID or local path.
        tokenizer_name_or_path: Optional separate tokenizer path. Defaults to model path.
        device_map: Optional device mapping (e.g., "auto", "cpu"). If None, inferred from config.
        peft_adapter_path: Optional path to LoRA adapters to load on top of the base model.
        
    Returns:
        Tuple of (Model, Tokenizer).
        
    Raises:
        ValueError: If the model cannot be loaded due to memory constraints or missing files.
        RuntimeError: If loading fails unexpectedly.
    """
    if tokenizer_name_or_path is None:
        tokenizer_name_or_path = model_name_or_path
        
    logger.info(f"Loading model: {model_name_or_path}")
    logger.info(f"Loading tokenizer: {tokenizer_name_or_path}")
    
    # Determine quantization
    quantization_config = _get_quantization_config()
    
    # Determine device map
    if device_map is None:
        config = get_config()
        if config.get("use_cpu", False):
            device_map = "cpu"
        else:
            # Let transformers auto-detect if GPU is available and sufficient
            # But with 4-bit, we often want "auto" to split layers
            device_map = "auto" if torch.cuda.is_available() else "cpu"
    
    # Load Tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_name_or_path,
            trust_remote_code=True,
            padding_side="right",
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
    except Exception as e:
        logger.error(f"Failed to load tokenizer: {e}")
        raise
    
    # Load Model
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            quantization_config=quantization_config,
            device_map=device_map,
            trust_remote_code=True,
            torch_dtype=torch.float16 if quantization_config else torch.float32,
            # Avoid memory issues during loading
            low_cpu_mem_usage=True,
        )
        
        # If PEFT adapters are provided, load them
        if peft_adapter_path:
            logger.info(f"Loading PEFT adapters from: {peft_adapter_path}")
            model = PeftModel.from_pretrained(model, peft_adapter_path)
            model = model.merge_and_unload() if config.get("merge_adapters", False) else model
            
        logger.info("Model loaded successfully.")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        # Explicitly fail loudly as per constraints
        raise RuntimeError(f"Model loading failed for {model_name_or_path}: {e}") from e


def get_model_card(model: PreTrainedModel) -> Dict[str, Any]:
    """
    Extracts basic metadata from a loaded model for logging and validation.
    
    Args:
        model: The loaded PreTrainedModel instance.
        
    Returns:
        Dictionary containing model type, config keys, and parameter count.
    """
    if hasattr(model, "config"):
        config = model.config
        return {
            "model_type": getattr(config, "model_type", "unknown"),
            "hidden_size": getattr(config, "hidden_size", None),
            "num_attention_heads": getattr(config, "num_attention_heads", None),
            "num_hidden_layers": getattr(config, "num_hidden_layers", None),
            "vocab_size": getattr(config, "vocab_size", None),
            "quantized": hasattr(model, "hf_quantizer") or str(model.dtype) != "torch.float32",
            "device_map": str(model.hf_device_map) if hasattr(model, "hf_device_map") else "single",
        }
    return {"error": "Could not retrieve model config"}


def validate_model_compatibility(
    model: PreTrainedModel,
    required_architectures: Optional[list] = None,
) -> bool:
    """
    Validates that the loaded model meets specific architectural requirements.
    
    Args:
        model: The loaded model.
        required_architectures: List of allowed architecture strings (e.g., ["LlamaForCausalLM"]).
        
    Returns:
        True if compatible, False otherwise.
    """
    if required_architectures is None:
        return True
        
    if not hasattr(model, "config"):
        return False
        
    arch = getattr(model.config, "architectures", [])
    if not arch:
        return False
        
    # Check if any of the model's architectures match the required list
    return any(any(req in str(arch_type) for arch_type in arch) for req in required_architectures)


def main():
    """
    Entry point for testing the model loader independently.
    Attempts to load a small test model (e.g., TinyLlama) to verify quantization setup.
    """
    # Ensure directories exist
    config = get_config()
    config.ensure_directories()
    
    # Use a small model for testing to avoid long downloads in CI/CD
    # In production, this would be set via environment variables or config
    test_model = config.get("test_model", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    
    logger.info(f"Running model loader validation with model: {test_model}")
    
    try:
        model, tokenizer = load_model(test_model)
        
        card = get_model_card(model)
        logger.info(f"Model Card: {card}")
        
        # Validate
        is_valid = validate_model_compatibility(model)
        logger.info(f"Compatibility Check: {'PASSED' if is_valid else 'FAILED'}")
        
        # Test a simple forward pass to ensure quantization works
        input_text = "Hello, world."
        inputs = tokenizer(input_text, return_tensors="pt")
        
        # Move inputs to device if model is on GPU
        if hasattr(model, "device"):
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        logger.info(f"Forward pass successful. Output shape: {outputs.logits.shape}")
        logger.info("Model loader validation COMPLETE.")
        
    except Exception as e:
        logger.error(f"Validation FAILED: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()
