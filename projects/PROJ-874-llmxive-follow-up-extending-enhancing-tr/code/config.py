"""
Configuration management for llmXive project.
Handles seed management, dataset paths, state updates, and centralized error handling/logging.
"""
import os
import json
import logging
import random
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import sys

# --- Custom Exceptions for Centralized Error Handling ---
class LlmXiveError(Exception):
    """Base exception for all llmXive specific errors."""
    pass

class ConfigError(LlmXiveError):
    """Raised when configuration loading or validation fails."""
    pass

class DatasetNotFoundError(LlmXiveError):
    """Raised when a required dataset file or directory is missing."""
    pass

class ValidationError(LlmXiveError):
    """Raised when data or state validation fails."""
    pass

class StateUpdateError(LlmXiveError):
    """Raised when updating the project state file fails."""
    pass

# --- Logging Infrastructure ---
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configures the root logger with standardized formatting and handlers.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, only console output is used.
    
    Returns:
        The configured root logger.
    
    Raises:
        ConfigError: If log_level is invalid or file cannot be opened.
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level.upper() not in valid_levels:
        raise ConfigError(f"Invalid log level: {log_level}. Must be one of {valid_levels}")
    
    log_level_int = getattr(logging, log_level.upper())
    logger = logging.getLogger()
    logger.setLevel(log_level_int)
    
    # Clear existing handlers to avoid duplicates in some environments
    logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level_int)
    logger.addHandler(console_handler)
    
    # File Handler (Optional)
    if log_file:
        try:
            # Ensure directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level_int)
            logger.addHandler(file_handler)
        except IOError as e:
            raise ConfigError(f"Failed to open log file '{log_file}': {e}")
    
    return logger

# --- Configuration Class ---
class Config:
    """
    Central configuration manager. Loads settings from a JSON file or environment variables.
    Handles validation and provides typed access to configuration values.
    """
    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path or "config/settings.json"
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Loads configuration from file or sets defaults."""
        config_file = Path(self._config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logging.info(f"Configuration loaded from {config_file}")
            except json.JSONDecodeError as e:
                raise ConfigError(f"Invalid JSON in config file {config_file}: {e}")
            except IOError as e:
                raise ConfigError(f"Failed to read config file {config_file}: {e}")
        else:
            logging.warning(f"Config file {config_file} not found. Using defaults.")
            self._config = self._get_defaults()
        
        self._validate_config()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Returns default configuration values."""
        return {
            "seed": 42,
            "datasets": {
                "narrlv": "narrlv_dataset",
                "vbench": "vbench_dataset"
            },
            "paths": {
                "raw": "data/raw",
                "processed": "data/processed",
                "results": "data/results"
            },
            "memory_limit_mb": 6144,
            "max_workers": 2,
            "flow_model": "raft-small",
            "flow_precision": "fp32" # Default to fp32 for CPU safety, overridden by benchmark if needed
        }
    
    def _validate_config(self) -> None:
        """Validates critical configuration values."""
        if not isinstance(self._config.get("seed"), int):
            raise ConfigError("Config 'seed' must be an integer.")
        
        if not isinstance(self._config.get("memory_limit_mb"), int) or self._config["memory_limit_mb"] <= 0:
            raise ConfigError("Config 'memory_limit_mb' must be a positive integer.")
        
        # Validate paths
        for key in ["raw", "processed", "results"]:
            if key not in self._config.get("paths", {}):
                raise ConfigError(f"Config 'paths.{key}' is missing.")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Safely gets a configuration value."""
        return self._config.get(key, default)
    
    def update(self, key: str, value: Any) -> None:
        """Updates a configuration value and persists it if possible."""
        self._config[key] = value
        # Attempt to persist
        try:
            Path(self._config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4)
        except IOError:
            logging.warning("Could not persist config update to disk.")

# --- Global Config Instance ---
_global_config: Optional[Config] = None

def get_config() -> Config:
    """Returns the singleton global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

# --- Seed Management ---
def get_seed() -> int:
    """Retrieves the random seed from configuration."""
    return get_config().get("seed", 42)

def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for reproducibility.
    Updates global config and seeds random, numpy (if available), and hashlib.
    """
    if seed is None:
        seed = get_seed()
    
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    # Update config
    config = get_config()
    config.update("seed", seed)
    logging.info(f"Random seed set to {seed}")

# --- Dataset Paths ---
def get_dataset_paths() -> Dict[str, str]:
    """Retrieves the configured dataset names/paths."""
    return get_config().get("datasets", {})

def get_required_files() -> List[str]:
    """
    Returns a list of required dataset identifiers that must be present
    before generation can proceed.
    """
    # Based on tasks.md: NarrLV and VBench
    return ["narrlv", "vbench"]

# --- Directory Paths ---
def get_processed_dir() -> Path:
    """Returns the path to the processed data directory."""
    base = get_config().get("paths", {}).get("processed", "data/processed")
    return Path(base)

def get_results_dir() -> Path:
    """Returns the path to the results directory."""
    base = get_config().get("paths", {}).get("results", "data/results")
    return Path(base)

def get_raw_dir() -> Path:
    """Returns the path to the raw data directory."""
    base = get_config().get("paths", {}).get("raw", "data/raw")
    return Path(base)

# --- State Management ---
_state_file = Path("data/state.json")

def get_state() -> Dict[str, Any]:
    """Loads the current project state from disk."""
    if not _state_file.exists():
        return {"tasks_completed": [], "last_run": None}
    
    try:
        with open(_state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to load state file: {e}")
        return {"tasks_completed": [], "last_run": None}

def update_state(task_id: str, status: str = "completed", details: Optional[Dict] = None) -> None:
    """
    Updates the project state file with the completion status of a task.
    
    Args:
        task_id: The ID of the task (e.g., "T008").
        status: The status string (e.g., "completed", "failed").
        details: Optional additional details to store.
    
    Raises:
        StateUpdateError: If the state file cannot be written.
    """
    state = get_state()
    state["tasks_completed"].append({
        "id": task_id,
        "status": status,
        "details": details,
        "timestamp": str(logging.Formatter().formatTime(logging.LogRecord("", "", "", "", "", "", ""))) # Simplified timestamp
    })
    state["last_run"] = str(logging.Formatter().formatTime(logging.LogRecord("", "", "", "", "", "", "")))
    
    try:
        _state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(_state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)
    except IOError as e:
        raise StateUpdateError(f"Failed to update state file: {e}")

# --- Resource Limits ---
def get_memory_limit() -> int:
    """Returns the configured memory limit in MB."""
    return get_config().get("memory_limit_mb", 6144)

def get_max_workers() -> int:
    """Returns the configured maximum number of worker processes."""
    return get_config().get("max_workers", 2)

def get_flow_model() -> str:
    """Returns the configured flow model name."""
    return get_config().get("flow_model", "raft-small")

def get_flow_precision() -> str:
    """Returns the configured flow model precision (fp16/fp32)."""
    return get_config().get("flow_precision", "fp32")

# --- Utility Functions ---
def calculate_hash(data: str) -> str:
    """Calculates the SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def validate_path_exists(path: str, description: str = "path") -> None:
    """
    Validates that a given path exists.
    
    Args:
        path: The path to check.
        description: A human-readable description of what the path is.
    
    Raises:
        DatasetNotFoundError: If the path does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise DatasetNotFoundError(f"Required {description} not found at: {path}")