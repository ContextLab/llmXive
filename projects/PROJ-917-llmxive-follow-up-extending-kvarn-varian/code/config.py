from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import os
import logging
import random
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Global configuration for the llmXive KVarN simulation project."""
    
    CPU_ONLY: bool = True
    EPSILON_FLOOR: float = 1e-6
    RANDOM_SEED: int = 42
    NUM_MATRICES: int = 10000
    SIMULATION_STEPS: int = 1000
    NUM_RUNS: int = 30
    BATCH_SIZE: int = 32
    LEARNING_RATE: float = 0.001
    NUM_EPOCHS: int = 50
    VALIDATION_SPLIT: float = 0.2
    OUTPUT_DIR: str = "data"
    MODEL_DIR: str = "data/models"
    RESULTS_DIR: str = "data/results"
    ANALYSIS_DIR: str = "data/analysis"
    SIMULATION_DIR: str = "data/simulation"
    
    # Epsilon sweep values for sensitivity analysis (T005b)
    # Defined to span multiple orders of magnitude as required by FR-007.
    # These values serve as the initial hardcoded defaults to break circular dependencies
    # before empirical bounds are derived in T005c.
    EPSILON_SWEEP_VALUES: List[float] = field(default_factory=lambda: [
        1e-8, 1e-7, 1e-6, 1e-5, 1e-4
    ])
    
    # Pilot bounds for epsilon validation (T005a)
    EPSILON_PILOT_BOUNDS: Dict[str, float] = field(default_factory=lambda: {
        "min": 0.0,
        "max": 0.1
    })
    
    # Quantization constants for Uniform INT8 Quantization (T009b)
    # FR-008: Required for T032_base quantization logic.
    # Uniform INT8 range is typically [-128, 127] for symmetric quantization.
    QUANTIZATION_MIN: int = -128
    QUANTIZATION_MAX: int = 127

_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        # Try to load from environment variables if available
        load_config_from_env(_config)
    return _config

def set_config(new_config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = new_config

def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _config
    _config = None

def load_config_from_env(config: Config = None) -> Config:
    """Load configuration from environment variables."""
    if config is None:
        config = get_config()
    
    env_mappings = {
        "CPU_ONLY": "CPU_ONLY",
        "EPSILON_FLOOR": "EPSILON_FLOOR",
        "RANDOM_SEED": "RANDOM_SEED",
        "NUM_MATRICES": "NUM_MATRICES",
        "SIMULATION_STEPS": "SIMULATION_STEPS",
        "NUM_RUNS": "NUM_RUNS",
        "BATCH_SIZE": "BATCH_SIZE",
        "LEARNING_RATE": "LEARNING_RATE",
        "NUM_EPOCHS": "NUM_EPOCHS",
    }
    
    for attr, env_var in env_mappings.items():
        if env_var in os.environ:
            try:
                val = os.environ[env_var]
                if attr in ["CPU_ONLY"]:
                    setattr(config, attr, val.lower() in ("true", "1", "yes"))
                elif attr in ["EPSILON_FLOOR", "LEARNING_RATE"]:
                    setattr(config, attr, float(val))
                else:
                    setattr(config, attr, int(val))
            except ValueError:
                logger.warning(f"Could not parse env var {env_var} for attribute {attr}")
    
    # Handle list config separately
    eps_sweep = os.environ.get("EPSILON_SWEEP_VALUES")
    if eps_sweep:
        try:
            # Expect format: "1e-8,1e-7,1e-6"
            values = [float(x.strip()) for x in eps_sweep.split(",")]
            config.EPSILON_SWEEP_VALUES = values
            logger.info(f"Loaded epsilon sweep values from env: {values}")
        except ValueError:
            logger.warning("Could not parse EPSILON_SWEEP_VALUES from environment")
    
    return config

def get_epsilon_sweep_values() -> List[float]:
    """Get the current epsilon sweep values from the global config."""
    return get_config().EPSILON_SWEEP_VALUES
