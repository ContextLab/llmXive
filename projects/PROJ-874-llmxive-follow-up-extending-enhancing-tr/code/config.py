"""
Configuration management for llmXive Follow-up project.

Provides:
- Seed management for reproducibility
- Dataset path resolution
- State update logic for tracking pipeline progress
- Environment variable overrides
"""

import os
import json
import logging
import random
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default configuration
DEFAULT_CONFIG = {
    "seed": 42,
    "dataset_names": ["NarrLV", "VBench"],
    "raw_data_dir": "data/raw",
    "processed_data_dir": "data/processed",
    "results_dir": "data/results",
    "log_level": "INFO",
    "max_workers": 2,  # CPU constraint
    "memory_limit_gb": 6.0,
    "flow_model": "raft-small",
    "flow_precision": "fp32",  # Fallback from fp16 if needed
}

# Required files for dataset validation (checksums)
REQUIRED_FILES = {
    "NarrLV": [
        "narrlv_train.json",
        "narrlv_val.json",
        "narrlv_test.json",
    ],
    "VBench": [
        "vbench_train.json",
        "vbench_val.json",
        "vbench_test.json",
    ],
}

# Logging configuration
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure and return the project logger."""
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    logger = logging.getLogger("llmxive")
    logger.setLevel(log_level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

logger = setup_logging()

class Config:
    """
    Central configuration manager.
    
    Handles:
    - Seed setting for reproducibility
    - Dataset path resolution
    - State tracking for pipeline progress
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration with optional override file."""
        self._config = DEFAULT_CONFIG.copy()
        self._state_file = PROJECT_ROOT / "data" / "pipeline_state.json"
        
        if config_path and config_path.exists():
            self._load_from_file(config_path)
        
        # Override from environment variables
        self._load_from_env()
        
        # Initialize state
        self._load_state()
    
    def _load_from_file(self, path: Path) -> None:
        """Load configuration from a JSON file."""
        try:
            with open(path, "r") as f:
                override_config = json.load(f)
            self._config.update(override_config)
            logger.info(f"Loaded config from {path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {path}: {e}")
    
    def _load_from_env(self) -> None:
        """Override config with environment variables."""
        env_mapping = {
            "LLMXIVE_SEED": "seed",
            "LLMXIVE_DATASET_NAMES": "dataset_names",
            "LLMXIVE_LOG_LEVEL": "log_level",
            "LLMXIVE_MAX_WORKERS": "max_workers",
            "LLMXIVE_MEMORY_LIMIT_GB": "memory_limit_gb",
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                if config_key in ["seed", "max_workers"]:
                    try:
                        self._config[config_key] = int(value)
                    except ValueError:
                        logger.warning(f"Invalid integer for {env_var}: {value}")
                elif config_key == "memory_limit_gb":
                    try:
                        self._config[config_key] = float(value)
                    except ValueError:
                        logger.warning(f"Invalid float for {env_var}: {value}")
                elif config_key == "dataset_names":
                    self._config[config_key] = value.split(",")
                else:
                    self._config[config_key] = value
        
        # Update logger level if changed
        if "log_level" in self._config:
            setup_logging(self._config["log_level"])
    
    def _load_state(self) -> None:
        """Load pipeline state from disk."""
        if self._state_file.exists():
            try:
                with open(self._state_file, "r") as f:
                    self._state = json.load(f)
                logger.debug(f"Loaded state from {self._state_file}")
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
                self._state = {}
        else:
            self._state = {}
    
    def save_state(self) -> None:
        """Save current pipeline state to disk."""
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._state_file, "w") as f:
            json.dump(self._state, f, indent=2)
        logger.debug(f"Saved state to {self._state_file}")
    
    def update_state(self, key: str, value: Any) -> None:
        """Update a single state value and persist."""
        self._state[key] = value
        self.save_state()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self._state.get(key, default)
    
    def set_seed(self, seed: Optional[int] = None) -> int:
        """Set random seed for reproducibility. Returns the seed used."""
        if seed is None:
            seed = self._config["seed"]
        
        self._config["seed"] = seed
        random.seed(seed)
        
        # Set numpy seed if available
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass
        
        logger.info(f"Random seed set to {seed}")
        return seed
    
    def get_seed(self) -> int:
        """Get the current seed value."""
        return self._config["seed"]
    
    def get_dataset_paths(self, dataset_name: Optional[str] = None) -> Dict[str, Path]:
        """
        Resolve dataset paths.
        
        Args:
            dataset_name: Optional specific dataset name. If None, returns all.
        
        Returns:
            Dict mapping dataset name to its raw data directory path.
        """
        if dataset_name:
            datasets = [dataset_name]
        else:
            datasets = self._config["dataset_names"]
        
        paths = {}
        for name in datasets:
            raw_dir = PROJECT_ROOT / self._config["raw_data_dir"] / name
            paths[name] = raw_dir
        
        return paths
    
    def get_processed_dir(self) -> Path:
        """Get the processed data directory."""
        return PROJECT_ROOT / self._config["processed_data_dir"]
    
    def get_results_dir(self) -> Path:
        """Get the results directory."""
        return PROJECT_ROOT / self._config["results_dir"]
    
    def get_required_files(self, dataset_name: str) -> List[str]:
        """Get list of required files for a dataset."""
        return REQUIRED_FILES.get(dataset_name, [])
    
    def get_config(self) -> Dict[str, Any]:
        """Get full configuration dictionary."""
        return self._config.copy()
    
    def get_memory_limit(self) -> float:
        """Get memory limit in GB."""
        return self._config["memory_limit_gb"]
    
    def get_max_workers(self) -> int:
        """Get maximum worker count."""
        return self._config["max_workers"]
    
    def get_flow_model(self) -> str:
        """Get flow model name."""
        return self._config["flow_model"]
    
    def get_flow_precision(self) -> str:
        """Get flow precision setting."""
        return self._config["flow_precision"]

# Global config instance
config = Config()

# Convenience functions for importing in other modules
def get_seed() -> int:
    return config.get_seed()

def set_seed(seed: int) -> int:
    return config.set_seed(seed)

def get_dataset_paths(dataset_name: Optional[str] = None) -> Dict[str, Path]:
    return config.get_dataset_paths(dataset_name)

def get_required_files(dataset_name: str) -> List[str]:
    return config.get_required_files(dataset_name)

def get_processed_dir() -> Path:
    return config.get_processed_dir()

def get_results_dir() -> Path:
    return config.get_results_dir()

def update_state(key: str, value: Any) -> None:
    config.update_state(key, value)

def get_state(key: str, default: Any = None) -> Any:
    return config.get_state(key, default)

def get_memory_limit() -> float:
    return config.get_memory_limit()

def get_max_workers() -> int:
    return config.get_max_workers()

def get_flow_model() -> str:
    return config.get_flow_model()

def get_flow_precision() -> str:
    return config.get_flow_precision()

def get_config() -> Dict[str, Any]:
    return config.get_config()