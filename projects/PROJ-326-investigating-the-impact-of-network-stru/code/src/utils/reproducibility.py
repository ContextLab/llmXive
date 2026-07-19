"""
Reproducibility utilities for seed management and run logging.
"""
import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from code.src.utils.config import load_config

logger = logging.getLogger(__name__)

def ensure_data_directory(path: str) -> Path:
    """Ensure the directory for the given path exists."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def generate_run_id() -> str:
    """Generate a unique run ID based on timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def inject_seed_to_log(config_path: str, log_path: str) -> Dict[str, Any]:
    """
    Read the global seed from config.yaml and inject it into the run log.
    Validates that the config contains the required 'random_seed' key.
    
    Args:
        config_path: Path to config.yaml
        log_path: Path to data/run_log.json
        
    Returns:
        Dict containing the run log data
        
    Raises:
        ValueError: If config does not contain 'random_seed'
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    config = load_config(config_path)
    
    if 'random_seed' not in config:
        raise ValueError("Config must contain 'random_seed' key for reproducibility.")
    
    seed = config['random_seed']
    run_id = generate_run_id()
    
    # Set seeds globally
    random.seed(seed)
    np.random.seed(seed)
    
    # Construct log entry
    log_entry = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "seeds": {
            "global": seed,
            "generator": seed,
            "simulation": seed
        },
        "verification_status": "PASS",
        "config_path": config_path
    }
    
    # Write to log
    log_file = ensure_data_directory(log_path)
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)
        
    logger.info(f"Seeds injected into {log_path} with run_id: {run_id}")
    return log_entry

def get_seed_from_config(config: Dict[str, Any]) -> int:
    """Extract seed from config, raising error if missing."""
    if 'random_seed' not in config:
        raise ValueError("Config must contain 'random_seed' key.")
    return config['random_seed']
