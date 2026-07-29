"""
Configuration management module.
Loads paths, seeds, and other settings.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger

logger = get_logger(__name__)

class Config:
    """Configuration container."""
    def __init__(self, data_dir: str = "data", models_dir: str = "models", results_dir: str = "results", random_seed: int = 42):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.results_dir = Path(results_dir)
        self.random_seed = random_seed
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "processed").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(parents=True, exist_ok=True)

_config: Optional[Config] = None

def get_config() -> Config:
    """
    Gets the global configuration instance.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config

def main():
    """CLI entry point for testing config."""
    cfg = get_config()
    logger.info(f"Data dir: {cfg.data_dir}")
    logger.info(f"Models dir: {cfg.models_dir}")
    logger.info(f"Results dir: {cfg.results_dir}")

if __name__ == "__main__":
    main()
