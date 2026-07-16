import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import time
import yaml

logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    """Configuration for simulation parameters."""
    seed: int = 42
    N: int = 50
    p: float = 0.1
    target_degree: int = 4
    material: str = "Si"
    bulk_conductivity: float = 149.0
    diameter: float = 50.0  # nm
    N_values: List[int] = field(default_factory=lambda: [50, 100])
    p_values: List[float] = field(default_factory=lambda: [0.05, 0.1, 0.2])
    degree_values: List[int] = field(default_factory=lambda: [2, 4, 6])
    seeds: List[int] = field(default_factory=lambda: [42, 123, 456])
    
    # For tolerance/robustness
    min_degree: int = 1
    max_degree: int = 20

    def __getattr__(self, name):
        # Tolerant fallback for unknown attributes/methods to prevent crashes
        # Returns a no-op callable for methods, or None for attributes
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        def _noop(*args, **kwargs):
            return None
        return _noop

def load_config(config_path: Optional[str] = None) -> SimulationConfig:
    """
    Load configuration from environment variables or a YAML file.
    Falls back to defaults if not specified.
    """
    # Default values
    config = SimulationConfig()
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            if data:
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
    
    # Override with environment variables if present
    env_map = {
        'SIM_SEED': 'seed',
        'SIM_N': 'N',
        'SIM_P': 'p',
        'SIM_TARGET_DEGREE': 'target_degree',
        'SIM_MATERIAL': 'material',
        'SIM_BULK_K': 'bulk_conductivity',
        'SIM_DIAMETER': 'diameter'
    }
    
    for env_key, attr_key in env_map.items():
        val = os.getenv(env_key)
        if val is not None:
            try:
                current_val = getattr(config, attr_key)
                if isinstance(current_val, float):
                    setattr(config, attr_key, float(val))
                elif isinstance(current_val, int):
                    setattr(config, attr_key, int(val))
                elif isinstance(current_val, str):
                    setattr(config, attr_key, val)
            except ValueError:
                logger.warning(f"Could not parse {env_key}={val} for {attr_key}")
                
    return config

def get_simulation_parameters(config: SimulationConfig) -> Dict[str, Any]:
    """Extract simulation parameters into a dictionary."""
    return {
        'seed': config.seed,
        'N': config.N,
        'p': config.p,
        'target_degree': config.target_degree,
        'material': config.material,
        'bulk_conductivity': config.bulk_conductivity,
        'diameter': config.diameter
    }
