"""
Integration test for model loading.

Task: T010
Story: US1 - Construct and Train Compressed Student Models
Description: Verify that the substitute teacher model (facebook/wav2vec2-base-960h)
             loads correctly on CPU and exposes the expected configuration.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

import torch
from transformers import Wav2Vec2Model, Wav2Vec2Config

# Import the teacher loader implementation from T011
# The API surface confirms this module exists and exports `load_teacher_model`
from models.teacher_loader import load_teacher_model


class TestStudentLoad:
    """Integration tests for model loading functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure CPU-only execution for the test environment."""
        self.original_device = torch.device("cpu")
        # Explicitly force CPU to satisfy the constraint
        torch.set_default_device("cpu") if hasattr(torch, "set_default_device") else None
        yield
        # Cleanup if necessary

    def test_load_substitute_model(self):
        """
        Test loading the substitute teacher model (facebook/wav2vec2-base-960h).

        Input: Path to `facebook/wav2vec2-base-960h` checkpoint (loaded via model_id).
        Output: Loaded model object.
        Assertions:
          1. model.device.type == 'cpu'
          2. 'wav2vec2' in model.config.model_type
        """
        # Define the substitute model ID as per T011 (Plan-SpecGap)
        model_id = "facebook/wav2vec2-base-960h"

        # Load the model using the implementation from T011
        # This function handles the actual loading and device placement
        try:
            model = load_teacher_model(model_id)
        except Exception as e:
            pytest.fail(f"Failed to load teacher model '{model_id}': {e}")

        # Assertion 1: Verify model is on CPU
        # The model might be a Wav2Vec2Model or a wrapper. We check the device of its parameters.
        # If it's a HuggingFace model, .device is not always a direct attribute,
        # so we check the device of the first parameter.
        param_device = next(model.parameters()).device
        assert param_device.type == "cpu", (
            f"Model parameters are on {param_device.type}, expected 'cpu'. "
            "Ensure the runner environment is CPU-only."
        )

        # Assertion 2: Verify model type contains 'wav2vec2'
        # The model.config.model_type should reflect the architecture
        assert hasattr(model, "config"), "Loaded model must have a 'config' attribute."
        assert hasattr(model.config, "model_type"), "Config must have 'model_type'."

        model_type = model.config.model_type
        assert "wav2vec2" in model_type.lower(), (
            f"Model type '{model_type}' does not contain 'wav2vec2'. "
            "Expected a Wav2Vec2 variant."
        )

        # Additional sanity check: Ensure the model is not quantized yet (T011 loads the base)
        # Wav2Vec2Base is FP32 by default
        assert next(model.parameters()).dtype == torch.float32, (
            "The base teacher model should be loaded in FP32 by default."
        )

        print(f"Successfully loaded {model_type} on {param_device}.")