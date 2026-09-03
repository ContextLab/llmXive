"""
Configuration module for the chaotic systems analysis pipeline.

Defines hyperparameters, numerical tolerances, and simulation settings
required for generating and analyzing chaotic trajectories.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import numpy as np


@dataclass
class NumericalSettings:
    """Numerical integration tolerances and solver settings."""
    rtol: float = 1e-9
    atol: float = 1e-12
    method: str = "DOP853"
    max_step: float = 0.01
    first_step: Optional[float] = None
    
    def __post_init__(self):
        if self.rtol <= 0 or self.atol <= 0:
            raise ValueError("Tolerances must be positive")
        if self.rtol > 1e-3 or self.atol > 1e-3:
            raise ValueError("Tolerances are too loose for chaotic systems")

@dataclass
class SimulationConfig:
    """Configuration for Lorenz oscillator simulations."""
    # Lorenz system parameters
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0
    
    # Integration time settings
    t_max: float = 1000.0
    dt_output: float = 0.01
    
    # Initial condition settings
    seed: int = 42
    initial_perturbation_scale: float = 1e-10
    
    # Coupling settings
    coupling_strength: float = 0.01
    coupling_topology: str = "ring"  # Options: "ring", "all_to_all", "random"
    
    # Dimensionality
    N_oscillators: int = 5
    
    # Noise settings
    noise_levels: List[float] = field(default_factory=lambda: [1e-4, 1e-3, 1e-2, 1e-1, 0.5, 1.0])
    noise_seed: int = 12345
    
    # Validation thresholds
    unphysical_threshold: float = 100.0
    high_noise_warning_threshold: float = 0.1
    high_noise_error_threshold: float = 1.0
    
    # FTLE settings
    ftle_window_sizes: List[int] = field(default_factory=lambda: [500, 1000, 5000])
    ftle_seed: int = 54321
    
    # Regression settings
    num_trials_per_noise: int = 30
    regression_seed: int = 98765
    
    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.sigma <= 0 or self.rho <= 0 or self.beta <= 0:
            raise ValueError("Lorenz parameters must be positive")
        if self.N_oscillators < 1:
            raise ValueError("N_oscillators must be at least 1")
        if self.t_max <= 0:
            raise ValueError("t_max must be positive")
        if self.dt_output <= 0:
            raise ValueError("dt_output must be positive")
        if any(n < 0 for n in self.noise_levels):
            raise ValueError("Noise levels must be non-negative")
        if self.unphysical_threshold <= 0:
            raise ValueError("unphysical_threshold must be positive")
        if self.high_noise_warning_threshold >= self.high_noise_error_threshold:
            raise ValueError("Warning threshold must be less than error threshold")

@dataclass
class AnalysisConfig:
    """Configuration for analysis and visualization."""
    # Baseline computation
    baseline_convergence_tolerance: float = 1e-6
    baseline_min_T: int = 5000
    
    # Regression analysis
    regression_model_candidates: List[str] = field(
        default_factory=lambda: ["additive", "multiplicative", "saturation"]
    )
    aic_weight_threshold: float = 0.9
    
    # Visualization
    plot_dpi: int = 300
    plot_font_size: int = 12
    plot_style: str = "seaborn-v0_8-whitegrid"
    
    # Output paths
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    figures_dir: str = "figures"
    
    def validate(self) -> None:
        """Validate analysis configuration."""
        if self.baseline_convergence_tolerance <= 0:
            raise ValueError("Convergence tolerance must be positive")
        if self.baseline_min_T < 100:
            raise ValueError("baseline_min_T must be at least 100")
        if self.plot_dpi < 50 or self.plot_dpi > 1200:
            raise ValueError("plot_dpi must be between 50 and 1200")

# Global configuration instances
numerical_settings = NumericalSettings()
simulation_config = SimulationConfig()
analysis_config = AnalysisConfig()

# Convenience constants
DEFAULT_SEED = simulation_config.seed
DEFAULT_N = simulation_config.N_oscillators
DEFAULT_NOISE_LEVELS = simulation_config.noise_levels
DEFAULT_RTOl = numerical_settings.rtol
DEFAULT_ATOL = numerical_settings.atol

def get_full_config() -> dict:
    """Return all configuration as a nested dictionary."""
    return {
        "numerical": {
            "rtol": numerical_settings.rtol,
            "atol": numerical_settings.atol,
            "method": numerical_settings.method,
            "max_step": numerical_settings.max_step,
        },
        "simulation": {
            "sigma": simulation_config.sigma,
            "rho": simulation_config.rho,
            "beta": simulation_config.beta,
            "t_max": simulation_config.t_max,
            "dt_output": simulation_config.dt_output,
            "seed": simulation_config.seed,
            "N_oscillators": simulation_config.N_oscillators,
            "noise_levels": simulation_config.noise_levels,
            "unphysical_threshold": simulation_config.unphysical_threshold,
        },
        "analysis": {
            "baseline_convergence_tolerance": analysis_config.baseline_convergence_tolerance,
            "baseline_min_T": analysis_config.baseline_min_T,
            "num_trials_per_noise": analysis_config.num_trials_per_noise,
        }
    }

def set_simulation_seed(seed: int) -> None:
    """Set the random seed for reproducible simulations."""
    simulation_config.seed = seed
    np.random.seed(seed)

def set_noise_levels(levels: List[float]) -> None:
    """Set custom noise levels for simulation."""
    if any(l < 0 for l in levels):
        raise ValueError("Noise levels must be non-negative")
    simulation_config.noise_levels = levels

def set_N_oscillators(n: int) -> None:
    """Set the number of coupled oscillators."""
    if n < 1:
        raise ValueError("N_oscillators must be at least 1")
    simulation_config.N_oscillators = n
    
    # Update ftle window constraints based on new N
    if simulation_config.t_max / simulation_config.dt_output < 1000:
        # Adjust window sizes if total trajectory length is small
        max_windows = int(simulation_config.t_max / simulation_config.dt_output) - 10
        simulation_config.ftle_window_sizes = [
            min(w, max_windows) for w in [500, 1000, 5000] if w <= max_windows
        ]
    
    if not simulation_config.ftle_window_sizes:
        simulation_config.ftle_window_sizes = [100]  # Minimum window size
