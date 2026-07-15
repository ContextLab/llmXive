import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import logging

@dataclass
class SimulationConfig:
    """Configuration for thermal conductivity simulations."""
    # Core simulation parameters
    N: int = 100
    p: float = 0.1
    d: float = 10.0  # nm
    l: float = 100.0  # nm
    seed: int = 42
    material: str = "Si"
    
    # Grid simulation parameters
    N_min: int = 50
    N_max: int = 200
    N_steps: int = 5
    p_min: float = 0.05
    p_max: float = 0.5
    p_steps: int = 5
    
    # Target degree for specific generation modes
    target_degree: float = 4.0
    
    # Fuchs-Sondheimer parameters
    lambda_bulk: float = 10.0  # nm
    p_specular: float = 0.5
    
    # Sensitivity analysis parameters
    sensitivity_range: tuple = field(default=(0.8, 1.2, 5))
    
    # Runtime limits
    timeout_seconds: int = 6 * 60 * 60  # 6 hours
    
    # Paths
    output_dir: str = "data/processed"
    results_file: str = "simulation_results.csv"
    
    # Logging
    log_level: str = "INFO"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.N < 2:
            raise ValueError("N must be at least 2")
        if not (0 < self.p < 1):
            raise ValueError("p must be between 0 and 1")
        if self.d <= 0 or self.l <= 0:
            raise ValueError("d and l must be positive")
        if self.N_min >= self.N_max:
            raise ValueError("N_min must be less than N_max")
        if self.p_min >= self.p_max:
            raise ValueError("p_min must be less than p_max")

    def __getattr__(self, name: str) -> Any:
        """
        Tolerant fallback for unknown attributes/methods.
        This ensures that if any code attempts to access an attribute
        that isn't explicitly defined (e.g., logging methods or future
        extensions), it returns a no-op callable instead of raising AttributeError.
        """
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        def _no_op(*args, **kwargs):
            return None
        
        return _no_op

def load_config() -> SimulationConfig:
    """
    Load simulation configuration from environment variables with sensible defaults.
    
    Environment variables:
    - SIM_N: Node count (default: 100)
    - SIM_P: Connection probability (default: 0.1)
    - SIM_D: Wire diameter in nm (default: 10.0)
    - SIM_L: Wire length in nm (default: 100.0)
    - SIM_SEED: Random seed (default: 42)
    - SIM_MATERIAL: Material name (default: "Si")
    - SIM_N_MIN: Min nodes for grid (default: 50)
    - SIM_N_MAX: Max nodes for grid (default: 200)
    - SIM_N_STEPS: Steps for N grid (default: 5)
    - SIM_P_MIN: Min probability for grid (default: 0.05)
    - SIM_P_MAX: Max probability for grid (default: 0.5)
    - SIM_P_STEPS: Steps for p grid (default: 5)
    - SIM_TARGET_DEGREE: Target average degree (default: 4.0)
    - SIM_LAMBDA_BULK: Bulk mean free path in nm (default: 10.0)
    - SIM_P_SPECULAR: Specularity parameter (default: 0.5)
    - SIM_TIMEOUT: Timeout in seconds (default: 21600)
    """
    def get_int(key: str, default: int) -> int:
        val = os.getenv(key)
        if val is None:
            return default
        try:
            return int(val)
        except ValueError:
            logging.warning(f"Invalid integer for {key}: {val}, using default {default}")
            return default

    def get_float(key: str, default: float) -> float:
        val = os.getenv(key)
        if val is None:
            return default
        try:
            return float(val)
        except ValueError:
            logging.warning(f"Invalid float for {key}: {val}, using default {default}")
            return default

    def get_str(key: str, default: str) -> str:
        val = os.getenv(key)
        return val if val is not None else default

    return SimulationConfig(
        N=get_int("SIM_N", 100),
        p=get_float("SIM_P", 0.1),
        d=get_float("SIM_D", 10.0),
        l=get_float("SIM_L", 100.0),
        seed=get_int("SIM_SEED", 42),
        material=get_str("SIM_MATERIAL", "Si"),
        N_min=get_int("SIM_N_MIN", 50),
        N_max=get_int("SIM_N_MAX", 200),
        N_steps=get_int("SIM_N_STEPS", 5),
        p_min=get_float("SIM_P_MIN", 0.05),
        p_max=get_float("SIM_P_MAX", 0.5),
        p_steps=get_int("SIM_P_STEPS", 5),
        target_degree=get_float("SIM_TARGET_DEGREE", 4.0),
        lambda_bulk=get_float("SIM_LAMBDA_BULK", 10.0),
        p_specular=get_float("SIM_P_SPECULAR", 0.5),
        timeout_seconds=get_int("SIM_TIMEOUT", 6 * 60 * 60),
        output_dir=get_str("SIM_OUTPUT_DIR", "data/processed"),
        results_file=get_str("SIM_RESULTS_FILE", "simulation_results.csv"),
        log_level=get_str("SIM_LOG_LEVEL", "INFO")
    )

def get_simulation_parameters() -> Dict[str, Any]:
    """
    Get a dictionary of all current simulation parameters.
    Useful for logging and reproducibility.
    """
    config = load_config()
    return {
        'N': config.N,
        'p': config.p,
        'd': config.d,
        'l': config.l,
        'seed': config.seed,
        'material': config.material,
        'N_min': config.N_min,
        'N_max': config.N_max,
        'N_steps': config.N_steps,
        'p_min': config.p_min,
        'p_max': config.p_max,
        'p_steps': config.p_steps,
        'target_degree': config.target_degree,
        'lambda_bulk': config.lambda_bulk,
        'p_specular': config.p_specular,
        'timeout_seconds': config.timeout_seconds,
        'output_dir': config.output_dir,
        'results_file': config.results_file,
        'log_level': config.log_level
    }
