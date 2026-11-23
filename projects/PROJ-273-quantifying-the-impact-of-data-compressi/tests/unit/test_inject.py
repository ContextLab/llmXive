"""
Unit tests for src/data/inject.py.

This module verifies that synthetic CBC signals injected into real GW noise
result in a Signal-to-Noise Ratio (SNR) greater than the detection threshold (8.0).

It relies on the `src/data/inject.py` module which must:
1. Fetch real noise from GWOSC (or use a provided mock noise file for CI speed).
2. Inject a synthetic CBC waveform with known parameters.
3. Calculate the matched-filter SNR.
4. Return the SNR value.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add the project root to the path to allow imports from src/
# Note: In the actual pipeline, this is handled by conftest.py or CI setup.
# We replicate the logic here to ensure the test is runnable in isolation.
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "code" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Attempt to import the inject module.
# If the module doesn't exist yet (T013 not done), this test will fail to import,
# which is the correct behavior for "Test Driven Development" (red phase).
try:
    from data.inject import inject_synthetic_signal
except ImportError:
    pytest.fail(
        "src/data/inject.py not found or inject_synthetic_signal not implemented. "
        "Implement T013 (src/data/inject.py) before running this test."
    )

def test_injected_signal_snr_exceeds_threshold():
    """
    Test that a synthetic CBC signal injected into noise yields SNR > 8.
    
    This verifies the core functionality of the injection pipeline:
    that the injected signal is strong enough to be detected above the noise floor.
    
    Expected: assert snr > 8
    """
    # Define test parameters for a strong, detectable signal
    # These are representative of a binary black hole merger (e.g., GW150914-like)
    # to ensure we get a high SNR easily in a test environment.
    params = {
        "mass_1": 30.0,   # Solar masses
        "mass_2": 30.0,   # Solar masses
        "spin_1": 0.0,
        "spin_2": 0.0,
        "distance": 400.0, # Mpc (closer = stronger signal)
        "f_lower": 20.0,   # Hz
        "duration": 4.0,   # seconds
        "sample_rate": 2048, # Hz
        "detector": "H1",
        "random_seed": 42
    }

    # Execute the injection
    # The function should return the SNR of the injected signal
    try:
        snr = inject_synthetic_signal(params)
    except Exception as e:
        pytest.fail(f"inject_synthetic_signal raised an unexpected error: {e}")

    # Assert the SNR is greater than the detection threshold
    # The threshold is typically 8.0 for GW detection
    assert snr > 8.0, (
        f"Injected signal SNR ({snr:.2f}) is below the detection threshold (8.0). "
        "Check injection amplitude, distance, or noise realization."
    )

    # Additional sanity check: SNR should be a positive float
    assert isinstance(snr, (int, float)), f"SNR must be numeric, got {type(snr)}"
    assert snr > 0, "SNR must be positive"