import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class Config:
    """Configuration manager for the project."""
    seed: int = 42
    ram_limit_gb: float = 7.0
    paths: Dict[str, str] = field(default_factory=lambda: {
        'raw': 'data/raw',
        'processed': 'data/processed',
        'artifacts': 'data/artifacts',
        'logs': 'data/logs',
        'figures': 'figures'
    })
    hyperparameters: Dict[str, Any] = field(default_factory=lambda: {
        'rf_n_trees': 500,
        'vlm_epochs': 10,
        'batch_size': 32
    })

_global_config: Optional[Config] = None

def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def reset_config():
    global _global_config
    _global_config = None

def get_available_ram_gb() -> float:
    """Estimate available RAM (simplified)."""
    # In a real system, this might check /proc/meminfo or psutil
    return 7.0

def main():
    """Entry point for config test."""
    logger.info("Config module loaded successfully.")
    cfg = get_config()
    logger.info(f"Current RAM limit: {cfg.ram_limit_gb} GB")

if __name__ == "__main__":
    from utils.logging_config import setup_logging
    setup_logging()
    main()
