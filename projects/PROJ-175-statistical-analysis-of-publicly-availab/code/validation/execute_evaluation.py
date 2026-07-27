"""
Execution wrapper for T029: Metrics Calculation.
Ensures the evaluation script runs and writes its output to the correct location.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.metrics import main as run_metrics

def run_evaluation_step():
    """
    Executes the metrics calculation script.
    """
    print("Starting Evaluation Step (T029)...")
    start_time = time.time()
    
    try:
        run_metrics()
        
        # Verify output exists
        output_file = PROJECT_ROOT / "data" / "evaluation_metrics.json"
        if not output_file.exists():
            raise FileNotFoundError("Evaluation metrics file was not created.")
        
        end_time = time.time()
        duration = end_time - start_time
        
        log_entry = {
            "task": "T029",
            "status": "SUCCESS",
            "duration_seconds": duration,
            "output_file": str(output_file.relative_to(PROJECT_ROOT))
        }
        
        # Write execution log
        log_path = PROJECT_ROOT / "data" / "evaluation_log.json"
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        print(f"Evaluation step completed successfully in {duration:.2f}s.")
        return 0
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        log_entry = {
            "task": "T029",
            "status": "FAILED",
            "error": str(e),
            "duration_seconds": duration
        }
        
        log_path = PROJECT_ROOT / "data" / "evaluation_log.json"
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        print(f"Evaluation step failed: {e}")
        return 1

def main():
    sys.exit(run_evaluation_step())

if __name__ == "__main__":
    main()
