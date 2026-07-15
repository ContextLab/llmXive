"""
Data models for the variable selection impact study.

Defines the core data structures for simulated datasets and power metrics.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import numpy as np


@dataclass
class SimulatedDataset:
    """
    Represents a simulated dataset derived from a real OpenML regression dataset.

    Attributes:
        X (np.ndarray): The feature matrix (n_samples, n_features).
        Y (np.ndarray): The target vector (n_samples,).
        true_coefficients (np.ndarray): The ground-truth coefficients used to generate Y.
        snr (float): Signal-to-Noise Ratio used in simulation.
        sparsity (float): Sparsity level (proportion of non-zero coefficients) used.
        seed (int): Random seed used for reproducibility.
        dataset_id (int): The OpenML dataset ID this simulation is based on.
    """
    X: np.ndarray
    Y: np.ndarray
    true_coefficients: np.ndarray
    snr: float
    sparsity: float
    seed: int
    dataset_id: int

    def __post_init__(self):
        """Ensure arrays are numpy arrays and shapes are consistent."""
        if not isinstance(self.X, np.ndarray):
            self.X = np.array(self.X)
        if not isinstance(self.Y, np.ndarray):
            self.Y = np.array(self.Y)
        if not isinstance(self.true_coefficients, np.ndarray):
            self.true_coefficients = np.array(self.true_coefficients)

        # Basic shape validation
        n_samples, n_features = self.X.shape
        if self.Y.shape != (n_samples,):
            raise ValueError(f"Y shape {self.Y.shape} does not match X samples {n_samples}")
        if self.true_coefficients.shape != (n_features,):
            raise ValueError(f"Coefficients shape {self.true_coefficients.shape} does not match X features {n_features}")


@dataclass
class PowerMetric:
    """
    Represents a computed power metric for a specific selection method and condition.

    Attributes:
        method (str): Name of the selection method (e.g., 'forward_stepwise', 'lasso').
        snr (float): Signal-to-Noise Ratio for this run.
        sparsity (float): Sparsity level for this run.
        alpha (float): Significance threshold used (e.g., 0.05).
        power_rate (float): Empirical power (proportion of true non-zero coeffs selected & significant).
        ci_lower (Optional[float]): Lower bound of the confidence interval for power_rate.
        ci_upper (Optional[float]): Upper bound of the confidence interval for power_rate.
    """
    method: str
    snr: float
    sparsity: float
    alpha: float
    power_rate: float
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None

    def __post_init__(self):
        """Validate numeric ranges."""
        if not (0.0 <= self.power_rate <= 1.0):
            raise ValueError(f"power_rate must be between 0 and 1, got {self.power_rate}")
        if self.ci_lower is not None and self.ci_upper is not None:
            if not (0.0 <= self.ci_lower <= self.ci_upper <= 1.0):
                raise ValueError(f"Confidence interval bounds invalid: [{self.ci_lower}, {self.ci_upper}]")