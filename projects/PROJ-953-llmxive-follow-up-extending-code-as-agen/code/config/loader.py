import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Config:
    """Configuration container for the pipeline."""
    dataset_path: str = "data/raw"
    output_path: str = "data/processed"
    model_path: str = "models"
    log_path: str = "data/logs"
    graph_path: str = "data/graphs"
    contracts_path: str = "contracts"
    state_path: str = "state"
    timeout_seconds: int = 600
    sample_size: int = 500
    random_seed: int = 42

def get_dataset_path() -> str:
    """Returns the configured dataset path."""
    return os.getenv("LLMXIVE_DATASET_PATH", "data/raw")

def validate_config(config: Config) -> bool:
    """Validates that required directories exist or can be created."""
    required_dirs = [
        config.dataset_path,
        config.output_path,
        config.model_path,
        config.log_path,
        config.graph_path,
        config.contracts_path,
        config.state_path
    ]
    for d in required_dirs:
        p = Path(d)
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"Error creating directory {d}: {e}")
                return False
    return True

_global_config: Optional[Config] = None

def get_config(config_path: Optional[str] = None) -> Config:
    """Loads configuration from file or returns default."""
    global _global_config
    if _global_config is not None:
        return _global_config

    if config_path and os.path.exists(config_path):
        # Simple JSON/YAML loader could go here
        # For now, return default with env overrides
        pass
    
    _global_config = Config()
    if os.getenv("LLMXIVE_DATASET_PATH"):
        _global_config.dataset_path = os.getenv("LLMXIVE_DATASET_PATH")
    if os.getenv("LLMXIVE_OUTPUT_PATH"):
        _global_config.output_path = os.getenv("LLMXIVE_OUTPUT_PATH")
    
    return _global_config

def get_global_config() -> Config:
    """Returns the global configuration instance."""
    return get_config()
