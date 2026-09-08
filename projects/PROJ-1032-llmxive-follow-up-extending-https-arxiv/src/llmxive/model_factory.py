"""
Model Factory for llmXive.

Handles loading of Phi-2 and Qwen1.5-1.8B models with 8-bit CPU quantization.
Implements strict OOM handling via ERR_CPU_LOAD_FAIL.
"""
import torch
import logging
from typing import Dict, Any, Optional, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from src.llmxive.exceptions import ERR_CPU_LOAD_FAIL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported models mapping model_id to config parameters
SUPPORTED_MODELS: Dict[str, Dict[str, Any]] = {
    "microsoft/phi-2": {
        "trust_remote_code": True,
        "max_memory": None,
        "device_map": "cpu",
    },
    "Qwen/Qwen1.5-1.8B": {
        "trust_remote_code": False,
        "max_memory": None,
        "device_map": "cpu",
    }
}

def _get_quantization_config() -> BitsAndBytesConfig:
    """
    Returns the BitsAndBytesConfig for 8-bit CPU quantization.
    Note: bnb_4bit_compute_dtype is set to torch.float32 for stability on CPU.
    """
    return BitsAndBytesConfig(
        load_in_8bit=True,
        llm_int8_threshold=6.0,
        llm_int8_has_fp16_weight=False,
        # Ensure computation happens in float32 for CPU stability
        llm_int8_skip_modules=["lm_head"],
    )

def load_model(
    model_id: str,
    device: str = "cpu",
    use_quantization: bool = True
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Loads a model from the supported list with 8-bit CPU quantization.

    Args:
        model_id: The HuggingFace model identifier (e.g., "microsoft/phi-2").
        device: Target device (default "cpu").
        use_quantization: Whether to apply 8-bit quantization.

    Returns:
        Tuple of (model, tokenizer).

    Raises:
        ERR_CPU_LOAD_FAIL: If the model fails to load due to OOM or memory issues.
        ValueError: If model_id is not in SUPPORTED_MODELS.
    """
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Model '{model_id}' is not in the supported list: {list(SUPPORTED_MODELS.keys())}")

    config_params = SUPPORTED_MODELS[model_id]
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=config_params.get("trust_remote_code", False))

    # Ensure tokenizer has a pad token for RL stability if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    try:
        logger.info(f"Loading model {model_id} on {device} with quantization={use_quantization}...")

        # Prepare quantization config
        quantization_config = _get_quantization_config() if use_quantization else None

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=config_params.get("trust_remote_code", False),
            device_map=config_params.get("device_map", "cpu"),
            torch_dtype=torch.float32, # Force float32 for CPU to avoid half-precision issues on some CPUs
            quantization_config=quantization_config,
            low_cpu_mem_usage=True,
        )

        logger.info(f"Successfully loaded model {model_id}.")
        return model, tokenizer

    except RuntimeError as e:
        # Catch OOM or memory allocation errors specific to torch/transformers
        error_msg = str(e).lower()
        if "oom" in error_msg or "out of memory" in error_msg or "cuda" in error_msg:
            logger.error(f"OOM error occurred while loading {model_id}: {e}")
            raise ERR_CPU_LOAD_FAIL(f"Failed to load model {model_id} due to memory constraints: {e}") from e
        else:
            # Re-raise if it's a different runtime error
            raise e
    except MemoryError as e:
        logger.error(f"MemoryError occurred while loading {model_id}: {e}")
        raise ERR_CPU_LOAD_FAIL(f"Failed to load model {model_id} due to system memory exhaustion: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error loading {model_id}: {e}")
        # Wrap generic exceptions that look like resource exhaustion
        if "memory" in str(e).lower() or "alloc" in str(e).lower():
            raise ERR_CPU_LOAD_FAIL(f"Failed to load model {model_id} due to resource constraints: {e}") from e
        raise

def get_model_size_info(model_id: str) -> Dict[str, Any]:
    """
    Retrieves metadata about the model size (parameters) without loading weights.
    Useful for logging and validation.

    Args:
        model_id: The HuggingFace model identifier.

    Returns:
        Dictionary with model metadata.
    """
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Model '{model_id}' is not in the supported list.")

    # We can try to get config without loading weights
    from transformers import AutoConfig
    try:
        config = AutoConfig.from_pretrained(model_id, trust_remote_code=SUPPORTED_MODELS[model_id].get("trust_remote_code", False))
        num_params = getattr(config, "num_parameters", None)
        # Fallback if num_parameters isn't directly on config for some models
        if num_params is None:
            # Approximate calculation if possible, otherwise unknown
            num_params = "Unknown"

        return {
            "model_id": model_id,
            "num_parameters": num_params,
            "hidden_size": getattr(config, "hidden_size", None),
            "num_attention_heads": getattr(config, "num_attention_heads", None),
            "num_hidden_layers": getattr(config, "num_hidden_layers", None),
        }
    except Exception as e:
        logger.warning(f"Could not retrieve size info for {model_id}: {e}")
        return {
            "model_id": model_id,
            "num_parameters": "Unknown",
            "error": str(e)
        }