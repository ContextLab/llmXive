"""
Model Loader Utility for Socratic Transformers Project.

Supports Low-bit quantization (GGUF or bitsandbytes CPU backend) to fit
Limited RAM constraints (approx. 7GB RAM / 14GB Disk).

This module provides functions to load base models and tokenizers with
hardware-aware quantization settings, ensuring compatibility with CPU-only
or memory-constrained environments.
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

# Import local config to ensure consistency with project settings
from src.utils.config import get_config, SocraticConfig

# Setup logger
logger = logging.getLogger(__name__)


def _get_quantization_config(
    quant_type: str = "4bit",
    use_cpu: bool = True,
    compute_dtype: Optional[torch.dtype] = None,
) -> Optional[Union[BitsAndBytesConfig, Dict[str, Any]]]:
    """
    Constructs the quantization configuration for the model.

    Args:
        quant_type: '4bit' (default), '8bit', or 'none'.
        use_cpu: If True, optimizes for CPU inference (bitsandbytes CPU backend).
        compute_dtype: The dtype to use for computation (defaults to float16 or bfloat16).

    Returns:
        A BitsAndBytesConfig object or None if no quantization is requested.

    Raises:
        ValueError: If an unsupported quantization type is requested.
    """
    if quant_type == "none" or quant_type is None:
        return None

    if compute_dtype is None:
        # Default to float16 if not specified, unless bfloat16 is forced by env
        compute_dtype = torch.float16
        if os.getenv("FORCE_BFLOAT16", "false").lower() == "true":
            compute_dtype = torch.bfloat16

    if quant_type == "4bit":
        # Configure for 4-bit quantization
        # double_quant: Apply nested quantization for better memory savings
        # quant_type: 'nf4' (Normal Float 4) is generally more stable than 'fp4'
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_quant_storage=torch.uint8, # Storage format
            llm_int8_enable_fp32_cpu_offload=use_cpu, # Critical for CPU offload
        )
        logger.info(
            f"Configured 4-bit quantization with NF4, double quant, "
            f"compute_dtype={compute_dtype}, CPU offload={use_cpu}"
        )
        return quant_config

    elif quant_type == "8bit":
        # Configure for 8-bit quantization
        quant_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=True,
        )
        logger.info("Configured 8-bit quantization")
        return quant_config

    else:
        raise ValueError(f"Unsupported quantization type: {quant_type}")


def load_model(
    model_name_or_path: str,
    quant_type: str = "4bit",
    use_cpu: bool = True,
    trust_remote_code: bool = False,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Loads a model and tokenizer with low-bit quantization support.

    This function attempts to load the model using `bitsandbytes` for 4-bit or 8-bit
    quantization. If `use_cpu` is True, it attempts to offload layers to CPU memory
    to fit within tight RAM constraints.

    Args:
        model_name_or_path: HuggingFace model identifier or local path.
        quant_type: '4bit' (default), '8bit', or 'none'.
        use_cpu: If True, enables CPU offload strategies.
        trust_remote_code: Whether to trust remote code from the model repo.
        device_map: Optional explicit device map. If None, 'auto' is used.

    Returns:
        Tuple of (model, tokenizer).

    Raises:
        RuntimeError: If the model fails to load due to memory constraints or missing dependencies.
        FileNotFoundError: If the model path is invalid.
    """
    logger.info(f"Attempting to load model: {model_name_or_path}")
    logger.info(f"Quantization: {quant_type}, CPU Mode: {use_cpu}")

    # Validate quantization type
    if quant_type not in ["4bit", "8bit", "none"]:
        raise ValueError(f"Invalid quant_type '{quant_type}'. Must be '4bit', '8bit', or 'none'.")

    # Prepare quantization config
    bnb_config = _get_quantization_config(
        quant_type=quant_type,
        use_cpu=use_cpu,
        compute_dtype=torch.float16,
    )

    # Determine device map
    if device_map is None:
        if use_cpu:
            # 'auto' with bitsandbytes often handles offloading, but explicit 'cpu' or
            # 'balanced_low_0' might be safer for strict RAM limits.
            # We use 'auto' and let bitsandbytes handle the offloading if llm_int8_enable_fp32_cpu_offload is set.
            device_map = "auto"
        else:
            device_map = "auto"

    try:
        # Load Tokenizer first
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=trust_remote_code,
            padding_side="right", # Standard for generation
            token=os.getenv("HF_TOKEN"),
        )

        # Ensure tokenizer has a pad token if it doesn't
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.warning("Pad token not found, set to eos_token.")

        # Load Model
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            quantization_config=bnb_config,
            device_map=device_map,
            trust_remote_code=trust_remote_code,
            torch_dtype=torch.float16, # Base dtype, quantization config overrides
            token=os.getenv("HF_TOKEN"),
            low_cpu_mem_usage=True, # Essential for large models on limited RAM
        )

        logger.info(f"Successfully loaded model: {model_name_or_path}")
        logger.info(f"Model device map: {model.hf_device_map if hasattr(model, 'hf_device_map') else 'N/A'}")

        # Force garbage collection to free up memory after loading
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_name_or_path}: {e}")
        raise RuntimeError(f"Model loading failed: {e}") from e


def get_model_card(model: PreTrainedModel) -> Dict[str, Any]:
    """
    Extracts metadata from the loaded model.

    Args:
        model: The loaded PreTrainedModel instance.

    Returns:
        Dictionary containing model name, config info, and quantization status.
    """
    card = {
        "model_name": model.name_or_path,
        "config": {
            "model_type": model.config.model_type,
            "hidden_size": getattr(model.config, "hidden_size", None),
            "num_attention_heads": getattr(model.config, "num_attention_heads", None),
            "num_hidden_layers": getattr(model.config, "num_hidden_layers", None),
            "vocab_size": getattr(model.config, "vocab_size", None),
        },
        "quantization": "4bit" if hasattr(model, "hf_quantizer") else "none",
        "device_map": getattr(model, "hf_device_map", None),
    }
    return card


def validate_model_compatibility(
    model_name: str,
    required_quant: str = "4bit",
    max_ram_gb: float = 7.0,
) -> bool:
    """
    Validates if a model is compatible with the current hardware constraints.

    This is a heuristic check based on model size estimates.

    Args:
        model_name: HuggingFace model identifier.
        required_quant: Required quantization type.
        max_ram_gb: Maximum available RAM in GB.

    Returns:
        True if compatible, False otherwise.
    """
    # Heuristic: Estimate RAM usage based on parameter count
    # 4-bit quantization roughly requires ~0.7 bytes per parameter + overhead
    # 7B model @ 4-bit ~ 5GB + overhead ~ 6-7GB.
    # We assume a 7B model is the upper limit for 7GB RAM with 4-bit.

    # Simple check: if model name contains "7b" or "8b", it might be tight but possible.
    # If it contains "13b" or larger, it's likely impossible without heavy offloading.
    model_lower = model_name.lower()
    if "13b" in model_lower or "70b" in model_lower:
        logger.warning(f"Model {model_name} is likely too large for {max_ram_gb}GB RAM even with 4-bit quantization.")
        return False

    if "3b" in model_lower or "1b" in model_lower or "2b" in model_lower:
        return True

    # Default assumption for "8b" or "7b" models is that they fit with 4-bit + CPU offload
    # but it is risky. We return True but log a warning.
    logger.info(f"Model {model_name} is estimated to fit with 4-bit quantization and CPU offload.")
    return True


def main() -> None:
    """
    Main entry point for testing the model loader.
    Runs a small load test on a tiny model to verify functionality.
    """
    config = get_config()
    # Use a small model for testing to ensure it runs in the CI/CD environment
    test_model = "HuggingFaceTB/SmolLM2-360M" # Very small, safe for testing
    if os.getenv("TEST_MODEL"):
        test_model = os.getenv("TEST_MODEL")

    print(f"Testing model loader with: {test_model}")

    try:
        model, tokenizer = load_model(
            model_name_or_path=test_model,
            quant_type="4bit",
            use_cpu=True,
        )

        card = get_model_card(model)
        print(f"Model Card: {card}")

        # Simple inference test
        input_text = "Hello, this is a test of the model loader."
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Generation Test: {result}")
        print("Model loader test PASSED.")

    except Exception as e:
        print(f"Model loader test FAILED: {e}")
        raise


if __name__ == "__main__":
    main()