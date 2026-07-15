import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import time

@dataclass
class SimulationConfig:
    """Configuration container for simulation parameters."""
    
    # Core simulation parameters
    N: int = 100  # Number of nodes
    p: float = 0.1  # Connection probability
    d: float = 50.0  # Wire diameter in nm
    l: float = 1000.0  # Wire length in nm
    seed: int = 42  # Random seed
    
    # Material parameters
    material: str = "Si"  # Material name (default: Silicon)
    bulk_conductivity: Optional[float] = None  # Override bulk conductivity
    
    # Solver parameters
    lambda_phonon: float = 10.0  # Phonon mean free path in nm
    specularity: float = 0.5  # Specularity parameter for Fuchs-Sondheimer
    
    # Analysis parameters
    runtime_limit_hours: float = 6.0  # Maximum runtime in hours
    target_degree: float = 4.0  # Target average degree for generation
    
    # Grid simulation parameters
    grid_N_values: list = field(default_factory=lambda: [50, 100, 200])
    grid_p_values: list = field(default_factory=lambda: [0.05, 0.1, 0.2, 0.3])
    grid_degree_values: list = field(default_factory=lambda: [2.0, 3.0, 4.0, 5.0])
    
    # Sensitivity analysis parameters
    sensitivity_factor_range: list = field(default_factory=lambda: [0.5, 0.75, 1.0, 1.25, 1.5])
    sensitivity_metric: str = "conductivity"  # Metric to analyze
    
    # Output paths
    output_csv: str = "data/processed/simulation_results.csv"
    log_file: Optional[str] = None
    
    # Percolation threshold (computed)
    percolation_threshold: Optional[float] = None
    
    # Sensitivity results (computed)
    sensitivity_deviation: Optional[float] = None
    sensitivity_std: Optional[float] = None
    sensitivity_mean: Optional[float] = None

    def __post_init__(self):
        """Validate and post-process configuration."""
        if self.bulk_conductivity is None:
            # Will be loaded from material_db later
            pass
        
        # Ensure lists are mutable
        if isinstance(self.grid_N_values, tuple):
            self.grid_N_values = list(self.grid_N_values)
        if isinstance(self.grid_p_values, tuple):
            self.grid_p_values = list(self.grid_p_values)
        if isinstance(self.grid_degree_values, tuple):
            self.grid_degree_values = list(self.grid_degree_values)
        if isinstance(self.sensitivity_factor_range, tuple):
            self.sensitivity_factor_range = list(self.sensitivity_factor_range)

    # Logger-like fallback for tolerance
    def __getattr__(self, name):
        # Any unknown attribute access returns a no-op callable
        def _noop(*args, **kwargs):
            return None
        return _noop

def load_config(env_prefix: str = "SIM_") -> SimulationConfig:
    """Load configuration from environment variables with defaults."""
    config_dict = {}
    
    # Map environment variables to config fields
    env_mapping = {
        "N": "SIM_N",
        "p": "SIM_P",
        "d": "SIM_D",
        "l": "SIM_L",
        "seed": "SIM_SEED",
        "material": "SIM_MATERIAL",
        "bulk_conductivity": "SIM_BULK_CONDUCTIVITY",
        "lambda_phonon": "SIM_LAMBDA",
        "specularity": "SIM_SPECULARITY",
        "runtime_limit_hours": "SIM_RUNTIME_LIMIT",
        "target_degree": "SIM_TARGET_DEGREE",
        "output_csv": "SIM_OUTPUT_CSV",
    }
    
    for field_name, env_var in env_mapping.items():
        value = os.environ.get(env_var)
        if value is not None:
            # Try to convert to appropriate type
            try:
                if field_name in ["N", "seed"]:
                    config_dict[field_name] = int(value)
                elif field_name in ["p", "d", "l", "bulk_conductivity", 
                                   "lambda_phonon", "specularity", 
                                   "runtime_limit_hours", "target_degree"]:
                    config_dict[field_name] = float(value)
                else:
                    config_dict[field_name] = value
            except ValueError:
                logging.warning(f"Invalid value for {field_name}: {value}, using default")
    
    return SimulationConfig(**config_dict)

def get_simulation_parameters(config: SimulationConfig) -> Dict[str, Any]:
    """Extract simulation parameters from config for logging."""
    return {
        "N": config.N,
        "p": config.p,
        "d": config.d,
        "l": config.l,
        "seed": config.seed,
        "material": config.material,
        "target_degree": config.target_degree,
        "runtime_limit_hours": config.runtime_limit_hours,
    }
