"""
Simulation configuration entity for statistical power analysis.

Defines the `SimulationConfig` dataclass used to parameterize
the Monte Carlo simulation pipeline (sample size, smoothing, iterations, seed).
"""
from dataclasses import dataclass
from typing import Optional
from utils.seed_manager import set_global_seed


@dataclass(frozen=True)
class SimulationConfig:
    """
    Configuration entity for running power analysis simulations.

    Attributes:
        sample_size_target (int): The target number of subjects for the simulation.
            Must be a positive integer.
        smoothing_kernel (float): The temporal smoothing kernel size in mm (or equivalent
            time units depending on the preprocessing pipeline).
        num_iterations (int): The number of bootstrap/Monte Carlo iterations to run.
            Must be a positive integer.
        random_seed (Optional[int]): The random seed for reproducibility. If None,
            the system will attempt to use the global seed or a default.
    """
    sample_size_target: int
    smoothing_kernel: float
    num_iterations: int
    random_seed: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate configuration constraints."""
        if self.sample_size_target <= 0:
            raise ValueError("sample_size_target must be greater than 0")
        if self.smoothing_kernel <= 0:
            raise ValueError("smoothing_kernel must be greater than 0")
        if self.num_iterations <= 0:
            raise ValueError("num_iterations must be greater than 0")

    def apply_seed(self) -> None:
        """
        Apply the random seed to the global environment if one is provided.

        Uses the `set_global_seed` function from `utils.seed_manager`.
        """
        if self.random_seed is not None:
            set_global_seed(self.random_seed)