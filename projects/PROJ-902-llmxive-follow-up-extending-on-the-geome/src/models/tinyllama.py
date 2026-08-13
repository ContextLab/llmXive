"""
TinyLlama model loading utilities with 8-bit CPU quantization.

Provides a function `load_quantized_model` that downloads the TinyLlama model
from HuggingFace Hub and loads it using `bitsandbytes` 8‑bit quantization on CPU.
The function returns the model instance and the total number of parameters.
"""

from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM

def load_quantized_model(
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v0.1",
) -> tuple[AutoModelForCausalLM, int]:
    """
    Load the TinyLlama model with 8‑bit quantization for CPU inference.

    Parameters
    ----------
    model_name: str
        HuggingFace repository identifier of the TinyLlama checkpoint.

    Returns
    -------
    model: AutoModelForCausalLM
        The quantized model placed on CPU.
    param_count: int
        Total number of parameters in the model (as a raw count; each
        parameter occupies one byte after 8‑bit quantization).
    """
    # Load the model with bitsandbytes 8‑bit quantization.
    # `load_in_8bit=True` triggers bitsandbytes; we then explicitly move
    # the model to CPU to guarantee no CUDA usage.
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        load_in_8bit=True,
        torch_dtype=torch.float16,
    )
    model.to("cpu")
    model.eval()

    # Count parameters (raw number, not bytes)
    param_count = sum(p.numel() for p in model.parameters())

    return model, param_count
