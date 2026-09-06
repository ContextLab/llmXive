import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

def ensure_log_directory(log_dir: str = "data/results") -> Path:
    """
    Ensure the log directory exists.
    
    Args:
        log_dir: Path to the log directory.
        
    Returns:
        Path object for the log directory.
    """
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def log_simulation_run(
    N: int,
    rho: float,
    seed: int,
    duration: float,
    vif_max: float,
    regeneration_attempts: int,
    regeneration_reason: str,
    log_file: str = "data/results/simulation.log"
) -> None:
    """
    Log simulation run parameters to a JSON-lines file.
    
    This function appends a single JSON record to the specified log file.
    The record contains all relevant simulation parameters and runtime metrics.
    
    Args:
        N: Sample size used in the simulation.
        rho: Target correlation coefficient used in the simulation.
        seed: Random seed used for reproducibility.
        duration: Execution time in seconds.
        vif_max: Maximum VIF score observed in the generated dataset.
        regeneration_attempts: Number of attempts made to generate a valid dataset.
        regeneration_reason: Reason for any regeneration attempts (e.g., "not_positive_semidefinite").
        log_file: Path to the log file.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "N": N,
        "rho": rho,
        "seed": seed,
        "duration": duration,
        "vif_max": vif_max,
        "regeneration_attempts": regeneration_attempts,
        "regeneration_reason": regeneration_reason
    }
    
    log_path = Path(log_file)
    ensure_log_directory(str(log_path.parent))
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

def get_log_entries(log_file: str = "data/results/simulation.log") -> list:
    """
    Read all log entries from the simulation log file.
    
    Args:
        log_file: Path to the log file.
        
    Returns:
        List of dictionaries, each representing a log entry.
    """
    entries = []
    log_path = Path(log_file)
    
    if not log_path.exists():
        return entries
        
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
                    
    return entries