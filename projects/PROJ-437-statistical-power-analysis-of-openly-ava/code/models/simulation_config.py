"""
SimulationConfig model.

Centralises the configuration parameters that drive a single simulation run.
The dataclass is deliberately lightweight – it only stores values that are
needed across the pipeline. Validation (e.g. against a JSON schema) is
performed elsewhere; this class merely provides a convenient, typed container.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SimulationConfig:
    """
    Configuration for a power‑analysis simulation.

    Attributes
    ----------
    sample_size_target: Desired number of subjects (will be clamped to the
                         available number of subjects by the pipeline).
    smoothing_kernel: Temporal smoothing kernel size in millimetres.
    num_iterations: Number of bootstrap iterations (must be >= 1).
    random_seed: Global seed for reproducibility.
    effect_sizes: List of ground‑truth Cohen's d values to inject.
    alpha_thresholds: List of significance thresholds.
    snr_levels: List of signal‑to‑noise ratios to simulate.
    magnitude_tolerances: List of percentage tolerances (e.g. 10.0 for ±10 %).
    """
    sample_size_target: int
    smoothing_kernel: float
    num_iterations: int = 50
    random_seed: int = 42
    effect_sizes: List[float] = field(default_factory=lambda: [0.0, 0.2, 0.5, 0.8, 1.0])
    alpha_thresholds: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.10])
    snr_levels: List[float] = field(default_factory=lambda: [0.5, 1.0, 2.0])
    magnitude_tolerances: List[float] = field(default_factory=lambda: [10.0, 20.0, 30.0])

    def __post_init__(self) -> None:
        if self.sample_size_target <= 0:
            raise ValueError("sample_size_target must be a positive integer")
        if self.smoothing_kernel <= 0:
            raise ValueError("smoothing_kernel must be positive")
        if self.num_iterations < 1:
            raise ValueError("num_iterations must be >= 1")
        # Ensure lists are not empty
        for name in (
            "effect_sizes",
            "alpha_thresholds",
            "snr_levels",
            "magnitude_tolerances",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} must contain at least one element")
