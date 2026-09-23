"""
Simulation configuration entity.

Defines the parameters for running simulation-based power analysis.
"""
from dataclasses import dataclass
from typing import Optional
from utils.seed_manager import set_global_seed, get_seed


@dataclass(frozen=True)
class SimulationConfig:
    """
    Configuration for simulation-based power analysis.

    Attributes:
        sample_size_target: Target number of subjects for the simulation.
        smoothing_kernel: Smoothing kernel size in mm (or seconds for temporal).
        num_iterations: Number of bootstrap iterations to run.
        random_seed: Optional random seed for reproducibility. If None, no seed is set.
    """
    sample_size_target: int
    smoothing_kernel: float
    num_iterations: int
    random_seed: Optional[int] = None

    def __post_init__(self):
        """Validate configuration parameters after initialization."""
        if self.sample_size_target <= 0:
            raise ValueError("sample_size_target must be greater than 0")
        if self.smoothing_kernel <= 0:
            raise ValueError("smoothing_kernel must be greater than 0")
        if self.num_iterations <= 0:
            raise ValueError("num_iterations must be greater than 0")

    def apply_seed(self) -> None:
        """
        Apply the random seed if one is configured.

        Does nothing if random_seed is None.
        """
        if self.random_seed is not None:
            set_global_seed(self.random_seed)