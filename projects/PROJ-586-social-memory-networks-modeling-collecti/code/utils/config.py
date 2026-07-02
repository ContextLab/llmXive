"""
Configuration management for the social memory network experiments.
Provides centralized configuration loading and validation.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    seed: int
    device: str
    max_tokens: int
    batch_size: int
    output_dir: str

def get_config(config_path: Optional[str] = None) -> ExperimentConfig:
    """
    Load configuration from file or use defaults.
    
    Args:
        config_path: Path to config.yaml. If None, uses default project config.
        
    Returns:
        ExperimentConfig with loaded or default values.
    """
    if config_path is None:
        # Default to project root config
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    # Default configuration (CPU-only, small model as per constraints)
    defaults = {
        'seed': 42,
        'device': 'cpu',
        'max_tokens': 512,
        'batch_size': 1,
        'output_dir': 'data'
    }

    if config_path.exists():
        with open(config_path, 'r') as f:
            loaded = yaml.safe_load(f)
            if loaded:
                defaults.update(loaded)

    return ExperimentConfig(
        seed=defaults.get('seed', 42),
        device=defaults.get('device', 'cpu'),
        max_tokens=defaults.get('max_tokens', 512),
        batch_size=defaults.get('batch_size', 1),
        output_dir=defaults.get('output_dir', 'data')
    )

def validate_config(config: ExperimentConfig) -> bool:
    """Validate configuration parameters."""
    if config.device not in ['cpu', 'cuda']:
        raise ValueError(f"Invalid device: {config.device}. Must be 'cpu' or 'cuda'.")
    
    if config.seed < 0:
        raise ValueError(f"Seed must be non-negative, got {config.seed}")
    
    if config.max_tokens <= 0:
        raise ValueError(f"max_tokens must be positive, got {config.max_tokens}")
        
    return True
