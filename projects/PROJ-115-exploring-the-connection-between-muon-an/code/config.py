"""
Project Configuration and Hyperparameters.

Defines the coarse and fine grid parameters as required by T018 (US5).
These parameters are used by the AMR strategy and the main scan pipeline.
"""
from dataclasses import dataclass
from typing import Tuple

@dataclass
class GridParams:
    """Parameters for the parameter scan grid."""
    m_chi_min: float = 1.0       # MeV
    m_chi_max: float = 1000.0    # MeV
    m_V_min: float = 1.0         # MeV
    m_V_max: float = 2000.0      # MeV
    g_min: float = 1e-5
    g_max: float = 1e-1
    
    # Coarse grid (for initial exploration/convergence study)
    coarse_steps_chi: int = 20
    coarse_steps_V: int = 20
    coarse_steps_g: int = 10
    
    # Fine grid (for final production if AMR not used, or base for AMR)
    fine_steps_chi: int = 100
    fine_steps_V: int = 100
    fine_steps_g: int = 50

    # AMR Configuration (Plan 0.3)
    amr_max_depth: int = 4
    amr_sensitivity_threshold: float = 0.1
    amr_min_cell_size_chi: float = 0.1
    amr_min_cell_size_V: float = 0.1
    amr_min_cell_size_g: float = 1e-6

# Global configuration instance
GRID_CONFIG = GridParams()

# Physics Constants
PHYSICS_CONSTANTS = {
    "alpha_em": 1/137.035999,
    "m_e": 0.510998950,  # MeV
    "m_mu": 105.6583755, # MeV
    "hbar_c": 197.3269804 # MeV fm
}

# Data Paths
DATA_PATHS = {
    "raw": "data/raw",
    "processed": "data/processed",
    "figures": "figures",
    "benchmarks": "data/benchmarks"
}
