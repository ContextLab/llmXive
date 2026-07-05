"""
Demo script to verify T005 logging infrastructure works end-to-end.
This script writes to data/run_log.json as required.
"""
import sys
import os
from pathlib import Path

# Ensure we can import the project modules
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from code.src.utils.logging import log_run, log_metric, get_run_log, clear_run_log

def main():
    print("Testing T005 Logging Infrastructure...")
    
    # Clean start
    clear_run_log()
    
    # Simulate a run
    run_id = "demo_run_001"
    seed = 12345
    params = {
        "network_type": "er",
        "n_nodes": 100,
        "p_edge": 0.05
    }
    metrics = {
        "duration_seconds": 1.5,
        "clustering_coeff": 0.12,
        "avg_degree": 5.0
    }
    
    print(f"Logging run: {run_id}")
    entry = log_run(
        seed=seed,
        parameters=params,
        metrics=metrics,
        run_id=run_id
    )
    
    # Add an extra metric later
    print("Logging additional metric...")
    log_metric("final_accuracy", 0.88, run_id=run_id)
    
    # Verify
    log = get_run_log()
    print(f"Total entries in log: {len(log)}")
    
    if len(log) == 1:
        print("SUCCESS: Log entry created and written to data/run_log.json")
        print(f"Content: {log[0]}")
        return 0
    else:
        print("FAILURE: Expected 1 log entry")
        return 1

if __name__ == "__main__":
    sys.exit(main())