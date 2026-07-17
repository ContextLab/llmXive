import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from code.src.utils.logging import log_metric, log_run

logger = None # Initialize in log module or pass context

def ensure_data_directory(file_path: Union[str, Path]) -> Path:
    """
    Ensure the directory for a given file path exists.
    Returns the Path object.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def generate_run_id() -> str:
    """
    Generate a unique run ID based on timestamp and random suffix.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = random.randint(1000, 9999)
    return f"run_{timestamp}_{suffix}"

def inject_seed_to_log(seed: int, log_path: Optional[Path] = None) -> None:
    """
    Inject the random seed used for the run into the log file.
    If log_path is not provided, it attempts to find the latest run log.
    """
    if log_path is None:
        # Default location
        log_path = Path("data/run_log.json")
    
    ensure_data_directory(log_path)
    
    seed_data = {
        "seed": seed,
        "injected_at": datetime.now().isoformat()
    }
    
    # Load existing log if exists
    log_data = {}
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            log_data = {}
    
    # Append seed info
    if "seeds" not in log_data:
        log_data["seeds"] = []
    log_data["seeds"].append(seed_data)
    
    # Also set global numpy and random seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def get_latest_run_seed(log_path: Optional[Path] = None) -> Optional[int]:
    """
    Retrieve the seed from the most recent run in the log.
    """
    if log_path is None:
        log_path = Path("data/run_log.json")
    
    if not log_path.exists():
        return None
    
    try:
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        if "seeds" in log_data and len(log_data["seeds"]) > 0:
            return log_data["seeds"][-1]["seed"]
    except (json.JSONDecodeError, IOError, IndexError):
        pass
    
    return None

def verify_reproducibility(seed: int, results_path: Path) -> bool:
    """
    Verify that a run with a given seed produces consistent results.
    This is a placeholder for a more complex verification logic.
    """
    # In a real scenario, we would re-run the simulation with the seed
    # and compare checksums or key metrics.
    # For now, we just check if the seed is in the log.
    if get_latest_run_seed() == seed:
        return True
    return False
