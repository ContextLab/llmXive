"""
CPU-safe model loading utilities for LLM inference.

This module provides functions to load and prepare transformer models
for CPU-only execution, avoiding GPU/CUDA dependencies and managing
memory constraints for limited RAM environments.
"""

import os
import sys
import time
from typing import Optional, Dict, Any, Tuple, Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList


class ModelLoadError(Exception):
    """Exception raised when model loading fails."""
    pass


class TimeoutError(Exception):
    """Exception raised when operation times out."""
    pass


class TimeoutStoppingCriteria(StoppingCriteria):
    """
    Stopping criteria that halts generation after a timeout period.

    This ensures inference doesn't run indefinitely on CPU-constrained systems.
    """

    def __init__(self, timeout_seconds: float):
        """
        Initialize timeout criteria.

        Args:
            timeout_seconds: Maximum allowed generation time in seconds.
        """
        super().__init__()
        self.timeout_seconds = timeout_seconds
        self.start_time = None

    def __call__(
        self,
        input_ids: torch.LongTensor,
        scores: torch.FloatTensor,
        **kwargs
    ) -> bool:
        """Check if timeout has been reached."""
        if self.start_time is None:
            self.start_time = time.time()

        elapsed = time.time() - self.start_time
        return elapsed >= self.timeout_seconds


def load_model_and_tokenizer(
    model_name: str,
    device: str = "cpu",
    torch_dtype: Optional[torch.dtype] = None,
    max_memory: Optional[Dict[str, int]] = None
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load a transformer model and tokenizer for CPU execution.

    Args:
        model_name: HuggingFace model identifier.
        device: Device to load model to (default: "cpu").
        torch_dtype: Data type for model weights (default: float32 for CPU).
        max_memory: Optional memory limit configuration.

    Returns:
        Tuple of (model, tokenizer).

    Raises:
        ModelLoadError: If model loading fails.
    """
    try:
        # Set default dtype for CPU
        if torch_dtype is None:
            torch_dtype = torch.float32

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            padding_side="left",
            trust_remote_code=True
        )

        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model with CPU-optimized settings
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
            device_map=device if device != "cpu" else None,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            max_memory=max_memory
        )

        # Ensure model is on CPU if requested
        if device == "cpu":
            model = model.to("cpu")

        return model, tokenizer

    except Exception as e:
        raise ModelLoadError(f"Failed to load model '{model_name}': {str(e)}")


def get_model_info(
    model: AutoModelForCausalLM
) -> Dict[str, Any]:
    """
    Get information about a loaded model.

    Args:
        model: The loaded transformer model.

    Returns:
        Dictionary containing model parameters, dtype, and device info.
    """
    num_params = sum(p.numel() for p in model.parameters())
    num_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

    return {
        "num_parameters": num_params,
        "num_trainable_parameters": num_trainable,
        "dtype": str(next(model.parameters()).dtype),
        "device": next(model.parameters()).device.type,
        "training_mode": model.training
    }


def prepare_inputs_for_cpu(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    text: str,
    max_length: int = 512,
    truncation: bool = True
) -> Dict[str, torch.Tensor]:
    """
    Prepare input tensors for CPU-based inference.

    Args:
        model: The loaded model.
        tokenizer: The model tokenizer.
        text: Input text to encode.
        max_length: Maximum sequence length.
        truncation: Whether to truncate long inputs.

    Returns:
        Dictionary of input tensors ready for model inference.
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=max_length,
        truncation=truncation,
        padding=True
    )

    # Move to CPU explicitly
    inputs = {k: v.to("cpu") for k, v in inputs.items()}

    return inputs


def main():
    """
    Main function for testing model loading.

    This function attempts to load a small test model and prints
    model information to verify CPU compatibility.
    """
    print("Testing CPU-safe model loading...")

    # Test with a small model
    test_model_name = "hf-internal-testing/tiny-random-gpt2"

    try:
        model, tokenizer = load_model_and_tokenizer(test_model_name, device="cpu")
        info = get_model_info(model)

        print(f"Model loaded successfully!")
        print(f"Parameters: {info['num_parameters']:,}")
        print(f"Device: {info['device']}")
        print(f"Dtype: {info['dtype']}")

        # Test input preparation
        test_text = "Hello, world! This is a test."
        inputs = prepare_inputs_for_cpu(model, tokenizer, test_text)

        print(f"Input shape: {inputs['input_ids'].shape}")
        print("CPU model loading test completed successfully.")

    except ModelLoadError as e:
        print(f"Model loading failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()