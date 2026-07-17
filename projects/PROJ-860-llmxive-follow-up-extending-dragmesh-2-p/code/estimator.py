"""
Virtual Tactile Estimator Module.

Implements the VirtualTactileEstimator class for estimating the friction coefficient
(k_est) based on torque and velocity measurements, applying a moving average filter
and epsilon clamping as per FR-001, FR-006, and FR-007.
"""

import numpy as np
from collections import deque
from typing import Optional, List, Tuple, Dict, Any


class VirtualTactileEstimator:
    """
    Estimates the virtual tactile friction coefficient k_est.

    Formula (FR-001): k_est = |Torque| / |Velocity|
    Constraints:
      - FR-006: Moving average filter with a configurable window (default=5) to smooth noise.
      - FR-007: Epsilon clamping to prevent division by zero and bound the result.
    """

    def __init__(
        self,
        window_size: int = 5,
        epsilon: float = 1e-4,
        min_k: float = 0.0,
        max_k: float = 10.0
    ):
        """
        Initialize the estimator.

        Args:
            window_size: Number of recent samples for the moving average (FR-006).
            epsilon: Small constant added to denominator to prevent division by zero (FR-007).
            min_k: Minimum allowed value for k_est after clamping (FR-007).
            max_k: Maximum allowed value for k_est after clamping (FR-007).
        """
        if window_size < 1:
            raise ValueError("window_size must be at least 1")
        if epsilon <= 0:
            raise ValueError("epsilon must be positive")
        if min_k < 0:
            raise ValueError("min_k cannot be negative")
        if max_k < min_k:
            raise ValueError("max_k must be greater than or equal to min_k")

        self.window_size = window_size
        self.epsilon = epsilon
        self.min_k = min_k
        self.max_k = max_k

        # Buffer for moving average of instantaneous k_est values
        self._k_buffer: deque = deque(maxlen=window_size)
        self._last_k: Optional[float] = None

    def update(self, torque: float, velocity: float) -> float:
        """
        Update the estimator with new torque and velocity readings.

        Calculates instantaneous k_est = |torque| / (|velocity| + epsilon),
        updates the moving average buffer, and returns the clamped smoothed value.

        Args:
            torque: The measured joint torque (N*m).
            velocity: The measured joint velocity (rad/s).

        Returns:
            The smoothed and clamped k_est value.

        Raises:
            ValueError: If inputs are not finite numbers.
        """
        # Validate inputs
        if not np.isfinite(torque) or not np.isfinite(velocity):
            raise ValueError("Torque and velocity must be finite numbers.")

        # Calculate instantaneous k_est (FR-001) with epsilon protection (FR-007)
        abs_torque = abs(float(torque))
        abs_velocity = abs(float(velocity))

        # Prevent division by zero using epsilon
        instantaneous_k = abs_torque / (abs_velocity + self.epsilon)

        # Update moving average buffer (FR-006)
        self._k_buffer.append(instantaneous_k)

        # Calculate smoothed k_est
        if len(self._k_buffer) == 0:
            smoothed_k = instantaneous_k
        else:
            smoothed_k = float(np.mean(self._k_buffer))

        # Apply range clamping (FR-007)
        clamped_k = max(self.min_k, min(self.max_k, smoothed_k))

        self._last_k = clamped_k
        return clamped_k

    def get_current_estimate(self) -> Optional[float]:
        """
        Get the most recent k_est estimate.

        Returns:
            The last calculated k_est value, or None if update() has not been called.
        """
        return self._last_k

    def reset(self) -> None:
        """
        Reset the estimator state (clear buffer and last value).
        """
        self._k_buffer.clear()
        self._last_k = None

    def get_buffer_stats(self) -> Dict[str, float]:
        """
        Get statistics about the current buffer.

        Returns:
            Dictionary containing count, mean, min, and max of the buffer.
            Returns zeros if buffer is empty.
        """
        if len(self._k_buffer) == 0:
            return {
                "count": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0
            }

        data = list(self._k_buffer)
        return {
            "count": float(len(data)),
            "mean": float(np.mean(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data))
        }
