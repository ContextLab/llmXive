import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List
import numpy as np
import logging

SEED = 42

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent

def get_code_root() -> Path:
    """Get the code root directory."""
    return get_project_root() / "code"

def get_data_dir() -> Path:
    """Get the data directory."""
    return get_project_root() / "data"

def get_raw_data_dir() -> Path:
    """Get the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_data_dir() -> Path:
    """Get the processed data directory."""
    return get_data_dir() / "processed"

def get_results_dir() -> Path:
    """Get the results directory."""
    return get_data_dir() / "results"

def get_logs_dir() -> Path:
    """Get the logs directory."""
    return get_project_root() / "logs"

def get_figures_dir() -> Path:
    """Get the figures directory."""
    return get_data_dir() / "figures"

def get_contracts_dir() -> Path:
    """Get the contracts directory."""
    return get_project_root() / "contracts"

def get_specs_dir() -> Path:
    """Get the specs directory."""
    return get_project_root() / "specs"

def set_global_seed(seed: int = SEED) -> None:
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_results_dir(),
        get_logs_dir(),
        get_figures_dir(),
        get_contracts_dir(),
        get_specs_dir()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config() -> Dict[str, Any]:
    """Get configuration dictionary."""
    return {
        "seed": SEED,
        "paths": {
            "project_root": str(get_project_root()),
            "data_dir": str(get_data_dir()),
            "raw_data_dir": str(get_raw_data_dir()),
            "processed_data_dir": str(get_processed_data_dir()),
            "results_dir": str(get_results_dir()),
            "logs_dir": str(get_logs_dir()),
            "figures_dir": str(get_figures_dir()),
            "contracts_dir": str(get_contracts_dir()),
            "specs_dir": str(get_specs_dir())
        }
    }

def get_path(key: str) -> Path:
    """Get path by key."""
    paths = {
        "project_root": get_project_root(),
        "data_dir": get_data_dir(),
        "raw_data_dir": get_raw_data_dir(),
        "processed_data_dir": get_processed_data_dir(),
        "results_dir": get_results_dir(),
        "logs_dir": get_logs_dir(),
        "figures_dir": get_figures_dir(),
        "contracts_dir": get_contracts_dir(),
        "specs_dir": get_specs_dir()
    }
    if key not in paths:
        raise KeyError(f"Unknown path key: {key}")
    return paths[key]

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    log_dir = get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if log_file is None:
        log_file = "pipeline.log"
    
    log_path = log_dir / log_file
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
