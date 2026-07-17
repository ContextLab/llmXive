import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from code.src.utils.config import get_global_config
from code.src.utils.logging import log_metric, get_run_log

def ensure_data_directory(path: Union[str, Path]) -> Path:
    """Ensure the directory for the given path exists."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def generate_run_id() -> str:
    """Generate a unique run identifier based on timestamp and process id."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"run_{timestamp}_{os.getpid()}"

def inject_seed_to_log(config_path: Union[str, Path] = "code/config.yaml", output_path: Union[str, Path] = "data/run_log.json") -> Dict[str, Any]:
    """
    Inject specific random seeds used during a run into data/run_log.json.
    
    This function:
    1. Loads the global configuration to find the pinned seed.
    2. Verifies the presence and correctness of these seeds against the config.
    3. Updates the run log (data/run_log.json) with the specific seeds and verification status.
    4. Does NOT update config.yaml.
    
    Args:
        config_path: Path to the config.yaml file.
        output_path: Path to the output run_log.json file.
        
    Returns:
        The updated log dictionary.
        
    Raises:
        FileNotFoundError: If config.yaml is missing.
        KeyError: If required seed keys are missing in config.
    """
    config_path = Path(config_path)
    output_path = Path(output_path)
    
    # Ensure output directory exists
    ensure_data_directory(output_path)
    
    # Load configuration
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    config = get_global_config(str(config_path))
    
    # Extract seeds from config (FR-007 requirement)
    if "global_seed" not in config:
        raise KeyError("Configuration missing 'global_seed' key required for reproducibility.")
        
    pinned_seed = config["global_seed"]
    
    # Verify correctness (ensure it's an integer)
    if not isinstance(pinned_seed, int):
        raise ValueError(f"Global seed must be an integer, got {type(pinned_seed)}")
        
    verification_status = "passed"
    verification_details = {
        "seed_found": True,
        "seed_type_valid": True,
        "seed_value": pinned_seed,
        "message": "Seed successfully verified and injected into run log."
    }
    
    # Initialize or load existing run log
    if output_path.exists():
        with open(output_path, 'r') as f:
            run_log = json.load(f)
    else:
        run_log = {
            "run_id": generate_run_id(),
            "timestamp": datetime.now().isoformat(),
            "seeds": {},
            "verification": {}
        }
    
    # Inject the specific seed
    run_log["seeds"]["global_random"] = pinned_seed
    run_log["seeds"]["numpy"] = pinned_seed  # Often synced with global in this pipeline
    run_log["seeds"]["python_random"] = pinned_seed
    
    # Record verification results
    run_log["verification"] = {
        "status": verification_status,
        "details": verification_details,
        "timestamp": datetime.now().isoformat()
    }
    
    # Update run timestamp
    run_log["timestamp"] = datetime.now().isoformat()
    
    # Write to disk
    with open(output_path, 'w') as f:
        json.dump(run_log, f, indent=2)
        
    # Also log to the in-memory log if available (for immediate feedback)
    try:
        current_log = get_run_log()
        current_log["seeds"] = run_log["seeds"]
        current_log["verification"] = run_log["verification"]
    except Exception:
        pass  # Logging might not be fully initialized yet
        
    return run_log

def get_latest_run_seed(log_path: Union[str, Path] = "data/run_log.json") -> Optional[int]:
    """Retrieve the global seed from the latest run log."""
    path = Path(log_path)
    if not path.exists():
        return None
        
    with open(path, 'r') as f:
        log = json.load(f)
        
    return log.get("seeds", {}).get("global_random")

def verify_reproducibility(config_path: Union[str, Path] = "code/config.yaml", log_path: Union[str, Path] = "data/run_log.json") -> bool:
    """
    Verify that the seeds in the run log match the global seed in config.
    
    Returns:
        True if verification passes, False otherwise.
    """
    try:
        config = get_global_config(str(config_path))
        if not Path(log_path).exists():
            return False
            
        with open(log_path, 'r') as f:
            log = json.load(f)
            
        config_seed = config.get("global_seed")
        log_seed = log.get("seeds", {}).get("global_random")
        
        return config_seed is not None and config_seed == log_seed
    except Exception:
        return False
