"""
Unit tests for the MPNN model device handling.

This test suite verifies two things:
1. CUDA is not available in the execution environment (CPU‑only).
2. The MPNN utility `get_device` reports a CPU device and logs the
   expected startup message ``Device: CPU``.
"""

import pytest
import torch

# Import the functions/classes under test.
# The relative import path follows the project's API surface.
from models.mpnn import get_device, SingleLayerMPNN


def test_cuda_unavailable():
    """Assert that the runtime does not have CUDA support."""
    # The specification requires that the test confirms a CPU‑only environment.
    assert torch.cuda.is_available() is False, "CUDA should not be available"


def test_device_is_cpu_and_logs_message(caplog):
    """
    Verify that `get_device` returns a CPU device and that a log entry
    containing ``Device: CPU`` is emitted during the call (or model
    construction).

    The test uses the ``caplog`` fixture to capture log records emitted
    at INFO level.
    """
    # Capture INFO‑level logs
    caplog.set_level("INFO")

    # Call the helper that determines the device.  It is expected to log
    # a message like ``Device: CPU``.
    device = get_device()
    assert device.type == "cpu", f"Expected CPU device, got {device}"

    # Some implementations may only log during model instantiation.
    # Instantiating the model ensures any lazy logging also occurs.
    try:
        # Use minimal dimensions; actual values are irrelevant for this test.
        _ = SingleLayerMPNN(in_channels=1, out_channels=1)
    except Exception:
        # If model construction fails for unrelated reasons, we still want
        # to verify the device handling; ignore the exception here.
        pass

    # Collect all log messages emitted during the test.
    messages = [record.getMessage() for record in caplog.records]

    # Assert that at least one message mentions the CPU device.
    assert any("Device: CPU" in msg for msg in messages), (
        "Expected a log entry containing 'Device: CPU' but none was found. "
        f"Captured messages: {messages}"
    )