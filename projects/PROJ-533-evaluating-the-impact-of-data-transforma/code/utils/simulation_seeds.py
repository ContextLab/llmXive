"""
Simulation seeds logging utility.

Provides functionality to log simulation seeds to a dedicated file
for reproducibility and audit purposes.
"""
from pathlib import Path
from typing import Optional
import os

# Path to the simulation seeds log file
SEEDS_LOG_PATH = Path("results/simulation_seeds.txt")

def log_simulation_seed(run_id: str, seed: int, file_path: Optional[Path] = None) -> None:
    """
    Log a simulation seed to the designated log file.
    
    Args:
        run_id: Unique identifier for the simulation run
        seed: Random seed value used for the simulation
        file_path: Optional custom path for the log file (defaults to SEEDS_LOG_PATH)
    
    Raises:
        FileNotFoundError: If the results directory doesn't exist
        PermissionError: If unable to write to the file
    """
    if file_path is None:
        file_path = SEEDS_LOG_PATH
    
    # Ensure the directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format the log entry
    log_entry = f"RUN_ID={run_id} SEED={seed}\n"
    
    # Append to the file
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)