"""
Configuration manager for the llmXive research pipeline.

Handles project paths, random seeds, and environment-specific settings.
Ensures reproducibility and consistent file structure access.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Import existing utilities
from utils.logger import get_logger, log_execution_start, log_execution_end

logger = get_logger(__name__)

# Project root relative to this file (code/data/ -> ../..)
_ROOT_RELATIVE = Path(__file__).resolve().parent.parent.parent

class Config:
    """
    Central configuration manager for seeds and paths.
    
    Loads settings from a YAML file if available, otherwise uses defaults.
    Provides typed access to paths and ensures directories exist.
    """

    def __init__(self, config_path: Optional[Path] = None, seed: Optional[int] = None):
        self._config_path = config_path or _ROOT_RELATIVE / "state" / "config.yaml"
        self._seed = seed
        self._config: Dict[str, Any] = {}
        self._root_path: Path = _ROOT_RELATIVE

        self._load_config()
        self._initialize_paths()
        self._initialize_seed()

        logger.info(f"Configuration initialized. Root: {self._root_path}")

    def _load_config(self) -> None:
        """Load configuration from YAML file if it exists."""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self._config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self._config_path}: {e}. Using defaults.")
        else:
            logger.info(f"No config file found at {self._config_path}. Using defaults.")

    def _initialize_paths(self) -> None:
        """Ensure standard directory structure exists."""
        dirs = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "data/figures",
            "tests",
            "tests/unit",
            "tests/contract",
            "docs",
            "state",
            "state/projects/PROJ-490-the-effect-of-simulated-social-compariso",
        ]
        
        for dir_name in dirs:
            dir_path = self._root_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug("Directory structure ensured.")

    def _initialize_seed(self) -> None:
        """Initialize random seeds for reproducibility."""
        seed = self._seed or self._config.get("seed", 42)
        self._seed = seed
        
        random.seed(seed)
        # Note: numpy and torch seeds are handled in specific modules when those libraries are used
        
        logger.info(f"Random seed set to: {seed}")

    @property
    def root(self) -> Path:
        """Project root path."""
        return self._root_path

    @property
    def data_raw(self) -> Path:
        """Path to raw data directory."""
        return self._root_path / "data" / "raw"

    @property
    def data_processed(self) -> Path:
        """Path to processed data directory."""
        return self._root_path / "data" / "processed"

    @property
    def data_figures(self) -> Path:
        """Path to figures directory."""
        return self._root_path / "data" / "figures"

    @property
    def state_dir(self) -> Path:
        """Path to state directory."""
        return self._root_path / "state"

    @property
    def project_state_path(self) -> Path:
        """Path to the specific project state YAML file."""
        return self.state_dir / "projects" / "PROJ-490-the-effect-of-simulated-social-compariso.yaml"

    @property
    def seed(self) -> int:
        """Current random seed."""
        return self._seed

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any, save: bool = False) -> None:
        """Set a configuration value."""
        self._config[key] = value
        if save:
            self.save()

    def save(self) -> None:
        """Save current configuration to YAML file."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False)
        logger.info(f"Configuration saved to {self._config_path}")

    def update_seed(self, seed: int) -> None:
        """Update the random seed and re-seed generators."""
        self._seed = seed
        random.seed(seed)
        logger.info(f"Seed updated to: {seed}")

# Global config instance (lazy initialization)
_global_config: Optional[Config] = None

def get_config(seed: Optional[int] = None) -> Config:
    """
    Get or create the global configuration instance.
    
    Args:
        seed: Optional seed override. If provided, updates the global config.
    
    Returns:
        Config instance.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config(seed=seed)
    elif seed is not None:
        _global_config.update_seed(seed)
    
    return _global_config

def reset_config() -> None:
    """Reset the global configuration instance."""
    global _global_config
    _global_config = None
    logger.info("Global configuration reset.")

if __name__ == "__main__":
    # Test execution
    log_execution_start("config_test")
    
    cfg = get_config(seed=12345)
    
    print(f"Root: {cfg.root}")
    print(f"Data Raw: {cfg.data_raw}")
    print(f"Data Processed: {cfg.data_processed}")
    print(f"State Path: {cfg.project_state_path}")
    print(f"Seed: {cfg.seed}")
    
    # Verify directories exist
    assert cfg.data_raw.exists(), "Raw data dir missing"
    assert cfg.data_processed.exists(), "Processed data dir missing"
    assert cfg.project_state_path.parent.exists(), "State dir missing"
    
    print("Configuration check passed.")
    
    log_execution_end("config_test")