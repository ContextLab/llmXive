import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

LOG_FILE_PATH = "data/results/simulation.log"

def ensure_log_directory():
    """Ensure the directory for the log file exists."""
    dir_path = os.path.dirname(LOG_FILE_PATH)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

def log_simulation_run(
    N: int,
    rho: float,
    seed: int,
    duration: float,
    vif_max: float,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Append a JSON log entry for a simulation run to data/results/simulation.log.

    Args:
        N: Sample size used in the simulation.
        rho: Target correlation coefficient.
        seed: Random seed used for reproducibility.
        duration: Duration of the simulation run in seconds.
        vif_max: Maximum Variance Inflation Factor observed.
        metadata: Optional dictionary of additional fields to include.
    """
    ensure_log_directory()

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "N": N,
        "rho": rho,
        "seed": seed,
        "duration": duration,
        "vif_max": vif_max
    }

    if metadata:
        entry.update(metadata)

    with open(LOG_FILE_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
