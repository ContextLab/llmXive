"""
Utility for logging simulation seeds to satisfy Constitution VII.
Ensures seeds are recorded alongside results for reproducibility.
"""
from pathlib import Path
from typing import Optional

def log_simulation_seed(
    run_id: str,
    seed: int,
    output_path: str = "results/simulation_seeds.txt"
) -> None:
    """
    Log a simulation run ID and its corresponding seed to a file.
    
    Format: RUN_ID=<id> SEED=<seed>
    
    This file is placed in results/ alongside specific simulation outputs
    to satisfy Constitution VII "alongside results" requirement.
    
    Args:
        run_id: Unique identifier for the simulation run
        seed: Random seed used for reproducibility
        output_path: Path to the seeds log file (default: results/simulation_seeds.txt)
    """
    log_path = Path(output_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_line = f"RUN_ID={run_id} SEED={seed}\n"
    
    with open(log_path, "a") as f:
        f.write(log_line)
