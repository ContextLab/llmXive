import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import hashlib

from simulation.config import SimulationConfig

LOG_FILE_PATH = "data/results/simulation.log"

def ensure_log_directory():
    """Ensure the directory for the log file exists."""
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

def log_simulation_run(
    N: int,
    rho: float,
    seed: int,
    duration: float,
    vif_max: float,
    regeneration_attempts: int,
    regeneration_reason: Optional[str] = None,
) -> None:
    """
    Log a single simulation run to data/results/simulation.log in JSON format (one JSON object per line).

    Args:
        N: Sample size.
        rho: Target correlation coefficient.
        seed: Random seed used for generation.
        duration: Duration of the run in seconds.
        vif_max: Maximum VIF score observed.
        regeneration_attempts: Number of regeneration attempts (int).
        regeneration_reason: Reason for regeneration if any ("PSD_failure", "VIF_limit", "rank_deficient").
    """
    ensure_log_directory()

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "N": N,
        "rho": rho,
        "seed": seed,
        "duration": duration,
        "vif_max": vif_max,
        "regeneration_attempts": regeneration_attempts,
        "regeneration_reason": regeneration_reason,
    }

    # Append as a single JSON line
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def get_log_entries() -> list:
    """
    Read and parse all entries from the simulation log file.

    Returns:
        List of dicts, each representing one log entry.
    """
    if not os.path.exists(LOG_FILE_PATH):
        return []

    entries = []
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
    return entries

def compute_log_checksum() -> str:
    """
    Compute SHA-256 checksum of the simulation log file.

    Returns:
        Hex digest of the SHA-256 hash.
    """
    if not os.path.exists(LOG_FILE_PATH):
        return ""

    sha256_hash = hashlib.sha256()
    with open(LOG_FILE_PATH, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
