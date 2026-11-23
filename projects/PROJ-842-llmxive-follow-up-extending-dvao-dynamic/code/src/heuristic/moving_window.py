"""
Moving Window Heuristic for Variance Estimation.

Implements the Moving-Window Heuristic for estimating variance based on the
last k steps of a trajectory. Includes enforcement of minimum window sizes
to ensure statistical stability.
"""
import numpy as np
from typing import List, Tuple, Optional, Deque, Generator
from collections import deque
import json
import os
import sys

# Default minimum window size constant
DEFAULT_MIN_WINDOW_SIZE = 10


def estimate_variance(trajectory: np.ndarray, window_size_k: int, rollout_size: Optional[int] = None) -> float:
    """
    Estimate variance using a moving window of the last k steps.

    Args:
        trajectory: 1D numpy array of reward/advantage values.
        window_size_k: The number of steps to use for the window (k).
        rollout_size: Optional total rollout size used to calculate dynamic minimum threshold.
                      If None, defaults to using DEFAULT_MIN_WINDOW_SIZE.

    Returns:
        float: The estimated variance of the windowed data.

    Raises:
        ValueError: If window_size_k is smaller than the calculated minimum threshold.
    """
    if trajectory is None or len(trajectory) == 0:
        raise ValueError("Trajectory cannot be empty.")

    # Calculate minimum window size threshold
    # min_k = max(10, 0.01 * rollout_size)
    if rollout_size is not None:
        min_k = max(DEFAULT_MIN_WINDOW_SIZE, int(0.01 * rollout_size))
    else:
        min_k = DEFAULT_MIN_WINDOW_SIZE

    if window_size_k < min_k:
        raise ValueError(
            f"Window size k={window_size_k} is too small for stable variance estimation; "
            f"minimum required is {min_k}"
        )

    if window_size_k > len(trajectory):
        # If k is larger than the trajectory, use the whole trajectory
        # This handles edge cases where the trajectory is short but k is large
        effective_k = len(trajectory)
    else:
        effective_k = window_size_k

    # Use the last effective_k steps
    window_data = trajectory[-effective_k:]

    # Calculate variance (ddof=0 for population variance, ddof=1 for sample variance)
    # Using ddof=0 as per standard heuristic definition unless specified otherwise
    # However, for unbiased estimation with small samples, ddof=1 is often preferred.
    # Given the context of "estimation", we use ddof=1 (sample variance).
    variance = np.var(window_data, ddof=1)

    return float(variance)


class MovingWindowVarianceHeuristic:
    """
    Class-based implementation of the Moving Window Variance Heuristic.
    Maintains an internal buffer of the last k values.
    """

    def __init__(self, window_size: int, rollout_size: Optional[int] = None):
        """
        Initialize the heuristic.

        Args:
            window_size: Number of steps (k) to maintain in the buffer.
            rollout_size: Optional total rollout size for minimum threshold calculation.
        """
        self.window_size = window_size
        self.rollout_size = rollout_size
        self.buffer: Deque[float] = deque(maxlen=window_size)

        # Validate minimum window size at initialization
        min_k = max(DEFAULT_MIN_WINDOW_SIZE, int(0.01 * rollout_size)) if rollout_size else DEFAULT_MIN_WINDOW_SIZE
        if window_size < min_k:
            raise ValueError(
                f"Window size k={window_size} is too small for stable variance estimation; "
                f"minimum required is {min_k}"
            )

    def update(self, value: float) -> float:
        """
        Update the buffer with a new value and return the current variance estimate.

        Args:
            value: New value to add to the window.

        Returns:
            float: Current variance estimate. Returns NaN if buffer is not full.
        """
        self.buffer.append(value)

        if len(self.buffer) < self.window_size:
            return float('nan')

        return float(np.var(self.buffer, ddof=1))

    def get_variance(self) -> float:
        """
        Get the current variance estimate from the buffer.

        Returns:
            float: Current variance estimate.
        """
        if len(self.buffer) < 2:
            return float('nan')
        return float(np.var(self.buffer, ddof=1))


def calculate_windowed_variance(trajectory: List[float], k: int) -> float:
    """
    Convenience wrapper for estimate_variance using a list.

    Args:
        trajectory: List of values.
        k: Window size.

    Returns:
        float: Calculated variance.
    """
    traj_array = np.array(trajectory)
    return estimate_variance(traj_array, k)


def compare_heuristic_to_fullbatch(trajectory: np.ndarray, k: int) -> Tuple[float, float, float]:
    """
    Compare the moving window variance estimate to the full-batch variance.

    Args:
        trajectory: 1D numpy array of values.
        k: Window size for the heuristic.

    Returns:
        Tuple of (heuristic_variance, fullbatch_variance, ratio).
    """
    if len(trajectory) < k:
        raise ValueError(f"Trajectory length {len(trajectory)} is less than window size {k}")

    # Heuristic: last k steps
    heuristic_var = estimate_variance(trajectory, k)

    # Full batch: entire trajectory
    fullbatch_var = float(np.var(trajectory, ddof=1))

    if fullbatch_var == 0:
        ratio = float('inf') if heuristic_var != 0 else 1.0
    else:
        ratio = heuristic_var / fullbatch_var

    return heuristic_var, fullbatch_var, ratio


def main():
    """
    CLI entry point for testing the Moving Window Heuristic.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test Moving Window Variance Heuristic")
    parser.add_argument("--k", type=int, default=10, help="Window size k")
    parser.add_argument("--rollout", type=int, default=1000, help="Rollout size for min threshold calculation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    np.random.seed(args.seed)
    dummy_trajectory = np.random.randn(args.rollout)

    try:
        var_est = estimate_variance(dummy_trajectory, args.k, rollout_size=args.rollout)
        print(f"Variance Estimate (k={args.k}): {var_est:.6f}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Test the error case
    print("Testing minimum window enforcement...")
    try:
        # Force a small k that should fail
        bad_k = 1
        estimate_variance(dummy_trajectory, bad_k, rollout_size=args.rollout)
        print("ERROR: Should have raised ValueError for small k")
        sys.exit(1)
    except ValueError as e:
        print(f"Correctly raised ValueError: {e}")

    print("All checks passed.")


if __name__ == "__main__":
    main()