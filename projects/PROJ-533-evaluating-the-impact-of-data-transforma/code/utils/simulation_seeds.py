"""
Utilities for logging simulation seeds to ensure reproducibility.
Satisfies Constitution VII "alongside results" requirement.
"""
from pathlib import Path
from typing import Optional
import os

SEEDS_FILE_PATH = "results/simulation_seeds.txt"

def log_simulation_seed(run_id: str, seed: int = 42, output_dir: Optional[str] = None) -> str:
    """
    Logs a simulation seed to the central seeds log file.
    
    This function ensures the seed is recorded BEFORE the simulation loop executes,
    satisfying the precondition requirement for reproducibility (Constitution VII).
    
    Args:
        run_id: Unique identifier for the simulation run.
        seed: The random seed used for this run (default 42).
        output_dir: Optional override for the output directory. Defaults to 'results/'.
        
    Returns:
        The absolute path to the seeds file where the entry was logged.
        
    Raises:
        FileNotFoundError: If the results directory does not exist and cannot be created.
    """
    if output_dir is None:
        output_dir = "results"
    
    seeds_path = Path(output_dir)
    seeds_path.mkdir(parents=True, exist_ok=True)
    
    file_path = seeds_path / "simulation_seeds.txt"
    
    log_entry = f"RUN_ID={run_id} SEED={seed}\n"
    
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    return str(file_path)
