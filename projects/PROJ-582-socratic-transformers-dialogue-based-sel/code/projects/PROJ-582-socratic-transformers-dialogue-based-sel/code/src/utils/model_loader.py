"""
Base model loader utility supporting 4-bit quantization via bitsandbytes.

This module implements memory-constrained model loading for CPU environments,
ensuring RSS stays below 7GB as per project constraints.
"""
import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import psutil
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Memory constraint: 7GB in bytes
MAX_MEMORY_RSS_BYTES = 7 * 1024 * 1024 * 1024

def load_model(
    model_name: str,
    device_map: str = "cpu",
    max_memory: Optional[Dict[str, Union[int, str]]] = None,
    trust_remote_code: bool = False,
    use_4bit: bool = True
) -> Tuple[Any, Any]:
    """
    Load a transformer model with 4-bit quantization for CPU execution.
    
    Args:
        model_name: HuggingFace model identifier or local path
        device_map: Device mapping strategy (default: "cpu")
        max_memory: Optional memory constraints per device
        trust_remote_code: Whether to trust remote code execution
        use_4bit: Enable 4-bit quantization via bitsandbytes
    
    Returns:
        Tuple of (model, tokenizer)
    
    Raises:
        MemoryError: If memory usage exceeds 7GB threshold during load
        ImportError: If required dependencies (bitsandbytes, psutil) are missing
    """
    logger.info(f"Loading model: {model_name} with 4-bit quantization on {device_map}")
    
    # Check memory before loading
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    logger.info(f"Initial memory usage: {initial_memory / (1024**2):.2f} MB")
    
    if initial_memory > MAX_MEMORY_RSS_BYTES * 0.8:
        logger.warning(f"Initial memory usage ({initial_memory / (1024**2):.2f} MB) is already high")
    
    # Configure 4-bit quantization
    if use_4bit:
        try:
            from bitsandbytes.nn import Linear4bit
            logger.info("bitsandbytes 4-bit quantization enabled")
            
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                llm_int8_skip_modules=["lm_head"]
            )
        except ImportError:
            logger.error("bitsandbytes not installed. Install with: pip install bitsandbytes")
            raise ImportError("bitsandbytes is required for 4-bit quantization")
    else:
        bnb_config = None
        logger.info("4-bit quantization disabled, loading in full precision")
    
    # Load tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=trust_remote_code,
        padding_side="left"
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    logger.info("Loading model...")
    model_kwargs = {
        "trust_remote_code": trust_remote_code,
        "torch_dtype": torch.float16,
        "device_map": device_map,
    }
    
    if bnb_config:
        model_kwargs["quantization_config"] = bnb_config
    
    if max_memory:
        model_kwargs["max_memory"] = max_memory
    
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **model_kwargs
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    # Memory check after loading
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    current_memory = process.memory_info().rss
    logger.info(f"Memory usage after load: {current_memory / (1024**2):.2f} MB")
    
    if current_memory > MAX_MEMORY_RSS_BYTES:
        error_msg = f"Memory usage ({current_memory / (1024**2):.2f} MB) exceeds 7GB limit"
        logger.error(error_msg)
        raise MemoryError(error_msg)
    
    # Verify model is frozen (no gradients)
    model.eval()
    for param in model.parameters():
        param.requires_grad = False
    
    logger.info(f"Model loaded successfully. Parameters: {model.num_parameters()}")
    return model, tokenizer

def get_model_card(model_name: str) -> Dict[str, Any]:
    """
    Retrieve model metadata from HuggingFace.
    
    Args:
        model_name: HuggingFace model identifier
    
    Returns:
        Dictionary containing model metadata
    """
    from transformers import AutoConfig
    
    try:
        config = AutoConfig.from_pretrained(model_name)
        return {
            "model_name": model_name,
            "model_type": config.model_type,
            "num_parameters": getattr(config, "hidden_size", None),
            "vocab_size": getattr(config, "vocab_size", None),
            "max_position_embeddings": getattr(config, "max_position_embeddings", None),
        }
    except Exception as e:
        logger.warning(f"Could not retrieve model card: {e}")
        return {"model_name": model_name, "error": str(e)}

def validate_model_compatibility(
    model_name: str,
    required_memory_gb: float = 7.0
) -> Tuple[bool, str]:
    """
    Validate if a model can be loaded within memory constraints.
    
    Args:
        model_name: HuggingFace model identifier
        required_memory_gb: Required memory in GB (default: 7.0)
    
    Returns:
        Tuple of (is_compatible, message)
    """
    from transformers import AutoConfig
    
    try:
        config = AutoConfig.from_pretrained(model_name)
        
        # Estimate memory: parameters * 4 bytes (float32) / 2 (4-bit) / 1e9
        # This is a rough estimate; actual usage depends on architecture
        num_params = getattr(config, "num_parameters", lambda: 0)()
        estimated_memory_gb = (num_params * 4) / (2 * 1e9)  # 4-bit quantization
        
        if estimated_memory_gb > required_memory_gb:
            return False, f"Estimated memory ({estimated_memory_gb:.2f} GB) exceeds limit ({required_memory_gb} GB)"
        
        return True, f"Model estimated at {estimated_memory_gb:.2f} GB, within {required_memory_gb} GB limit"
    
    except Exception as e:
        return False, f"Could not validate model: {e}"

def main():
    """Main entry point for model loader CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load a transformer model with 4-bit quantization")
    parser.add_argument("--model", type=str, default="microsoft/Phi-3-mini-4k-instruct",
                      help="HuggingFace model identifier")
    parser.add_argument("--check-only", action="store_true",
                      help="Only check compatibility, don't load")
    
    args = parser.parse_args()
    
    # Validate compatibility
    is_compatible, message = validate_model_compatibility(args.model)
    logger.info(message)
    
    if not is_compatible:
        logger.error("Model not compatible with memory constraints")
        sys.exit(1)
    
    if args.check_only:
        logger.info("Compatibility check passed. Exiting.")
        sys.exit(0)
    
    # Load model
    try:
        model, tokenizer = load_model(args.model)
        logger.info("Model loaded successfully")
        
        # Test inference with a simple prompt
        test_prompt = "What is 2+2?"
        inputs = tokenizer(test_prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                pad_token_id=tokenizer.pad_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Test response: {response}")
        
    except MemoryError as e:
        logger.error(f"Memory error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
