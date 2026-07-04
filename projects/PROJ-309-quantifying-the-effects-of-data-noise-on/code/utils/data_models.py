"""
Data models for the dynamical systems noise analysis pipeline.

This module defines the core data structures (dataclasses) used to represent
trajectories, noisy trajectories, and metric results, aligning with the
project specification entities.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass(frozen=True)
class Trajectory:
    """
    Represents a clean, deterministic chaotic trajectory.

    Attributes:
        system_name: Name of the dynamical system (e.g., 'lorenz', 'rossler').
        parameters: Dictionary of system parameters (e.g., {'sigma': 10, 'rho': 28, 'beta': 8/3}).
        seed: Random seed used for initialization (if applicable).
        times: 1D numpy array of time points.
        state: 2D numpy array of shape (N, 3) containing the state vectors (x, y, z).
        metadata: Optional dictionary for additional context (e.g., integration method, tolerance).
    """
    system_name: str
    parameters: Dict[str, float]
    seed: int
    times: np.ndarray
    state: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Basic validation to ensure data integrity
        if self.state.shape[1] != 3:
            raise ValueError(f"Trajectory state must have 3 dimensions, got {self.state.shape[1]}")
        if len(self.times) != self.state.shape[0]:
            raise ValueError(f"Times length ({len(self.times)}) must match state rows ({self.state.shape[0]})")


@dataclass(frozen=True)
class NoisyTrajectory:
    """
    Represents a trajectory with injected noise.

    Attributes:
        clean_trajectory: The original clean Trajectory object.
        noise_type: Type of noise injected (e.g., 'gaussian', 'quantization').
        snr_db: Signal-to-Noise Ratio in decibels used for injection.
        noise_params: Dictionary of specific noise parameters (e.g., {'bit_depth': 8} for quantization).
        noisy_state: 2D numpy array of shape (N, 3) containing the noisy state vectors.
        measured_snr_db: The actual measured SNR after injection (may differ slightly from target).
    """
    clean_trajectory: Trajectory
    noise_type: str
    snr_db: float
    noise_params: Dict[str, Any]
    noisy_state: np.ndarray
    measured_snr_db: Optional[float] = None

    def __post_init__(self):
        if self.noisy_state.shape != self.clean_trajectory.state.shape:
            raise ValueError("Noisy state shape must match clean trajectory state shape")


@dataclass(frozen=True)
class MetricResult:
    """
    Represents the result of a metric calculation on a noisy trajectory.

    Attributes:
        metric_name: Name of the metric (e.g., 'correlation_dimension', 'lyapunov_exponent', 'fnn_rate').
        trajectory_id: Identifier linking to the source trajectory (e.g., seed or file hash).
        noise_type: Type of noise present in the trajectory.
        snr_db: SNR level of the trajectory.
        value: The computed numerical value of the metric.
        ground_truth: The known ground truth value for the clean system (if available).
        relative_error: Calculated relative error as a percentage: |computed - ground| / |ground| * 100.
        metadata: Additional context about the calculation (e.g., embedding dimension, tolerance).
    """
    metric_name: str
    trajectory_id: str
    noise_type: str
    snr_db: float
    value: float
    ground_truth: Optional[float] = None
    relative_error: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.ground_truth is not None and self.ground_truth != 0:
            self.relative_error = abs(self.value - self.ground_truth) / abs(self.ground_truth) * 100.0
        elif self.ground_truth is not None and self.ground_truth == 0:
            # Handle division by zero case if ground truth is exactly 0
            self.relative_error = float('inf') if self.value != 0 else 0.0