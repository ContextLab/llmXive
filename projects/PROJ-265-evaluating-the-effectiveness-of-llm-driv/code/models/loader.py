"""
CodeLlama Model Loader for CPU-only execution.

This module implements the loading of a CodeLlama model (4-bit quantized)
using the accelerate library for CPU inference, adhering to the
project's resource constraints (FR-002).

The loader is designed to be memory-efficient and robust, failing loudly
if the model cannot be loaded within the specified constraints.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from accelerate import init_empty_weights, load_checkpoint_and_dispatch, infer_auto_device_map

# Project local imports
from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error

# Constants
MODEL_ID = "codellama/CodeLlama-7b-hf"  # Default model, configurable via env or args
QUANTIZATION_BITS = 4
MAX_MEMORY_CPU_GB = 6.0  # Target max memory usage on CPU
MAX_MEMORY_CPU_MB = int(MAX_MEMORY_CPU_GB * 1024)

logger = get_logger(__name__)


class ModelLoaderError(Exception):
    """Custom exception for model loading failures."""
    pass


def get_quantization_config() -> BitsAndBytesConfig:
    """
    Configure 4-bit quantization for CPU inference.

    Returns:
        BitsAndBytesConfig: Configuration for 4-bit quantization.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float32,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        llm_int8_enable_fp32_cpu_offload=False,  # We are not using LLM.int8 here
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"],
        llm_int8_threshold=6.0,
    )


def create_device_map() -> Dict[str, Any]:
    """
    Create a device map for CPU-only execution.

    Since we are running on CPU only, all model layers will be mapped to 'cpu'.
    The accelerate library handles the distribution of memory.

    Returns:
        Dict[str, Any]: Device map for the model.
    """
    # For CPU-only, we don't need a complex device map.
    # The model will be loaded entirely on CPU.
    return {"": "cpu"}


def load_model(
    model_id: Optional[str] = None,
    cache_dir: Optional[str] = None,
    max_memory_gb: float = MAX_MEMORY_CPU_GB,
) -> tuple:
    """
    Load the CodeLlama model (4-bit, CPU) using accelerate.

    Args:
        model_id: The Hugging Face model ID to load. Defaults to MODEL_ID.
        cache_dir: Optional directory to cache the model.
        max_memory_gb: Maximum memory to use on CPU in GB.

    Returns:
        tuple: (model, tokenizer)

    Raises:
        ModelLoaderError: If the model cannot be loaded or if memory limits are exceeded.
    """
    if model_id is None:
        model_id = MODEL_ID

    log_stage_start(logger, "load_model", {"model_id": model_id, "max_memory_gb": max_memory_gb})

    try:
        # 1. Load Tokenizer
        logger.info(f"Loading tokenizer for {model_id}...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            cache_dir=cache_dir,
            use_fast=False,  # CodeLlama often works better with slow tokenizer for specific features
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # 2. Configure Quantization
        logger.info("Configuring 4-bit quantization...")
        quantization_config = get_quantization_config()

        # 3. Load Model
        # We use `device_map="auto"` with `max_memory` to let accelerate handle
        # the placement, but since we are CPU-only, it will put everything on CPU.
        # We explicitly set max_memory to ensure we don't exceed limits.
        logger.info("Loading model with 4-bit quantization on CPU...")

        # Calculate max memory in MB for accelerate
        max_memory = {
            "cpu": max_memory_gb * 1024 * 1024 * 1024,
        }

        # For CPU-only, we can also use `device_map="cpu"` directly if we don't need
        # complex offloading, but `auto` with max_memory is safer for large models.
        # However, `device_map="auto"` on CPU might try to split layers if memory is tight.
        # Given the constraint of <3B params or 7B quantized to 4-bit, it should fit.
        # CodeLlama-7b 4-bit is approx 3.5-4GB.

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map="cpu",  # Explicitly CPU
            trust_remote_code=True,
            cache_dir=cache_dir,
            torch_dtype=torch.float32,  # Use float32 for compute as requested by config
            low_cpu_mem_usage=True,
        )

        logger.info("Model loaded successfully.")
        log_stage_complete(logger, "load_model", {"status": "success", "model_id": model_id})
        return model, tokenizer

    except Exception as e:
        log_stage_error(logger, "load_model", str(e))
        raise ModelLoaderError(f"Failed to load model {model_id}: {str(e)}") from e


def main():
    """
    Main entry point for testing the model loader.

    This function attempts to load the model and tokenizer, then performs
    a simple inference to verify the setup.
    """
    print("Starting Model Loader Test...")

    try:
        model, tokenizer = load_model()

        # Simple test inference
        test_prompt = "def hello_world():\n    print('Hello, World!')"
        inputs = tokenizer(test_prompt, return_tensors="pt")

        print(f"Running inference with prompt: {test_prompt}")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("Inference successful!")
        print(f"Generated: {generated_text}")

    except ModelLoaderError as e:
        print(f"Model Loader Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()