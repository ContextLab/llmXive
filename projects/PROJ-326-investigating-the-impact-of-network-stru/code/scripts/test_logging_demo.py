"""
Demo script to verify logging infrastructure (T005) works end-to-end.
Writes a real log entry to data/run_log.json.
"""
import sys
import os
from pathlib import Path

# Ensure we can import the project modules
# Assuming script is run from project root or code/
# We add the project root to path if needed
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.utils.logging import log_run, log_metric, get_run_log

def main():
    print("Starting logging infrastructure demo...")
    
    # Simulate a run
    run_seed = 12345
    run_params = {
        "topology": "er",
        "n_nodes": 100,
        "p_edge": 0.05,
        "simulation_steps": 50
    }
    run_metrics = {
        "duration_seconds": 1.5,
        "memory_mb": 128
    }
    
    # Log the run
    entry = log_run(
        seed=run_seed,
        parameters=run_params,
        metrics=run_metrics,
        extra={"author": "automated_pipeline"}
    )
    
    print(f"Logged run with ID: {entry['run_id']}")
    print(f"Seed: {entry['seed']}")
    print(f"Metrics: {entry['metrics']}")
    
    # Log an additional metric
    log_metric("final_accuracy", 0.89, run_id=entry['run_id'])
    
    # Verify by reading back
    full_log = get_run_log()
    print(f"Total entries in log: {len(full_log)}")
    print(f"Last entry metrics: {full_log[-1]['metrics']}")
    
    print("Demo completed successfully. Check data/run_log.json")

if __name__ == "__main__":
    main()