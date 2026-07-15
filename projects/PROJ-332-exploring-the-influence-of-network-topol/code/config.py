import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import time
import yaml

logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    """Configuration container for simulation parameters."""
    N: int = 100
    p: float = 0.1
    d: float = 10.0  # nm
    l: float = 100.0  # nm
    seed: int = 42
    material: str = "Si"
    bulk_conductivity: Optional[float] = None
    target_degree: Optional[float] = None
    timeout_hours: float = 6.0
    sensitivity_factors: List[float] = field(default_factory=lambda: [0.5, 0.75, 1.0, 1.25, 1.5])

    # Tolerant attribute access for any dynamic logger-like calls
    def __getattr__(self, name: str) -> Any:
        # If any script calls .info(), .debug(), .warning(), etc. on this config,
        # return a no-op callable to prevent AttributeError.
        if name in ("info", "debug", "warning", "error", "critical", "log"):
            def _noop(*args: Any, **kwargs: Any) -> None:
                pass
            return _noop
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

def load_config(config_path: Optional[str] = None) -> SimulationConfig:
    """Load configuration from a YAML file or return defaults."""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            return SimulationConfig(**{k: v for k, v in data.items() if hasattr(SimulationConfig, k)})
    return SimulationConfig()

def get_simulation_parameters() -> Dict[str, Any]:
    """Get current simulation parameters from environment or defaults."""
    return {
        "N": int(os.getenv("SIM_N", "100")),
        "p": float(os.getenv("SIM_P", "0.1")),
        "d": float(os.getenv("SIM_D", "10.0")),
        "l": float(os.getenv("SIM_L", "100.0")),
        "seed": int(os.getenv("SIM_SEED", "42")),
        "material": os.getenv("SIM_MATERIAL", "Si"),
    }
