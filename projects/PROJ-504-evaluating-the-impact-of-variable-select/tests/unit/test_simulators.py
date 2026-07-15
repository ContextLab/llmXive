"""
Unit tests for the data simulation module.

This module implements TDD-First tests for User Story 1, specifically verifying
that the simulator generates outcome vectors with the correct Signal-to-Noise Ratio (SNR).

Task: T011 [TDD-First] [P] [US1] Unit test for simulator in `tests/unit/test_simulators.py`: 
function `test_simulator_generates_correct_snr` asserts generated Y variance matches SNR target within tolerance.
"""
import pytest
import numpy as np
from typing import Tuple

# Import the real implementation from the sibling module
# Note: In a real execution environment, the PYTHONPATH would include the project root/code/
try:
    from data.simulators import generate_synthetic_outcome
except ImportError:
    # Fallback for direct execution from tests/ if PYTHONPATH is not set correctly in this specific runner context
    # In the actual project structure, this should be: from code.data.simulators import ...
    # However, per the API surface provided, we assume the module is importable as 'data.simulators' 
    # or we adjust based on standard project layout. 
    # Given the API surface list didn't explicitly list 'data.simulators', but T016/T015 refer to it,
    # we assume it exists. If it doesn't, the test will fail to import, which is a valid failure state 
    # indicating the implementation (T015/016) is missing.
    # To ensure this test file is runnable as part of the suite, we attempt the standard import.
    import sys
    import os
    # Add 'code' to path if running from project root
    code_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'code')
    if code_path not in sys.path:
        sys.path.insert(0, code_path)
    
    from data.simulators import generate_synthetic_outcome


# Tolerance for SNR verification (relative or absolute)
SNR_TOLERANCE = 0.15  # 15% tolerance for variance estimation noise

def _calculate_snr(y_true: np.ndarray, y_noisy: np.ndarray) -> float:
    """
    Calculate the empirical SNR from the generated data.
    
    SNR = Var(signal) / Var(noise)
    where signal is the true linear combination and noise is the residual.
    """
    signal = y_true
    noise = y_noisy - y_true
    
    var_signal = np.var(signal)
    var_noise = np.var(noise)
    
    if var_noise == 0:
        return float('inf')
    
    return var_signal / var_noise


def test_simulator_generates_correct_snr():
    """
    Assert that the generated Y variance matches the SNR target within tolerance.
    
    This test verifies the core requirement of the simulator: controlling the 
    ratio of signal variance to noise variance.
    
    Args:
        None
        
    Returns:
        None: Asserts equality within tolerance.
        
    Raises:
        AssertionError: If the calculated SNR deviates from the target by more than SNR_TOLERANCE.
    """
    # 1. Setup: Define parameters
    n_samples = 10000  # Large sample to ensure variance estimation is stable
    n_features = 10
    target_snr_db = 10.0  # Target SNR in dB (linear scale = 10)
    target_snr_linear = 10 ** (target_snr_db / 10.0)
    
    # Create a fixed seed for reproducibility
    seed = 42
    np.random.seed(seed)
    
    # Generate random X (standard normal)
    X = np.random.randn(n_samples, n_features)
    
    # Generate random true coefficients (some non-zero)
    true_coefficients = np.random.randn(n_features)
    # Ensure at least some are non-zero to have a signal
    true_coefficients[5:] = 0.0 
    
    # 2. Action: Call the simulator
    # The function should return (Y, noise_vector) or similar
    # Assuming the signature based on standard simulation patterns:
    # generate_synthetic_outcome(X, true_coefficients, snr, seed)
    # We need to handle the case where the function might not exist yet (implementation pending)
    try:
        Y, noise = generate_synthetic_outcome(X, true_coefficients, target_snr_linear, seed)
    except Exception as e:
        # If the implementation is missing, the test fails explicitly
        pytest.fail(f"Simulator function 'generate_synthetic_outcome' not implemented or failed: {e}")
    
    # 3. Verification: Calculate empirical SNR
    # Reconstruct the signal to compare
    signal = X @ true_coefficients
    
    # Calculate empirical SNR
    empirical_snr = _calculate_snr(signal, Y)
    
    # 4. Assertion: Check against tolerance
    # We allow a relative tolerance because variance estimation is stochastic
    # Even with 10k samples, there will be some variance in the estimate.
    lower_bound = target_snr_linear * (1 - SNR_TOLERANCE)
    upper_bound = target_snr_linear * (1 + SNR_TOLERANCE)
    
    assert lower_bound <= empirical_snr <= upper_bound, (
        f"Empirical SNR ({empirical_snr:.4f}) is outside the acceptable range "
        f"of [{lower_bound:.4f}, {upper_bound:.4f}] for target SNR {target_snr_linear:.4f}. "
        f"Deviation: {abs(empirical_snr - target_snr_linear) / target_snr_linear * 100:.2f}%"
    )


def test_simulator_snr_consistency_across_seeds():
    """
    Verify that the SNR is consistent across different random seeds.
    """
    target_snr_linear = 5.0
    n_trials = 5
    n_samples = 5000
    n_features = 5
    
    snr_values = []
    
    for i in range(n_trials):
        seed = i * 100
        X = np.random.randn(n_samples, n_features)
        coeffs = np.random.randn(n_features)
        
        try:
            Y, _ = generate_synthetic_outcome(X, coeffs, target_snr_linear, seed)
            signal = X @ coeffs
            snr = _calculate_snr(signal, Y)
            snr_values.append(snr)
        except Exception:
            pytest.fail("Simulator failed during consistency check.")
    
    # Calculate mean and std
    mean_snr = np.mean(snr_values)
    std_snr = np.std(snr_values)
    
    # The standard deviation should be relatively small compared to the mean
    # This ensures the noise injection is stable
    cv = std_snr / mean_snr
    assert cv < 0.10, f"SNR variability too high (CV={cv:.2f}). Expected < 0.10."
    
    # Check mean is close to target
    assert abs(mean_snr - target_snr_linear) < (target_snr_linear * 0.15), \
        f"Mean SNR {mean_snr} deviates significantly from target {target_snr_linear}"