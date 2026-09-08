"""
Model Factory for llmXive.

Provides functions to load low-capacity models (Phi-2, Qwen1.5-1.8B)
with 8-bit CPU quantization, ensuring strict memory constraints and
proper error handling for OOM scenarios.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from llmxive.exceptions import ERR_CPU_LOAD_FAIL
import logging

logger = logging.getLogger(__name__)

# Supported model identifiers
SUPPORTED_MODELS = {
    "phi-2": "microsoft/phi-2",
    "qwen1.5-1.8b": "Qwen/Qwen1.5-1.8B"
}

def _get_quantization_config():
    """
    Returns a BitsAndBytesConfig for 8-bit CPU quantization.
    Note: 8-bit quantization on CPU via bitsandbytes requires specific
    compilation or fallback behavior. We configure for 8-bit generally,
    but ensure device_map is 'cpu'.
    """
    return BitsAndBytesConfig(
        load_in_8bit=True,
        llm_int8_enable_fp32_cpu_offload=True,
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"],
    )

def load_model(model_id: str, device: str = "cpu", max_memory: str = "6.5GB"):
    """
    Loads a model from Hugging Face Hub with 8-bit quantization on CPU.

    Args:
        model_id (str): The model identifier (e.g., "phi-2", "qwen1.5-1.8b").
        device (str): Target device. Must be "cpu".
        max_memory (str): Maximum memory limit string (for logging/validation).

    Returns:
        tuple: (model, tokenizer)

    Raises:
        ERR_CPU_LOAD_FAIL: If the model fails to load due to OOM or other critical errors.
        ValueError: If model_id is not supported or device is not 'cpu'.
    """
    if device != "cpu":
        raise ValueError("This factory currently only supports CPU loading (device='cpu').")

    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model_id: {model_id}. Supported: {list(SUPPORTED_MODELS.keys())}")

    hf_model_name = SUPPORTED_MODELS[model_id]
    logger.info(f"Loading model '{model_id}' ({hf_model_name}) with 8-bit CPU quantization...")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            hf_model_name,
            trust_remote_code=True,
            padding_side="left"
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        quant_config = _get_quantization_config()

        # Attempt to load model
        model = AutoModelForCausalLM.from_pretrained(
            hf_model_name,
            quantization_config=quant_config,
            device_map="cpu",
            torch_dtype=torch.float32, # CPU typically uses float32
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )

        logger.info(f"Model '{model_id}' loaded successfully.")
        return model, tokenizer

    except (RuntimeError, MemoryError, OSError) as e:
        # Check for OOM indicators in error message
        error_msg = str(e).lower()
        if "oom" in error_msg or "out of memory" in error_msg or "cuda" in error_msg:
            logger.error(f"OOM detected while loading {model_id}: {e}")
            raise ERR_CPU_LOAD_FAIL(f"Failed to load {model_id} due to OOM: {e}") from e
        
        # If it's a generic load error that isn't explicitly OOM, we still raise
        # because the requirement is to raise on failure to load for CPU constraints.
        logger.error(f"Failed to load model {model_id}: {e}")
        raise ERR_CPU_LOAD_FAIL(f"Failed to load {model_id} with 8-bit quantization: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error loading model {model_id}: {e}")
        raise ERR_CPU_LOAD_FAIL(f"Unexpected error loading {model_id}: {e}") from e

def get_model_size_info(model_id: str):
    """
    Returns estimated size info for a model (parameters).
    """
    # These are approximations for documentation/logging purposes
    # Actual loading handles the real memory constraints.
    info = {
        "phi-2": {"params": "2.7B", "approx_ram_gb": 4.5},
        "qwen1.5-1.8b": {"params": "1.8B", "approx_ram_gb": 3.0}
    }
    return info.get(model_id, {"params": "Unknown", "approx_ram_gb": None})