"""
Model loading utilities for llmXive.

Provides CPU-quantized (4-bit) small language model loading using
llama-cpp-python and transformers.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

try:
    from llama_cpp import Llama
    from llama_cpp.llama import Llama as LlamaType
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None
    LlamaType = None

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    AutoModelForCausalLM = None
    AutoTokenizer = None
    BitsAndBytesConfig = None

from src.lib.config import get_config

logger = logging.getLogger(__name__)

# Default model paths and configurations
DEFAULT_MODEL_REPO = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
DEFAULT_MODEL_FILE = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
DEFAULT_MAX_CONTEXT = 4096
DEFAULT_N_CTX = 4096
DEFAULT_N_BATCH = 512
DEFAULT_N_THREADS = 4

def load_quantized_model(
    model_path: Optional[str] = None,
    model_repo: Optional[str] = None,
    model_file: Optional[str] = None,
    n_ctx: int = DEFAULT_N_CTX,
    n_batch: int = DEFAULT_N_BATCH,
    n_threads: int = DEFAULT_N_THREADS,
    max_tokens: Optional[int] = None,
    use_llama_cpp: bool = True,
    **kwargs
) -> Tuple[Any, Any]:
    """
    Load a CPU-quantized (4-bit) small language model.
    
    Args:
        model_path: Path to the model file (GGUF format for llama-cpp).
        model_repo: HuggingFace repo ID (if model_path is not provided).
        model_file: Model filename in the repo (if model_path is not provided).
        n_ctx: Context window size.
        n_batch: Batch size for prompt processing.
        n_threads: Number of CPU threads to use.
        max_tokens: Maximum tokens to generate (for tokenizer).
        use_llama_cpp: If True, use llama-cpp-python; else use transformers.
        **kwargs: Additional arguments passed to the model loader.
    
    Returns:
        Tuple of (model, tokenizer)
    
    Raises:
        RuntimeError: If model loading fails or required dependencies are missing.
        FileNotFoundError: If model file is not found.
    """
    config = get_config()
    
    if use_llama_cpp:
        return _load_llama_cpp_model(
            model_path=model_path,
            model_repo=model_repo,
            model_file=model_file,
            n_ctx=n_ctx,
            n_batch=n_batch,
            n_threads=n_threads,
            **kwargs
        )
    else:
        return _load_transformers_model(
            model_repo=model_repo or DEFAULT_MODEL_REPO,
            n_ctx=n_ctx,
            max_tokens=max_tokens,
            **kwargs
        )

def _load_llama_cpp_model(
    model_path: Optional[str] = None,
    model_repo: Optional[str] = None,
    model_file: Optional[str] = None,
    n_ctx: int = DEFAULT_N_CTX,
    n_batch: int = DEFAULT_N_BATCH,
    n_threads: int = DEFAULT_N_THREADS,
    **kwargs
) -> Tuple[LlamaType, None]:
    """
    Load a GGUF model using llama-cpp-python.
    
    This function handles 4-bit quantized models optimized for CPU inference.
    """
    if not LLAMA_CPP_AVAILABLE:
        raise RuntimeError(
            "llama-cpp-python is not installed. Install it with: "
            "pip install llama-cpp-python"
        )
    
    # Resolve model path
    if model_path is None:
        if model_repo is None:
            model_repo = DEFAULT_MODEL_REPO
        if model_file is None:
            model_file = DEFAULT_MODEL_FILE
        
        # Check if file exists locally
        local_model_path = Path(model_repo) / model_file
        if not local_model_path.exists():
            # Try to download from HuggingFace
            try:
                from huggingface_hub import hf_hub_download
                logger.info(f"Downloading model from {model_repo}/{model_file}...")
                model_path = hf_hub_download(
                    repo_id=model_repo,
                    filename=model_file,
                    cache_dir=config.get("cache_dir", "./artifacts/models")
                )
            except ImportError:
                raise RuntimeError(
                    "huggingface_hub is not installed. Install it with: "
                    "pip install huggingface_hub"
                )
        else:
            model_path = str(local_model_path)
    
    # Verify file exists
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    logger.info(f"Loading GGUF model from: {model_path}")
    logger.info(f"Context: {n_ctx}, Batch: {n_batch}, Threads: {n_threads}")
    
    try:
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_batch=n_batch,
            n_threads=n_threads,
            n_gpu_layers=0,  # CPU only
            verbose=False,
            **kwargs
        )
        logger.info(f"Successfully loaded model: {model_path}")
        return model, None  # No tokenizer needed for llama-cpp
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Model loading failed: {e}") from e

def _load_transformers_model(
    model_repo: str,
    n_ctx: int = DEFAULT_N_CTX,
    max_tokens: Optional[int] = None,
    **kwargs
) -> Tuple[Any, Any]:
    """
    Load a quantized model using transformers with bitsandbytes.
    
    This function loads 4-bit quantized models for CPU inference.
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError(
            "torch and transformers are not installed. Install them with: "
            "pip install torch transformers"
        )
    
    # Check for bitsandbytes
    try:
        import bitsandbytes
        bitsandbytes_available = True
    except ImportError:
        bitsandbytes_available = False
    
    if not bitsandbytes_available:
        raise RuntimeError(
            "bitsandbytes is not installed. Install it with: "
            "pip install bitsandbytes"
        )
    
    logger.info(f"Loading quantized model from: {model_repo}")
    
    try:
        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_repo,
            trust_remote_code=True
        )
        
        # Set max length if not specified
        if max_tokens is None:
            max_tokens = n_ctx
        
        tokenizer.model_max_length = max_tokens
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_repo,
            quantization_config=bnb_config,
            device_map="cpu",  # Force CPU
            trust_remote_code=True,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        
        logger.info(f"Successfully loaded quantized model: {model_repo}")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load transformers model: {e}")
        raise RuntimeError(f"Model loading failed: {e}") from e

def get_model_info(model: Any) -> Dict[str, Any]:
    """
    Get information about a loaded model.
    
    Args:
        model: The loaded model instance.
    
    Returns:
        Dictionary with model information.
    """
    info = {
        "type": type(model).__name__,
        "model_class": model.__class__.__module__ + "." + model.__class__.__name__
    }
    
    if hasattr(model, "n_ctx"):
        info["context_length"] = model.n_ctx
    
    if hasattr(model, "model_path"):
        info["model_path"] = model.model_path
    
    return info

def validate_model_compatibility(model_path: str) -> bool:
    """
    Validate if a model path is compatible with CPU-quantized loading.
    
    Args:
        model_path: Path to the model file.
    
    Returns:
        True if compatible, False otherwise.
    """
    path = Path(model_path)
    
    # Check for GGUF format
    if path.suffix.lower() == ".gguf":
        return LLAMA_CPP_AVAILABLE
    
    # Check for HuggingFace format
    if path.is_dir() or "/" in str(path):
        return TORCH_AVAILABLE and os.path.exists(path)
    
    return False

def clear_model_cache():
    """Clear model cache if available."""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Model cache cleared")
    except Exception as e:
        logger.warning(f"Failed to clear cache: {e}")