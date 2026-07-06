"""
Model loading utilities for CPU-only inference.

Provides functions to load and unload quantized CodeGen models on CPU.
"""

import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger
from utils.config import ensure_directories

logger = get_logger(__name__)

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers import BitsAndBytesConfig
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("Transformers library not available. Inference will fail.")

def load_model(model_name: str = "CodeGen-350M") -> Tuple[Any, Any]:
    """
    Load a quantized CodeGen model for CPU inference.
    
    Args:
        model_name: Name of the model to load (e.g., "CodeGen-350M")
    
    Returns:
        Tuple of (model, tokenizer)
    
    Raises:
        ImportError: If required libraries are not installed
        RuntimeError: If model loading fails
    """
    if not HAS_TRANSFORMERS:
        raise ImportError(
            "Transformers library not installed. "
            "Please install with: pip install transformers torch bitsandbytes"
        )
    
    ensure_directories()
    
    # Map model names to HuggingFace identifiers
    model_map = {
        "CodeGen-350M": "salesforce/codegen-350m-mono",
        "CodeGen-small": "salesforce/codegen-350m-mono",
        "CodeGen-2B": "salesforce/codegen-2b-mono"
    }
    
    hf_model_name = model_map.get(model_name, model_name)
    
    logger.info(f"Loading model: {hf_model_name} (mapped from {model_name})")
    
    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            hf_model_name,
            trust_remote_code=True
        )
        
        # Configure for CPU-only, quantized inference
        # Note: bitsandbytes 4-bit/8-bit requires CUDA, so we use standard quantization for CPU
        # For CPU, we'll load in 16-bit but with low precision to save memory
        model = AutoModelForCausalLM.from_pretrained(
            hf_model_name,
            torch_dtype=torch.float16,  # Use half precision for memory efficiency
            low_cpu_mem_usage=True,
            device_map="cpu",  # Explicitly force CPU
            trust_remote_code=True
        )
        
        # Ensure model is in eval mode
        model.eval()
        
        logger.info(f"Model loaded successfully: {hf_model_name}")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model {hf_model_name}: {str(e)}")
        raise RuntimeError(f"Model loading failed: {str(e)}") from e

def unload_model(model: Any, tokenizer: Any) -> None:
    """
    Unload model and tokenizer to free memory.
    
    Args:
        model: The loaded model
        tokenizer: The loaded tokenizer
    """
    try:
        if model is not None:
            del model
        if tokenizer is not None:
            del tokenizer
        
        # Force garbage collection
        import gc
        gc.collect()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Model unloaded successfully")
    except Exception as e:
        logger.warning(f"Error during model unload: {str(e)}")

def main():
    """Test model loading."""
    logger.info("Testing model loading...")
    try:
        model, tokenizer = load_model("CodeGen-350M")
        logger.info("Model loading test passed")
        unload_model(model, tokenizer)
    except Exception as e:
        logger.error(f"Model loading test failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
