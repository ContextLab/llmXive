"""
Configuration Loader Module for llmXive.

This module provides configuration management for the pipeline,
including environment variables and dataset paths.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Config:
    """Configuration container."""
    dataset_path: str = "data/raw"
    processed_path: str = "data/processed"
    graphs_path: str = "data/graphs"
    models_path: str = "models"
    state_path: str = "state/projects/llmxive.yaml"
    timeout: float = 300.0
    random_seed: int = 42
    additional_params: Dict[str, Any] = field(default_factory=dict)

def get_dataset_path(dataset_name: str, config: Optional[Config] = None) -> Path:
    """Get path for a specific dataset."""
    if config is None:
        config = get_config()
    
    base_path = Path(config.dataset_path)
    return base_path / dataset_name

def validate_config(config: Config) -> bool:
    """Validate configuration."""
    required_paths = [
        config.dataset_path,
        config.processed_path,
        config.graphs_path,
        config.models_path
    ]
    
    for path in required_paths:
        if not Path(path).parent.exists():
            print(f"Warning: Parent directory for {path} does not exist")
            return False
    
    return True

def get_config() -> Config:
    """Get configuration from environment or defaults."""
    config = Config()
    
    # Override from environment variables
    if os.getenv("LLMXIVE_DATASET_PATH"):
        config.dataset_path = os.getenv("LLMXIVE_DATASET_PATH")
    
    if os.getenv("LLMXIVE_PROCESSED_PATH"):
        config.processed_path = os.getenv("LLMXIVE_PROCESSED_PATH")
    
    if os.getenv("LLMXIVE_GRAPHS_PATH"):
        config.graphs_path = os.getenv("LLMXIVE_GRAPHS_PATH")
    
    if os.getenv("LLMXIVE_MODELS_PATH"):
        config.models_path = os.getenv("LLMXIVE_MODELS_PATH")
    
    if os.getenv("LLMXIVE_TIMEOUT"):
        config.timeout = float(os.getenv("LLMXIVE_TIMEOUT"))
    
    if os.getenv("LLMXIVE_RANDOM_SEED"):
        config.random_seed = int(os.getenv("LLMXIVE_RANDOM_SEED"))
    
    return config

def get_global_config() -> Config:
    """Get global configuration (singleton pattern)."""
    if not hasattr(get_global_config, "_config"):
        get_global_config._config = get_config()
    return get_global_config._config

# Re-export validate_config for compatibility
__all__ = [
    "Config",
    "get_dataset_path",
    "validate_config",
    "get_config",
    "get_global_config"
]
