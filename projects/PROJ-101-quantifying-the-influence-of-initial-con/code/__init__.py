"""
llmXive Project: Quantifying the Influence of Initial Conditions on Chaotic Systems

This package provides tools for generating chaotic trajectories,
computing Finite-Time Lyapunov Exponents (FTLE), and analyzing
the scaling of deviations with noise and system dimension.
"""

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

from .config import get_full_config, set_simulation_seed
from .utils.stability import check_boundedness, check_convergence
from .data.generator import generate_coupled_lorenz_trajectory
from .analysis.ftle import compute_ftle_single_trajectory
from .analysis.baseline import compute_asymptotic_baseline

__all__ = [
    'get_full_config',
    'set_simulation_seed',
    'check_boundedness',
    'check_convergence',
    'generate_coupled_lorenz_trajectory',
    'compute_ftle_single_trajectory',
    'compute_asymptotic_baseline'
]