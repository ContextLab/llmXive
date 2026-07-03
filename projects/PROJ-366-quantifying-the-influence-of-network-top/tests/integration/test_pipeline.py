"""
Integration test for Green-Kubo convergence check.

This test verifies that the Green-Kubo simulation pipeline correctly detects
convergence based on the relative change in heat current autocorrelation.

Convergence criteria: relative change < 1% in the final segment.
"""
import os
import json
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import get_config, get_simulation_config
from code.simulation.green_kubo import (
    run_green_kubo_simulation,
    check_convergence,
    calculate_relative_change
)

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_synthetic_autocorrelation_data(
    length: int = 1000,
    noise_level: float = 0.05,
    convergence_point: Optional[int] = None
) -> np.ndarray:
    """
    Generate synthetic heat current autocorrelation data for testing.
    
    Args:
        length: Length of the time series
        noise_level: Standard deviation of Gaussian noise
        convergence_point: If specified, the data will converge after this point
                           (relative change < 1% after this point)
    
    Returns:
        np.ndarray: Synthetic autocorrelation values
    """
    # Start with decaying values
    t = np.arange(length)
    base_signal = np.exp(-t / 100) * 100.0
    
    # Add noise
    noise = np.random.normal(0, noise_level * 100, length)
    signal = base_signal + noise
    
    # If convergence point is specified, make the signal converge
    if convergence_point is not None and convergence_point < length:
        # Calculate the mean of the last 10% before convergence point
        pre_converge_mean = np.mean(signal[convergence_point-100:convergence_point])
        # Make the rest of the signal hover around this mean with small fluctuations
        signal[convergence_point:] = pre_converge_mean + np.random.normal(
            0, 0.01 * pre_converge_mean, length - convergence_point
        )
    
    return signal


def test_convergence_detection_converged():
    """
    Test that convergence is correctly detected when relative change < 1%.
    
    This test generates synthetic data that converges and verifies that
    the check_convergence function returns True.
    """
    logger.info("Testing convergence detection for converged data...")
    
    # Generate data that converges after 80% of the series
    converged_data = generate_synthetic_autocorrelation_data(
        length=1000, convergence_point=800
    )
    
    # Check convergence with a window of 10% of the data
    is_converged, relative_change = check_convergence(
        converged_data, window_fraction=0.1, threshold=0.01
    )
    
    logger.info(f"Converged data - is_converged: {is_converged}, relative_change: {relative_change}")
    
    assert is_converged, f"Expected converged data to be detected as converged, but got relative_change={relative_change}"
    assert relative_change < 0.01, f"Expected relative_change < 0.01, got {relative_change}"
    
    logger.info("✓ Convergence detection test passed for converged data")


def test_convergence_detection_not_converged():
    """
    Test that non-convergence is correctly detected when relative change >= 1%.
    
    This test generates synthetic data that does NOT converge and verifies that
    the check_convergence function returns False.
    """
    logger.info("Testing convergence detection for non-converged data...")
    
    # Generate data that does NOT converge (continues to decay)
    non_converged_data = generate_synthetic_autocorrelation_data(
        length=1000, convergence_point=None
    )
    
    # Check convergence with a window of 10% of the data
    is_converged, relative_change = check_convergence(
        non_converged_data, window_fraction=0.1, threshold=0.01
    )
    
    logger.info(f"Non-converged data - is_converged: {is_converged}, relative_change: {relative_change}")
    
    assert not is_converged, f"Expected non-converged data to be detected as not converged"
    
    logger.info("✓ Convergence detection test passed for non-converged data")


def test_relative_change_calculation():
    """
    Test the calculation of relative change between two segments.
    """
    logger.info("Testing relative change calculation...")
    
    # Create two segments with known relative change
    segment1 = np.array([100.0, 102.0, 98.0, 101.0, 99.0])
    segment2 = np.array([100.5, 101.5, 99.5, 100.0, 100.0])
    
    # Expected: mean1 = 100.0, mean2 = 100.3, relative_change = |100.3 - 100.0| / 100.0 = 0.003
    relative_change = calculate_relative_change(segment1, segment2)
    
    expected_mean1 = np.mean(segment1)
    expected_mean2 = np.mean(segment2)
    expected_relative_change = abs(expected_mean2 - expected_mean1) / expected_mean1
    
    logger.info(f"Segment 1 mean: {expected_mean1}, Segment 2 mean: {expected_mean2}")
    logger.info(f"Calculated relative change: {relative_change}, Expected: {expected_relative_change}")
    
    assert np.isclose(relative_change, expected_relative_change, rtol=1e-5), \
        f"Relative change calculation mismatch: {relative_change} vs {expected_relative_change}"
    
    logger.info("✓ Relative change calculation test passed")


def test_integration_with_simulation_config():
    """
    Integration test that verifies the convergence check works with actual simulation config.
    
    This test:
    1. Loads the simulation configuration
    2. Generates synthetic autocorrelation data
    3. Checks convergence using the configured parameters
    4. Verifies the result matches expectations
    """
    logger.info("Running integration test with simulation configuration...")
    
    # Load simulation config
    sim_config = get_simulation_config()
    logger.info(f"Loaded simulation config: {sim_config}")
    
    # Get convergence parameters from config or use defaults
    convergence_threshold = sim_config.get('convergence_threshold', 0.01)
    convergence_window_fraction = sim_config.get('convergence_window_fraction', 0.1)
    
    logger.info(f"Using convergence threshold: {convergence_threshold}, window fraction: {convergence_window_fraction}")
    
    # Generate converged data
    converged_data = generate_synthetic_autocorrelation_data(
        length=2000, convergence_point=1600
    )
    
    # Check convergence
    is_converged, relative_change = check_convergence(
        converged_data,
        window_fraction=convergence_window_fraction,
        threshold=convergence_threshold
    )
    
    logger.info(f"Integration test - is_converged: {is_converged}, relative_change: {relative_change}")
    
    assert is_converged, f"Integration test failed: converged data not detected as converged"
    assert relative_change < convergence_threshold, \
        f"Integration test failed: relative_change {relative_change} >= threshold {convergence_threshold}"
    
    logger.info("✓ Integration test with simulation config passed")


def test_edge_case_small_window():
    """
    Test convergence detection with a very small window (edge case).
    """
    logger.info("Testing edge case with small window...")
    
    # Generate data
    data = generate_synthetic_autocorrelation_data(length=500, convergence_point=400)
    
    # Use a very small window (1%)
    is_converged, relative_change = check_convergence(
        data, window_fraction=0.01, threshold=0.01
    )
    
    logger.info(f"Small window test - is_converged: {is_converged}, relative_change: {relative_change}")
    
    # Should still work, though may be noisier
    assert isinstance(is_converged, bool), "is_converged should be a boolean"
    assert isinstance(relative_change, float), "relative_change should be a float"
    
    logger.info("✓ Edge case test passed")


def test_edge_case_very_small_data():
    """
    Test convergence detection with very small data (edge case).
    """
    logger.info("Testing edge case with very small data...")
    
    # Generate very small dataset
    data = np.array([100.0, 101.0, 99.0, 100.5, 99.5])
    
    # Use a window that covers the whole dataset (edge case)
    is_converged, relative_change = check_convergence(
        data, window_fraction=0.5, threshold=0.01
    )
    
    logger.info(f"Very small data test - is_converged: {is_converged}, relative_change: {relative_change}")
    
    # Should handle gracefully
    assert isinstance(is_converged, bool), "is_converged should be a boolean"
    
    logger.info("✓ Very small data edge case test passed")


def run_all_tests():
    """
    Run all integration tests for Green-Kubo convergence check.
    """
    logger.info("=" * 60)
    logger.info("Starting Green-Kubo Convergence Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        test_convergence_detection_converged,
        test_convergence_detection_not_converged,
        test_relative_change_calculation,
        test_integration_with_simulation_config,
        test_edge_case_small_window,
        test_edge_case_very_small_data
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            logger.info(f"\nRunning {test_func.__name__}...")
            test_func()
            passed += 1
            logger.info(f"✓ {test_func.__name__} PASSED")
        except AssertionError as e:
            failed += 1
            logger.error(f"✗ {test_func.__name__} FAILED: {e}")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test_func.__name__} ERROR: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Test Summary: {passed} passed, {failed} failed")
    logger.info("=" * 60)
    
    if failed > 0:
        logger.error("Some tests failed!")
        return 1
    else:
        logger.info("All tests passed!")
        return 0


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)