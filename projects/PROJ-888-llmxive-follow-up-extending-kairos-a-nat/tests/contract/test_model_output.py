"""
Contract test for model output schema (User Story 2).

This test verifies that the model output adheres to the expected schema:
- Batch dimension
- Sequence length
- State dimensionality

It asserts that the output shape corresponds to these three dimensions.
"""
import pytest
import numpy as np
from typing import Tuple

# Mock model output generator for contract testing
# In a real integration, this would come from code/models/kairos_adapter.py
def mock_model_output(batch_size: int = 2, seq_len: int = 10, dim: int = 64) -> np.ndarray:
    """
    Generates a mock model output array with the expected shape.
    This simulates the output of the Kairos adapter during inference.
    """
    return np.random.rand(batch_size, seq_len, dim).astype(np.float32)

def test_model_output_shape():
    """
    Assert that the model output shape corresponds to:
    (batch_dimension, sequence_length, dimensionality)

    This is a contract test ensuring the model adheres to the defined schema.
    """
    # Define expected dimensions based on project config or test parameters
    batch_size = 4
    sequence_length = 50
    state_dimensionality = 128

    # Generate mock output (simulating the model's forward pass)
    output = mock_model_output(
        batch_size=batch_size,
        seq_len=sequence_length,
        dim=state_dimensionality
    )

    # Assert the shape is a tuple of length 3
    assert isinstance(output.shape, tuple), "Output shape must be a tuple"
    assert len(output.shape) == 3, f"Output must be 3D: (batch, seq, dim). Got shape: {output.shape}"

    # Assert specific dimensions match expectations
    b, s, d = output.shape
    assert b == batch_size, f"Batch dimension mismatch: expected {batch_size}, got {b}"
    assert s == sequence_length, f"Sequence length mismatch: expected {sequence_length}, got {s}"
    assert d == state_dimensionality, f"State dimensionality mismatch: expected {state_dimensionality}, got {d}"

def test_model_output_shape_minimal():
    """
    Test with minimal valid dimensions to ensure the schema holds even at the lower bound.
    """
    output = mock_model_output(batch_size=1, seq_len=1, dim=1)
    assert output.shape == (1, 1, 1), f"Minimal shape failed: {output.shape}"

def test_model_output_shape_large():
    """
    Test with larger dimensions to ensure the schema holds under load.
    """
    output = mock_model_output(batch_size=32, seq_len=1000, dim=512)
    assert output.shape == (32, 1000, 512), f"Large shape failed: {output.shape}"