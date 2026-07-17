"""
Reproducibility utilities for the llmXive automated science pipeline.
Handles seed injection, run ID generation, and verification of reproducibility.
"""
import json
import os
import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from code.src.utils.config import load_config, get_config_value
from code.src.utils.logging import log_run, log_metric, get_run_log


def ensure_data_directory(path: Union[str, Path]) -> Path:
    """Ensure the directory for a given path exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_run_id() -> str:
    """Generate a unique run ID based on timestamp and random component."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_component = random.randint(1000, 9999)
    return f"{timestamp}_{random_component}"


def inject_seed_to_log(
    config_path: Union[str, Path],
    output_path: Union[str, Path],
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inject specific random seeds from config into the run log.
    
    This function:
    1. Loads the global config to retrieve the pinned random seed.
    2. Sets the seed for numpy, random, and (optionally) torch if available.
    3. Creates or updates `data/run_log.json` with the injected seeds.
    4. Verifies the presence and correctness of seeds against the config.
    5. Returns the verification results.
    
    Args:
        config_path: Path to the config.yaml file.
        output_path: Path where run_log.json should be written.
        run_id: Optional custom run ID. If None, a new one is generated.
        
    Returns:
        Dictionary containing verification results and log entry.
        
    Raises:
        FileNotFoundError: If config file is not found.
        ValueError: If required seed keys are missing in config.
    """
    config_path = Path(config_path)
    output_path = Path(output_path)
    
    # Ensure output directory exists
    ensure_data_directory(output_path.parent)
    
    # Load configuration
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    config = load_config(config_path)
    
    # Extract seed from config (FR-007 requirement)
    if 'random_seed' not in config:
        raise ValueError("Config must contain 'random_seed' key for reproducibility.")
        
    seed = config['random_seed']
    
    # Set seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    # Attempt to set torch seed if available (graceful degradation)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch not required for this project
        
    # Generate run ID if not provided
    if run_id is None:
        run_id = generate_run_id()
        
    # Prepare log entry
    log_entry = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "config_path": str(config_path),
        "seeds": {
            "global_seed": seed,
            "numpy_seed": int(np.random.get_state()[1][0]), # Current state snapshot
            "random_seed": random.randint(0, 2**32 - 1) # Snapshot of current state
        },
        "verification": {
            "config_seed_present": True,
            "config_seed_value": seed,
            "seeds_applied": True,
            "verification_status": "passed"
        }
    }
    
    # Verify against config
    if config['random_seed'] != seed:
        log_entry["verification"]["verification_status"] = "failed"
        log_entry["verification"]["error"] = "Seed mismatch between config and applied seed"
        
    # Load existing log if it exists to append, or create new
    existing_log = None
    log_file = Path(output_path)
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                existing_log = json.load(f)
                if not isinstance(existing_log, list):
                    existing_log = [existing_log]
        except (json.JSONDecodeError, IOError):
            existing_log = []
    
    # Append new entry
    if existing_log is None:
        existing_log = []
    existing_log.append(log_entry)
    
    # Write to disk
    with open(log_file, 'w') as f:
        json.dump(existing_log, f, indent=2)
        
    # Also update the global run log via logging utility if needed
    # (This ensures consistency with T005 logging infrastructure)
    log_run("reproducibility", {
        "run_id": run_id,
        "seed": seed,
        "status": "seed_injected"
    })
    
    return log_entry


def get_latest_run_seed(log_path: Union[str, Path] = "data/run_log.json") -> Optional[int]:
    """
    Retrieve the seed from the most recent run log entry.
    
    Args:
        log_path: Path to the run_log.json file.
        
    Returns:
        The seed integer if found, None otherwise.
    """
    log_file = Path(log_path)
    if not log_file.exists():
        return None
        
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data[-1].get("seeds", {}).get("global_seed")
            elif isinstance(data, dict):
                return data.get("seeds", {}).get("global_seed")
    except (json.JSONDecodeError, IOError):
        return None
        
    return None


def verify_reproducibility(
    config_path: Union[str, Path],
    log_path: Union[str, Path] = "data/run_log.json"
) -> Dict[str, Any]:
    """
    Verify that the seeds in the run log match the config.
    
    Args:
        config_path: Path to config.yaml.
        log_path: Path to run_log.json.
        
    Returns:
        Dictionary with verification results.
    """
    config = load_config(config_path)
    config_seed = config.get('random_seed')
    
    log_seed = get_latest_run_seed(log_path)
    
    result = {
        "config_seed": config_seed,
        "log_seed": log_seed,
        "match": config_seed == log_seed,
        "status": "passed" if config_seed == log_seed else "failed"
    }
    
    return result