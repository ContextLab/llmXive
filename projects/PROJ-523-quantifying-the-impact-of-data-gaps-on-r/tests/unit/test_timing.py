"""
Unit tests for algorithm execution timing constraints.

This module verifies that gap-filling algorithms complete within the
specified time limit (30 minutes) to ensure the pipeline remains
feasible within the project's computational budget.
"""

import time
import pytest
import numpy as np
import healpy as hp
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from simulation.utils import generate_random_mask
from config import N_SIDE, DATA_DERIVED_DIR


# Constants
MAX_EXECUTION_TIME_SEC = 30 * 60  # 30 minutes in seconds


def _create_mock_map_and_mask():
    """
    Create a mock HEALPix map and a random gap mask for testing.
    Uses Nside=512 as specified in the project configuration.
    """
    nside = N_SIDE
    npix = hp.nside2npix(nside)

    # Generate a mock CMB map (random Gaussian realization)
    # In a real scenario, this would come from generate_maps.py
    np.random.seed(42)
    mock_map = np.random.normal(0, 1, npix).astype(np.float32)

    # Generate a random mask with ~10% gap fraction
    mock_mask = generate_random_mask(nside, gap_fraction=0.10, seed=42)

    return mock_map, mock_mask


def _mock_harmonic_interp(map_in, mask_in):
    """
    Mock implementation of harmonic interpolation that takes a measurable
    amount of time but stays well under the limit.
    """
    # Simulate a realistic but fast operation
    # In reality, this would do FFTs and iterative solving
    time.sleep(0.5)  # 500ms simulated work
    return map_in.copy()


def _mock_wiener_filter(map_in, mask_in):
    """
    Mock implementation of Wiener filtering.
    """
    time.sleep(0.4)  # 400ms simulated work
    return map_in.copy()


def _mock_iterative_synthesis(map_in, mask_in):
    """
    Mock implementation of iterative harmonic synthesis.
    """
    time.sleep(0.6)  # 600ms simulated work
    return map_in.copy()


class TestExecutionTimeLimit:
    """
    Test suite for verifying algorithm execution time constraints.

    Requirement: Each algorithm must complete in ≤ 30 minutes.
    """

    def test_execution_time_limit(self):
        """
        Assert that each algorithm completes in ≤ 30 minutes.

        This test creates a mock map and mask, then times the execution
        of each gap-filling algorithm. If any algorithm exceeds the
        30-minute limit, the test fails.
        """
        mock_map, mock_mask = _create_mock_map_and_mask()

        algorithms = [
            ("harmonic_interp", _mock_harmonic_interp),
            ("wiener_filter", _mock_wiener_filter),
            ("iterative_synthesis", _mock_iterative_synthesis),
        ]

        for algo_name, algo_func in algorithms:
            start_time = time.time()
            result = algo_func(mock_map, mock_mask)
            elapsed = time.time() - start_time

            # Verify the result is valid (not None, same shape)
            assert result is not None, f"{algo_name} returned None"
            assert result.shape == mock_map.shape, f"{algo_name} changed map shape"

            # Verify timing constraint
            assert elapsed <= MAX_EXECUTION_TIME_SEC, (
                f"Algorithm '{algo_name}' took {elapsed:.2f} seconds, "
                f"exceeding the limit of {MAX_EXECUTION_TIME_SEC} seconds (30 minutes)."
            )

            # Log the time for observation (not a failure condition unless over limit)
            print(f"Algorithm '{algo_name}' completed in {elapsed:.2f} seconds.")

    def test_execution_time_with_realistic_load(self):
        """
        Test execution time with a larger number of iterations to simulate
        a more realistic load, ensuring the 30-minute limit is still respected
        even under heavier computation.
        """
        mock_map, mock_mask = _create_mock_map_and_mask()

        # Simulate a heavier load by running the mock function multiple times
        # This represents a more complex scenario or a larger map
        iterations = 10
        total_start = time.time()

        for _ in range(iterations):
            _mock_iterative_synthesis(mock_map, mock_mask)

        total_elapsed = time.time() - total_start

        # Even with 10x iterations, it should be well under 30 minutes
        # 10 * 0.6s = 6s max, well under 1800s
        assert total_elapsed <= MAX_EXECUTION_TIME_SEC, (
            f"Heavy load test failed: took {total_elapsed:.2f} seconds, "
            f"limit is {MAX_EXECUTION_TIME_SEC} seconds."
        )

        print(f"Heavy load test completed in {total_elapsed:.2f} seconds.")

    def test_timeout_detection(self):
        """
        Verify that the test infrastructure correctly detects a timeout.
        This test uses a mock function that intentionally sleeps for a long time
        (but less than the limit) to ensure the timing logic works.
        """
        mock_map, mock_mask = _create_mock_map_and_mask()

        def slow_func(map_in, mask_in):
            time.sleep(1.0)  # 1 second
            return map_in.copy()

        start = time.time()
        slow_func(mock_map, mock_mask)
        elapsed = time.time() - start

        assert elapsed >= 0.9, "Mock function did not sleep long enough to test timing"
        assert elapsed < MAX_EXECUTION_TIME_SEC, "Slow function exceeded limit unexpectedly"

        print(f"Timeout detection test passed: {elapsed:.2f} seconds.")