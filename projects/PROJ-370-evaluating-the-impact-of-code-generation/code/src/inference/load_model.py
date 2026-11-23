import logging
import torch
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from config.settings import get_config, ensure_directories

# Import memory watchdog to enforce FR-015 (≤7GB limit)
from src.utils.memory_watchdog import get_memory_usage_bytes, check_memory_limit, MemoryLimitExceeded

logger = logging.getLogger(__name__)

# Constants
MODEL_ID = "bigcode/starcoder2-3b"
MEMORY_LIMIT_GB = 7
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 * 1024 * 1024

def load_model_and_tokenizer(
    model_id: Optional[str] = None,
    device_map: str = "auto",
    low_cpu_mem_usage: bool = True,
    max_memory: Optional[Dict[str, Any]] = None
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load StarCoder2-3B model and tokenizer.
    
    Args:
        model_id: Model identifier (defaults to bigcode/starcoder2-3b)
        device_map: Device mapping strategy (default: "auto")
        low_cpu_mem_usage: Optimize CPU memory usage (default: True)
        max_memory: Optional max memory constraints per device
    
    Returns:
        Tuple of (model, tokenizer)
    
    Raises:
        MemoryLimitExceeded: If memory usage exceeds 7GB during loading
        RuntimeError: If model loading fails
    """
    if model_id is None:
        model_id = MODEL_ID
    
    logger.info(f"Loading model: {model_id}")
    logger.info(f"Device map: {device_map}, Low CPU memory: {low_cpu_mem_usage}")
    
    # Load tokenizer first
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        trust_remote_code=True
    )
    
    # Configure model loading
    model_kwargs = {
        "device_map": device_map,
        "low_cpu_mem_usage": low_cpu_mem_usage,
        "trust_remote_code": True,
    }
    
    # Add memory constraints if provided
    if max_memory is not None:
        model_kwargs["max_memory"] = max_memory
    
    # Check memory usage before loading
    pre_load_memory = get_memory_usage_bytes()
    logger.info(f"Memory usage before loading: {pre_load_memory / (1024**3):.2f} GB")
    
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            **model_kwargs
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")
    
    # Check memory usage after loading
    post_load_memory = get_memory_usage_bytes()
    memory_delta = post_load_memory - pre_load_memory
    logger.info(f"Memory usage after loading: {post_load_memory / (1024**3):.2f} GB")
    logger.info(f"Memory delta: {memory_delta / (1024**3):.2f} GB")
    
    # Verify memory constraint (FR-015)
    if post_load_memory > MEMORY_LIMIT_BYTES:
        logger.error(f"Memory limit exceeded: {post_load_memory / (1024**3):.2f} GB > {MEMORY_LIMIT_GB} GB")
        raise MemoryLimitExceeded(
            f"Model loading exceeded memory limit of {MEMORY_LIMIT_GB}GB. "
            f"Current usage: {post_load_memory / (1024**3):.2f} GB"
        )
    
    logger.info(f"Successfully loaded {model_id}")
    return model, tokenizer

def load_model_for_inference(
    model_id: Optional[str] = None,
    precision: str = "default"
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load model configured for inference with memory constraints.
    
    Args:
        model_id: Model identifier
        precision: Precision mode (default: "default" for FP16/BF16 if available)
    
    Returns:
        Tuple of (model, tokenizer)
    
    Raises:
        MemoryLimitExceeded: If memory usage exceeds 7GB
    """
    # Default precision uses model's native precision (usually FP16 for StarCoder2)
    # StarCoder2-3B is designed to run efficiently in FP16
    model, tokenizer = load_model_and_tokenizer(
        model_id=model_id,
        device_map="auto",
        low_cpu_mem_usage=True
    )
    
    logger.info(f"Model loaded with {precision} precision")
    return model, tokenizer

def main():
    """Main entry point for testing model loading."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    ensure_directories()
    
    try:
        logger.info("Starting model load test...")
        model, tokenizer = load_model_for_inference()
        logger.info(f"Model loaded successfully. Model type: {type(model)}")
        logger.info(f"Tokenizer type: {type(tokenizer)}")
        
        # Verify model is on correct device
        if hasattr(model, 'hf_device_map'):
            logger.info(f"Model device map: {model.hf_device_map}")
        
        return 0
    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
