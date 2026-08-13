"""
Unit test for TinyLlama 8‑bit quantized model loading.

The test verifies that:
1. The model loads without raising CUDA‑related errors.
2. All parameters reside on the CPU.
3. The total number of parameters fits within the 7 GB RAM budget
   (≈ 7 GB = 7 × 1024³ bytes, one byte per parameter after 8‑bit quantization).
"""

import pytest
import torch

from src.models.tinyllama import load_quantized_model

@pytest.mark.timeout(300)
def test_quantized_model_loads_and_within_ram_budget():
    # Load the quantized TinyLlama model.
    model, param_count = load_quantized_model()

    # Ensure all parameters are on CPU (no CUDA tensors).
    for param in model.parameters():
        assert param.device.type == "cpu", "Parameter found on non‑CPU device"

    # Define the RAM budget in bytes (7 GB).
    ram_budget_bytes = 7 * 1024 ** 3

    # In 8‑bit quantization each parameter consumes ~1 byte.
    assert param_count <= ram_budget_bytes, (
        f"Model parameter count ({param_count}) exceeds 7 GB RAM budget"
    )
