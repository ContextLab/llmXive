"""
Demo script to initialize the simulation seeds log file.

This script is designed to be run at the start of a simulation batch to
ensure the `results/simulation_seeds.txt` file exists and is ready to receive
entries. It does not run a simulation itself, but prepares the logging artifact
required by Constitution VII.
"""
import os
from pathlib import Path
from code.utils.simulation_seeds import log_simulation_seed

def main():
    """
    Initializes the simulation seeds log file.
    
    This is a placeholder run to ensure the file exists and the path is valid.
    Real seeds will be appended by `code/simulate_null.py` and `code/simulate_power.py`
    before their respective simulation loops.
    """
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Log a "initialization" entry to mark the file creation
    # In a real pipeline, this would be done by the simulation runner
    init_run_id = "PIPELINE_INIT"
    
    try:
        path = log_simulation_seed(init_run_id, seed=42)
        print(f"Successfully initialized seed log at: {path}")
        print(f"Content: RUN_ID={init_run_id} SEED=42")
    except Exception as e:
        print(f"Failed to initialize seed log: {e}")
        raise

if __name__ == "__main__":
    main()