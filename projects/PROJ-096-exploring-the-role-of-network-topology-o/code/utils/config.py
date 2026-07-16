import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Global Configuration Defaults
DEFAULT_GLOBAL_SEED = 42
DEFAULT_T_EVAL_START = 0.0
DEFAULT_T_EVAL_STOP = 100.0
DEFAULT_T_EVAL_NUM = 10000

# Configuration File Path relative to project root
CONFIG_FILE_NAME = "config.json"

_global_config: Dict[str, Any] = {}
_initialized: bool = False

def init_config(project_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize the global configuration.
    Loads from a JSON file if it exists, otherwise sets up defaults.
    Ensures deterministic seeds and t_eval settings are established.
    """
    global _global_config, _initialized
    
    if _initialized:
        return _global_config

    if project_root is None:
        # Default to current working directory if not specified
        project_root = os.getcwd()
    
    config_path = Path(project_root) / CONFIG_FILE_NAME

    if config_path.exists():
        with open(config_path, 'r') as f:
            _global_config = json.load(f)
    else:
        # Initialize with deterministic defaults
        _global_config = {
            "seed": DEFAULT_GLOBAL_SEED,
            "t_eval": {
                "start": DEFAULT_T_EVAL_START,
                "stop": DEFAULT_T_EVAL_STOP,
                "num": DEFAULT_T_EVAL_NUM
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        # Save default config for reproducibility
        with open(config_path, 'w') as f:
            json.dump(_global_config, f, indent=4)

    _initialized = True
    return _global_config

def get_config() -> Dict[str, Any]:
    """
    Retrieve the current global configuration.
    Raises RuntimeError if not initialized.
    """
    if not _initialized:
        # Attempt to auto-init with default root
        init_config()
    return _global_config

def set_config(key: str, value: Any) -> None:
    """
    Update a specific configuration value.
    """
    if not _initialized:
        init_config()
    _global_config[key] = value

def get_seed() -> int:
    """
    Retrieve the global random seed for reproducibility.
    """
    config = get_config()
    return config.get("seed", DEFAULT_GLOBAL_SEED)

def apply_global_seed() -> None:
    """
    Apply the global seed to numpy and random modules.
    This must be called before any random number generation in the pipeline.
    """
    import numpy as np
    import random
    
    seed = get_seed()
    np.random.seed(seed)
    random.seed(seed)

def get_t_eval() -> tuple:
    """
    Retrieve the time evaluation settings for scipy.integrate.odeint.
    Returns a tuple (t_eval_array, start, stop, num).
    """
    config = get_config()
    t_cfg = config.get("t_eval", {})
    
    start = t_cfg.get("start", DEFAULT_T_EVAL_START)
    stop = t_cfg.get("stop", DEFAULT_T_EVAL_STOP)
    num = t_cfg.get("num", DEFAULT_T_EVAL_NUM)
    
    import numpy as np
    t_eval = np.linspace(start, stop, num)
    
    return t_eval, start, stop, num

def update_t_eval(start: Optional[float] = None, stop: Optional[float] = None, num: Optional[int] = None) -> None:
    """
    Update the t_eval settings in the global configuration.
    """
    if not _initialized:
        init_config()
    
    config = get_config()
    if "t_eval" not in config:
        config["t_eval"] = {}
    
    if start is not None:
        config["t_eval"]["start"] = start
    if stop is not None:
        config["t_eval"]["stop"] = stop
    if num is not None:
        config["t_eval"]["num"] = num
    
    # Persist changes
    project_root = os.getcwd()
    config_path = Path(project_root) / CONFIG_FILE_NAME
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)