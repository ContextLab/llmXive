import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

_config: Dict[str, Any] = {}
_logger: Optional[logging.Logger] = None

def get_default_config() -> Dict[str, Any]:
    """
    Returns the default configuration dictionary.
    """
    return {
        "seed": 42,
        "device": "cpu",
        "data_dirs": {
            "raw": "data/raw",
            "processed": "data/processed",
            "assets": "data/assets"
        },
        "code_dir": "code",
        "artifacts_dir": "artifacts",
        "tests_dir": "tests",
        "log_dir": "artifacts/logs",
        "weight_dir": "artifacts/weights",
        "figure_dir": "artifacts/figures",
        "max_memory_gb": 4.0,
        "batch_size": 32,
        "learning_rate": 0.001,
        "epochs": 100,
        "early_stopping_patience": 5,
        "qm9_split": "train",
        "reaction_type_mapping": {
            "EC 1.x.x.x": "oxidation_reduction",
            "EC 2.x.x.x": "transferase",
            "EC 3.x.x.x": "hydrolase",
            "EC 4.x.x.x": "lyase",
            "EC 5.x.x.x": "isomerase",
            "EC 6.x.x.x": "ligase"
        }
    }

def get_config() -> Dict[str, Any]:
    """
    Returns the current configuration, merging defaults with any overrides.
    """
    global _config
    if not _config:
        _config = get_default_config()
    return _config

def set_config(new_config: Dict[str, Any]) -> None:
    """
    Updates the global configuration with new values.
    """
    global _config
    _config.update(new_config)

def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for reproducibility.
    """
    if seed is None:
        seed = get_config().get("seed", 42)
    
    random.seed(seed)
    np.random.seed(seed)
    # Note: torch and other libraries would be seeded here if imported

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Ensures all directories defined in the configuration exist.
    Creates them if they don't.
    """
    if config is None:
        config = get_config()
    
    dirs_to_create = []
    
    # Add data directories
    if "data_dirs" in config:
        for dir_key, dir_path in config["data_dirs"].items():
            dirs_to_create.append(dir_path)
    
    # Add other standard directories
    standard_dirs = [
        config.get("code_dir", "code"),
        config.get("artifacts_dir", "artifacts"),
        config.get("tests_dir", "tests"),
        config.get("log_dir", "artifacts/logs"),
        config.get("weight_dir", "artifacts/weights"),
        config.get("figure_dir", "artifacts/figures")
    ]
    
    for dir_path in standard_dirs:
        if dir_path and dir_path not in dirs_to_create:
            dirs_to_create.append(dir_path)
    
    for dir_path in dirs_to_create:
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            if _logger:
                _logger.info(f"Created directory: {dir_path}")

def init_config_logging() -> logging.Logger:
    """
    Initializes the config module logger.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("config")
        _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
    return _logger
