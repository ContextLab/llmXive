import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

LOG_DIR = "data/results"
LOG_FILE_NAME = "simulation.log"

def ensure_log_directory() -> str:
    """Ensure the log directory exists."""
    os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR

def log_simulation_run(
    N: int,
    rho: float,
    seed: int,
    duration: float,
    vif_max: float,
    config_path: Optional[str] = None,
    instance_id: Optional[str] = None
) -> None:
    """
    Append a single simulation run record to the JSON log file.
    
    Args:
        N: Sample size used in the simulation.
        rho: Target correlation coefficient used.
        seed: Random seed used for reproducibility.
        duration: Time taken for the simulation run in seconds.
        vif_max: Maximum VIF observed in the generated dataset.
        config_path: Optional path to the configuration file used.
        instance_id: Optional unique identifier for the dataset instance.
    """
    ensure_log_directory()
    log_path = os.path.join(LOG_DIR, LOG_FILE_NAME)
    
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "N": N,
        "rho": rho,
        "seed": seed,
        "duration": duration,
        "vif_max": vif_max
    }
    
    if config_path is not None:
        record["config_path"] = config_path
    if instance_id is not None:
        record["instance_id"] = instance_id
    
    # Append as a JSON Lines file (one JSON object per line)
    # This allows for easy streaming and avoids loading the whole file into memory
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
