from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Config:
    """
    Global configuration for the Normalized Gaps Between Consecutive Squarefree Numbers project.
    
    This configuration defines the cutoffs for N and the random seed for reproducibility.
    """
    N_cutoffs: List[int]
    random_seed: int

# Global instance as per project requirements
CONFIG = Config(
    N_cutoffs=[10**6, 5*10**6, 10**7],
    random_seed=42
)