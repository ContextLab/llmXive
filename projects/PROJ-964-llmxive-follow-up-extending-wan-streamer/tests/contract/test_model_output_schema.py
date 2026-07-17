"""
Contract test for model output schema (T021).

Validates that the GRU Estimator model output adheres to the required schema:
- Output shape: [batch_size, 2]
- Column 0: predicted_delta_magnitude (float)
- Column 1: uncertainty_score (float, range 0.0-1.0)

This test ensures FR-002 compliance and references T031 for MOS validation logic.
"""
import os
import sys
import pytest
import torch
import numpy as np
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.gru_estimator import GRUEstimator
from utils.config import set_seed


@pytest.fixture
def model():
    """Load or instantiate the GRU Estimator model."""
    set_seed(42)
    # Input features: timestamp, semantic_feature, prosodic_feature, latent_delta_magnitude, turn_label
    # We assume a sequence length of 10 for this contract test
    input_dim = 5
    hidden_dim = 32
    output_dim = 2  # delta_magnitude, uncertainty_score
    
    model = GRUEstimator(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim)
    return model


@pytest.fixture
def dummy_batch():
    """Create a dummy input batch."""
    set_seed(42)
    batch_size = 16
    sequence_length = 10
    input_dim = 5
    # Random tensor within reasonable range
    x = torch.randn(batch_size, sequence_length, input_dim)
    return x


def test_output_shape(model, dummy_batch):
    """
    Contract: Output must be of shape [batch_size, 2].
    """
    model.eval()
    with torch.no_grad():
        output = model(dummy_batch)
    
    batch_size, seq_len, _ = dummy_batch.shape
    assert output.shape == (batch_size, 2), \
        f"Expected output shape ({batch_size}, 2), got {output.shape}"


def test_output_dtype(model, dummy_batch):
    """
    Contract: Output must be floating point.
    """
    model.eval()
    with torch.no_grad():
        output = model(dummy_batch)
    
    assert torch.is_floating_point(output), \
        f"Output must be floating point, got {output.dtype}"


def test_uncertainty_score_range(model, dummy_batch):
    """
    Contract: Column 1 (uncertainty_score) must be in range [0.0, 1.0].
    This is critical for FR-002 and downstream logic (e.g., T031 MOS validation).
    """
    model.eval()
    with torch.no_grad():
        output = model(dummy_batch)
    
    uncertainty_scores = output[:, 1]
    
    min_val = uncertainty_scores.min().item()
    max_val = uncertainty_scores.max().item()
    
    assert min_val >= 0.0, \
        f"Uncertainty score minimum {min_val} is below 0.0"
    assert max_val <= 1.0, \
        f"Uncertainty score maximum {max_val} is above 1.0"


def test_delta_magnitude_non_negative(model, dummy_batch):
    """
    Contract: Column 0 (predicted_delta_magnitude) should logically be non-negative.
    While the raw model output might be any float, the specification implies a magnitude.
    We enforce a ReLU or absolute value logic in the model if not already done,
    or here we check for reasonable bounds if the model is expected to output raw deltas.
    However, for a 'magnitude', it should be >= 0.
    """
    model.eval()
    with torch.no_grad():
        output = model(dummy_batch)
    
    delta_magnitudes = output[:, 0]
    
    # Assuming the model outputs magnitude directly or we enforce it.
    # If the model outputs raw delta, we check for validity.
    # Given the name 'magnitude', we expect >= 0.
    # If the implementation uses absolute value or ReLU, this passes.
    # If it outputs raw signed delta, this test might fail, indicating a schema mismatch.
    # Based on FR-002 "predicted delta magnitude", it implies non-negative.
    # We assert that the model should be designed to output non-negative magnitudes.
    # If the current model doesn't enforce this, the model code needs adjustment,
    # but this test validates the CONTRACT.
    # For this test to pass, the model must ensure non-negative output for col 0.
    # We assume the model implementation (T018) handles this (e.g., via ReLU).
    # If the model outputs negative values, this test fails, correctly flagging a contract violation.
    
    # Note: If the model is trained to predict signed deltas, the schema might be "delta" not "magnitude".
    # The task T021 specifically asks for "delta magnitude".
    # We enforce the contract: magnitude >= 0.
    min_delta = delta_magnitudes.min().item()
    assert min_delta >= 0.0, \
        f"Predicted delta magnitude {min_delta} is negative, violating magnitude contract"


def test_output_consistency_with_schema(model, dummy_batch):
    """
    Comprehensive contract check:
    - Shape is correct
    - Uncertainty is in [0, 1]
    - Delta magnitude is non-negative
    """
    model.eval()
    with torch.no_grad():
        output = model(dummy_batch)
    
    batch_size = dummy_batch.shape[0]
    
    # 1. Shape
    assert output.shape == (batch_size, 2), "Shape mismatch"
    
    # 2. Uncertainty Score (Col 1)
    unc = output[:, 1]
    assert unc.min() >= 0.0 and unc.max() <= 1.0, "Uncertainty score out of [0, 1] range"
    
    # 3. Delta Magnitude (Col 0)
    delta = output[:, 0]
    assert delta.min() >= 0.0, "Delta magnitude is negative"
    
    # 4. No NaNs or Infs
    assert not torch.isnan(output).any(), "Output contains NaN"
    assert not torch.isinf(output).any(), "Output contains Inf"
    
    # 5. Reference T031: This test validates the input schema for T031 (MOS validation).
    # T031 expects (uncertainty_score, actual_error) pairs.
    # This test ensures the uncertainty_score is a valid probability-like value.
    assert output.dtype == torch.float32, "Output dtype must be float32 for downstream compatibility"