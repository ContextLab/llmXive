import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

LOG_FILE_PATH = "data/results/simulation.log"

def ensure_log_directory() -> Path:
    """
    Ensures the directory for the log file exists.
    Creates it if it doesn't.
    """
    log_path = Path(LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path.parent

def log_simulation_run(
    N: int,
    rho: float,
    seed: int,
    duration: float,
    vif_max: float,
    output_path: Optional[str] = None
) -> None:
    """
    Appends a single JSON line to the simulation log file.

    Args:
        N: Sample size used in the simulation.
        rho: Target correlation coefficient used.
        seed: Random seed used for reproducibility.
        duration: Duration of the run in seconds.
        vif_max: Maximum VIF score observed in the generated data.
        output_path: Optional path override for the log file.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "N": N,
        "rho": rho,
        "seed": seed,
        "duration": duration,
        "vif_max": vif_max
    }

    path_to_use = output_path if output_path else LOG_FILE_PATH
    ensure_log_directory()

    with open(path_to_use, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def get_log_entries(output_path: Optional[str] = None) -> list:
    """
    Reads and parses all JSON log entries from the log file.

    Returns:
        A list of dictionaries, each representing one simulation run.
    """
    path_to_use = output_path if output_path else LOG_FILE_PATH
    
    if not os.path.exists(path_to_use):
        return []

    entries = []
    with open(path_to_use, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries
