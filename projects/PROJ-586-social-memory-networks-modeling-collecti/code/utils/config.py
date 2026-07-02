"""
Configuration management for the social memory network project.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Config:
    """Project configuration."""
    seed: int = 42
    device: str = "cpu"
    max_rounds: int = 10
    memory_max_size: int = 1000
    experiment_name: str = "social_memory_experiment"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'seed': self.seed,
            'device': self.device,
            'max_rounds': self.max_rounds,
            'memory_max_size': self.memory_max_size,
            'experiment_name': self.experiment_name
        }

_config: Optional[Config] = None

def get_config() -> Config:
    """Get the project configuration."""
    global _config
    if _config is None:
        # Load from environment or use defaults
        _config = Config(
            seed=int(os.getenv('SEED', 42)),
            device=os.getenv('DEVICE', 'cpu')
        )
    return _config

def set_config(config: Config) -> None:
    """Set the project configuration."""
    global _config
    _config = config
