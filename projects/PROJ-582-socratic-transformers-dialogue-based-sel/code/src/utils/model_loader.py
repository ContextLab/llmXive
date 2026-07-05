"""
Model loader utility supporting low-bit quantization for CPU-constrained inference.

Implements fallback strategies for Limited RAM constraints using:
- bitsandbytes 4-bit quantization (CPU backend)
- GGUF model loading via llama-cpp-python (if available)
- Automatic fallback to smaller model sizes on OOM
"""

import os
import gc
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from transformers.utils import is_bitsandbytes_available

from src.utils.config import SocraticConfig, get_config
from src.utils.logging import SocraticLogger

# Configure logger
logger = SocraticLogger.get_logger("model_loader")


def _check_bitsandbytes() -> bool:
    """Check if bitsandbytes is available and compatible with CPU."""
    if not is_bitsandbytes_available():
        logger.warning("bitsandbytes not installed. Falling back to standard loading.")
        return False
    
    try:
        import bitsandbytes as bnb
        # Check if CPU backend is supported
        if not hasattr(bnb.nn, 'Linear4bit'):
            logger.warning("bitsandbytes 4-bit linear layer not available.")
            return False
        return True
    except Exception as e:
        logger.warning(f"bitsandbytes check failed: {e}")
        return False


def _load_gguf_model(
    model_path: str,
    n_ctx: int = 2048,
    n_threads: Optional[int] = None
) -> Tuple[Any, Any]:
    """
    Load a GGUF model using llama-cpp-python.
    
    Args:
        model_path: Path to the GGUF file
        n_ctx: Context window size
        n_threads: Number of threads (None for auto)
        
    Returns:
        Tuple of (model, tokenizer) - model is llama-cpp instance
    """
    try:
        from llama_cpp import Llama
        from transformers import AutoTokenizer
        
        logger.info(f"Loading GGUF model from {model_path}")
        
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads or os.cpu_count(),
            verbose=False
        )
        
        # For GGUF, we typically use a separate tokenizer or the one from the original model
        # Here we try to load the tokenizer from the same directory
        tokenizer_path = Path(model_path).parent
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_path,
            trust_remote_code=True
        )
        
        logger.info("GGUF model loaded successfully")
        return model, tokenizer
        
    except ImportError:
        logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        raise
    except Exception as e:
        logger.error(f"Failed to load GGUF model: {e}")
        raise


def _load_quantized_transformer(
    model_name: str,
    config: SocraticConfig,
    device: str = "cpu"
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load a transformer model with 4-bit quantization using bitsandbytes.
    
    Args:
        model_name: HuggingFace model identifier
        config: SocraticConfig instance
        device: Target device (default: cpu)
        
    Returns:
        Tuple of (model, tokenizer)
    """
    if not _check_bitsandbytes():
        logger.warning("bitsandbytes not available, loading in full precision")
        return _load_full_precision_model(model_name, device)
    
    logger.info(f"Loading {model_name} with 4-bit quantization on {device}")
    
    # Configure 4-bit quantization for CPU
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float32,  # Use float32 for CPU stability
        llm_int8_enable_fp32_cpu_offload=True,  # Enable CPU offloading
        llm_int8_has_fp16_weight=False,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="left"
    )
    
    # Add padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto" if device != "cpu" else "cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            torch_dtype=torch.float32,
        )
        
        logger.info("Model loaded with 4-bit quantization")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load quantized model: {e}")
        raise


def _load_full_precision_model(
    model_name: str,
    device: str = "cpu"
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load a transformer model in full precision (fallback).
    
    Args:
        model_name: HuggingFace model identifier
        device: Target device
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.warning(f"Loading {model_name} in full precision (no quantization)")
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="left"
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.float32,
        device_map="auto" if device != "cpu" else "cpu",
        low_cpu_mem_usage=True,
    )
    
    logger.info("Full precision model loaded")
    return model, tokenizer


def _try_fallback_model(
    primary_model: str,
    fallback_model: str = "microsoft/phi-1.5",
    config: Optional[SocraticConfig] = None
) -> Tuple[AutoModelForCausalLM, AutoTokenizer, str]:
    """
    Attempt to load a smaller fallback model on OOM.
    
    Args:
        primary_model: The original model that failed
        fallback_model: Smaller model to try
        config: Optional config for additional settings
        
    Returns:
        Tuple of (model, tokenizer, model_name_used)
    """
    logger.warning(f"OOM detected on {primary_model}. Attempting fallback to {fallback_model}")
    
    try:
        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        model, tokenizer = _load_quantized_transformer(fallback_model, config or get_config())
        logger.info(f"Successfully loaded fallback model: {fallback_model}")
        return model, tokenizer, fallback_model
        
    except Exception as e:
        logger.error(f"Fallback model {fallback_model} also failed: {e}")
        raise


def load_model(
    model_name: str,
    use_gguf: bool = False,
    fallback_model: Optional[str] = None,
    max_memory: Optional[Dict[str, Any]] = None,
    config: Optional[SocraticConfig] = None
) -> Tuple[Union[AutoModelForCausalLM, Any], AutoTokenizer, str]:
    """
    Main entry point for loading models with quantization and fallback support.
    
    Args:
        model_name: HuggingFace model identifier or path to GGUF file
        use_gguf: If True, attempt to load as GGUF format
        fallback_model: Optional smaller model to use on OOM (default: phi-1.5)
        max_memory: Optional max memory configuration
        config: SocraticConfig instance (uses global if None)
        
    Returns:
        Tuple of (model, tokenizer, model_name_used)
        
    Raises:
        RuntimeError: If all loading attempts fail
    """
    config = config or get_config()
    fallback_model = fallback_model or config.fallback_model
    
    logger.info(f"Attempting to load model: {model_name}")
    
    # Try GGUF if requested
    if use_gguf or model_name.endswith(".gguf"):
        try:
            model, tokenizer = _load_gguf_model(model_name)
            return model, tokenizer, model_name
        except Exception as e:
            logger.warning(f"GGUF loading failed: {e}. Trying transformer format.")
    
    # Try quantized transformer
    try:
        model, tokenizer = _load_quantized_transformer(model_name, config)
        return model, tokenizer, model_name
    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "OOM" in str(e):
            if fallback_model:
                return _try_fallback_model(model_name, fallback_model, config)
            else:
                raise RuntimeError("OOM and no fallback model specified") from e
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        if fallback_model:
            return _try_fallback_model(model_name, fallback_model, config)
        raise


def get_model_card(model_name: str) -> Dict[str, Any]:
    """
    Get metadata about a model from HuggingFace.
    
    Args:
        model_name: HuggingFace model identifier
        
    Returns:
        Dictionary with model metadata
    """
    try:
        from huggingface_hub import model_info
        
        info = model_info(model_name)
        
        return {
            "name": info.id,
            "description": info.description,
            "tags": info.tags,
            "pipeline_tag": info.pipeline_tag,
            "likes": info.likes,
            "downloads": info.downloads,
            "card_data": info.card_data,
        }
    except Exception as e:
        logger.warning(f"Could not fetch model card for {model_name}: {e}")
        return {"name": model_name, "error": str(e)}


def validate_model_compatibility(
    model_name: str,
    target_ram_gb: int = 7
) -> Dict[str, Any]:
    """
    Validate if a model can fit within target RAM constraints.
    
    Args:
        model_name: HuggingFace model identifier
        target_ram_gb: Target RAM in GB
        
    Returns:
        Dictionary with compatibility assessment
    """
    try:
        from huggingface_hub import model_info
        
        info = model_info(model_name)
        
        # Estimate model size from safetensors or pytorch files
        model_size_gb = 0
        if info.siblings:
            for file in info.siblings:
                if file.rfilename.endswith((".safetensors", ".bin")):
                    if file.size:
                        model_size_gb += file.size / (1024**3)
        
        # Account for quantization (4-bit = ~1/4 size)
        quantized_size_gb = model_size_gb / 4
        
        return {
            "model_name": model_name,
            "estimated_full_size_gb": round(model_size_gb, 2),
            "estimated_quantized_size_gb": round(quantized_size_gb, 2),
            "target_ram_gb": target_ram_gb,
            "fits_full": model_size_gb <= target_ram_gb,
            "fits_quantized": quantized_size_gb <= target_ram_gb,
            "recommendation": "quantized" if quantized_size_gb <= target_ram_gb else "fallback_needed",
        }
    except Exception as e:
        logger.warning(f"Could not validate model {model_name}: {e}")
        return {
            "model_name": model_name,
            "error": str(e),
            "recommendation": "unknown"
        }
